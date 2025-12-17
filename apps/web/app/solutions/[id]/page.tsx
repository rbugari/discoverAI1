'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { supabase } from '@/lib/supabase';
import Link from 'next/link';
import { ArrowLeft, Loader2, RefreshCw, X, FileText, Database, Table, Download, ArrowRightLeft, LayoutGrid, Network, Filter, Settings, Map, ArrowDown, ArrowRight, Focus, Minimize2 } from 'lucide-react';
import ReactFlow, { 
  Node, 
  Edge, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState,
  MarkerType,
  useReactFlow,
  ReactFlowProvider,
  MiniMap
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import dagre from 'dagre';
import { ChatAssistant } from '@/components/ChatAssistant';
import CatalogPage from './catalog/page';

interface PageProps {
  params: {
    id: string;
  };
}

// ... (getLayoutedElements function remains the same) ...
const getLayoutedElements = (nodes: Node[], edges: Edge[], direction = 'LR') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const nodeWidth = 220;
  const nodeHeight = 80;

  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = direction === 'LR' ? 'left' : 'top';
    node.sourcePosition = direction === 'LR' ? 'right' : 'bottom';

    // We are shifting the dagre node position (anchor=center center) to the top left
    // so it matches the React Flow node anchor point (top left).
    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    };

    return node;
  });

  return { nodes: layoutedNodes, edges };
};

import { MessageSquare } from 'lucide-react';

function GraphContent({ id, solution }: { id: string, solution: any }) {
  const [graphLoading, setGraphLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [focusNodeId, setFocusNodeId] = useState<string | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [nodeTypesFilter, setNodeTypesFilter] = useState<Record<string, boolean>>({
    'TABLE': true,
    'VIEW': true,
    'PIPELINE': true,
    'PROCESS': true,
    'SCRIPT': true,
    'FILE': true,
    'DATABASE': true,
    'PACKAGE': true
  });
  
  // Raw Graph Data (Store full graph to allow filtering/restoring)
  const [rawGraph, setRawGraph] = useState<{nodes: Node[], edges: Edge[]}>({ nodes: [], edges: [] });

  // ReactFlow State
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const { fitView } = useReactFlow();

  // Layout Controls
  const [layoutDirection, setLayoutDirection] = useState<'LR' | 'TB'>('LR');
  const [showMinimap, setShowMinimap] = useState(true);

  // 1. Fetch Graph Data
  const fetchGraph = useCallback(async () => {
    setGraphLoading(true);
    try {
      const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/solutions/${id}/graph`;
      const response = await axios.get(apiUrl);
      const { nodes: rawNodes, edges: rawEdges } = response.data;

      // Transform nodes for ReactFlow (Initial processing)
      const initialNodes: Node[] = rawNodes.map((n: any) => {
        let bgColor = '#fff';
        let borderColor = '#777';
        let labelColor = '#000';

        // Normalize type to ensure consistency
        const normalizedType = (n.data.type || 'FILE').toUpperCase();
        n.data.type = normalizedType;

        // Color coding by TYPE
        switch (normalizedType) {
          case 'PIPELINE':
          case 'PROCESS':
            bgColor = '#f3e8ff'; // Purple
            borderColor = '#9333ea';
            break;
          case 'SCRIPT':
          case 'FILE':
            bgColor = '#e0f2fe'; // Blue
            borderColor = '#0284c7';
            break;
          case 'TABLE':
          case 'VIEW':
            bgColor = '#dcfce7'; // Green
            borderColor = '#16a34a';
            break;
          case 'DATABASE':
            bgColor = '#ffedd5'; // Orange
            borderColor = '#ea580c';
            break;
          case 'PACKAGE':
            bgColor = '#fee2e2'; // Red/Pink
            borderColor = '#ef4444';
            break;
          default:
            bgColor = '#f3f4f6'; // Gray
            borderColor = '#9ca3af';
        }

        return {
          id: n.id,
          position: { x: 0, y: 0 },
          data: { ...n.data, fullData: n },
          style: { 
            background: bgColor,
            border: `2px solid ${borderColor}`,
            borderRadius: '8px',
            padding: '12px',
            width: 220,
            fontSize: '12px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            color: labelColor,
            fontWeight: '500'
          },
        };
      });

      const initialEdges: Edge[] = rawEdges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        type: 'smoothstep',
        markerEnd: { type: MarkerType.ArrowClosed },
        animated: true,
        style: { stroke: '#64748b', strokeWidth: 1.5 }
      }));

      setRawGraph({ nodes: initialNodes, edges: initialEdges });

    } catch (error) {
      console.error("Error fetching graph:", error);
      alert("Failed to load graph data. Check console for details.");
    } finally {
      setGraphLoading(false);
    }
  }, [id]);

  // 2. Process & Filter Graph (Runs when raw data, filters, focus, or layout changes)
  useEffect(() => {
    if (rawGraph.nodes.length === 0) return;

    let filteredNodes = rawGraph.nodes;
    let filteredEdges = rawGraph.edges;

    // A. Apply Type Filters
    filteredNodes = filteredNodes.filter(n => {
        const type = n.data.type; 
        if (nodeTypesFilter[type] !== undefined) return nodeTypesFilter[type];
        return true; 
    });

    // B. Apply Focus Mode (Lineage Isolation)
    if (focusNodeId) {
        const connectedNodeIds = new Set<string>();
        const visitedEdges = new Set<string>();
        
        // Add center node
        connectedNodeIds.add(focusNodeId);

        // Helper for traversal
        const traverse = (nodeId: string, direction: 'upstream' | 'downstream') => {
            const queue = [nodeId];
            while (queue.length > 0) {
                const currentId = queue.shift()!;
                
                // Find connected edges
                const relevantEdges = rawGraph.edges.filter(e => {
                    if (visitedEdges.has(e.id)) return false;
                    if (direction === 'upstream') return e.target === currentId;
                    if (direction === 'downstream') return e.source === currentId;
                    return false;
                });

                relevantEdges.forEach(e => {
                    visitedEdges.add(e.id);
                    const nextNodeId = direction === 'upstream' ? e.source : e.target;
                    if (!connectedNodeIds.has(nextNodeId)) {
                        connectedNodeIds.add(nextNodeId);
                        queue.push(nextNodeId);
                    }
                });
            }
        };

        // Run traversal both ways
        traverse(focusNodeId, 'upstream');
        traverse(focusNodeId, 'downstream');

        // Filter nodes to only connected ones
        filteredNodes = filteredNodes.filter(n => connectedNodeIds.has(n.id));
    }

    // C. Sync Edges with filtered nodes
    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
    filteredEdges = rawGraph.edges.filter(e => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target));

    // D. Apply Layout
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        filteredNodes,
        filteredEdges,
        layoutDirection
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);

    // Fit View
    setTimeout(() => {
        window.requestAnimationFrame(() => fitView());
    }, 100);

  }, [rawGraph, nodeTypesFilter, focusNodeId, layoutDirection, fitView, setNodes, setEdges]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);


  const onNodeClick = (_: React.MouseEvent, node: Node) => {
    setSelectedNode(node.data.fullData);
  };

  // Calculate Upstream and Downstream nodes for the selected node
  const nodeDependencies = useMemo(() => {
    if (!selectedNode) return { inputs: [], outputs: [] };

    const inputs = edges
      .filter(e => e.target === selectedNode.id)
      .map(e => {
        const sourceNode = nodes.find(n => n.id === e.source);
        return sourceNode ? { ...sourceNode.data.fullData, label: e.label || 'Input' } : null;
      })
      .filter(Boolean);

    const outputs = edges
      .filter(e => e.source === selectedNode.id)
      .map(e => {
        const targetNode = nodes.find(n => n.id === e.target);
        return targetNode ? { ...targetNode.data.fullData, label: e.label || 'Output' } : null;
      })
      .filter(Boolean);

    return { inputs, outputs };
  }, [selectedNode, edges, nodes]);

  const handleExportCSV = () => {
    if (nodes.length === 0) return;

    // CSV Headers
    const headers = ['ID', 'Type', 'Label', 'Schema', 'Summary'];
    
    // CSV Rows
    const rows = nodes.map(n => {
        const d = n.data.fullData.data;
        // Escape quotes and handle newlines
        const summary = (d.summary || '').replace(/"/g, '""'); 
        return [
            `"${n.id}"`,
            `"${d.type}"`,
            `"${d.label}"`,
            `"${d.schema || ''}"`,
            `"${summary}"`
        ].join(',');
    });

    const csvContent = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `solution_${solution.name.replace(/\s+/g, '_')}_export.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex-1 bg-muted/20 relative flex overflow-hidden">
        {/* Filters Panel - Absolute Top Left */}
        <div className="absolute top-4 left-4 z-10 bg-card/95 backdrop-blur p-2 rounded-lg shadow-sm border border-border">
             <div className="text-xs font-semibold text-muted-foreground uppercase mb-2 px-1 flex items-center gap-1">
                 <Filter size={12} /> Filter Nodes
             </div>
             <div className="space-y-1">
                 {Object.keys(nodeTypesFilter).map(type => (
                     <label key={type} className="flex items-center gap-2 px-2 py-1 hover:bg-muted/50 rounded cursor-pointer text-xs transition-colors">
                         <input 
                            type="checkbox" 
                            checked={nodeTypesFilter[type]} 
                            onChange={(e) => setNodeTypesFilter(prev => ({...prev, [type]: e.target.checked}))}
                            className="rounded border-input text-primary focus:ring-primary"
                         />
                         <span className="font-medium text-foreground">{type}</span>
                     </label>
                 ))}
             </div>
        </div>

        {/* View Controls - Top Right */}
        <div className="absolute top-4 right-4 z-10 flex gap-2">
            <div className="bg-card/95 backdrop-blur p-1 rounded-lg shadow-sm border border-border flex items-center gap-1">
                {focusNodeId && (
                   <button 
                      onClick={() => setFocusNodeId(null)}
                      className="p-1.5 rounded bg-destructive/10 text-destructive hover:bg-destructive/20 flex items-center gap-1 mr-2 transition-colors"
                      title="Clear Focus"
                   >
                       <Minimize2 size={16} /> <span className="text-xs font-semibold">Reset View</span>
                   </button>
                )}
                <button 
                   onClick={() => setLayoutDirection('LR')}
                   className={`p-1.5 rounded hover:bg-muted transition-colors ${layoutDirection === 'LR' ? 'bg-primary/10 text-primary' : 'text-muted-foreground'}`}
                   title="Horizontal Layout"
                >
                    <ArrowRight size={16} />
                </button>
                <button 
                   onClick={() => setLayoutDirection('TB')}
                   className={`p-1.5 rounded hover:bg-muted transition-colors ${layoutDirection === 'TB' ? 'bg-primary/10 text-primary' : 'text-muted-foreground'}`}
                   title="Vertical Layout"
                >
                    <ArrowDown size={16} />
                </button>
                <div className="w-px h-4 bg-border mx-1"></div>
                <button 
                   onClick={() => setShowMinimap(!showMinimap)}
                   className={`p-1.5 rounded hover:bg-muted transition-colors ${showMinimap ? 'bg-primary/10 text-primary' : 'text-muted-foreground'}`}
                   title="Toggle Minimap"
                >
                    <Map size={16} />
                </button>
            </div>
        </div>

        <div className="flex-1 h-full">
            <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
            attributionPosition="bottom-right"
            >
            <Controls />
            <Background color="#aaa" gap={16} />
            {showMinimap && (
              <MiniMap 
                style={{ height: 120, width: 160, backgroundColor: 'white', border: '1px solid #e5e7eb' }} 
                zoomable 
                pannable 
                nodeColor={(n) => {
                  switch (n.data.type) {
                    case 'PIPELINE': return '#d8b4fe';
                    case 'TABLE': return '#86efac';
                    case 'FILE': return '#7dd3fc';
                    default: return '#e5e7eb';
                  }
                }}
              />
            )}
            </ReactFlow>
        </div>

        {/* Side Panel */}
        {selectedNode && (
            <div className="w-96 border-l border-border bg-card overflow-y-auto shadow-xl z-20 absolute right-0 top-0 bottom-0 transition-transform transform translate-x-0">
                <div className="p-6">
                    <div className="flex justify-between items-start mb-6">
                        <div>
                            <span className="text-xs font-bold text-primary uppercase tracking-wider bg-primary/10 px-2 py-1 rounded">
                                {selectedNode.data.type}
                            </span>
                            <h2 className="text-xl font-bold mt-2 break-words text-foreground">{selectedNode.data.label}</h2>
                        </div>
                        <button 
                            onClick={() => setSelectedNode(null)}
                            className="text-muted-foreground hover:text-foreground p-1 hover:bg-muted rounded-full transition-colors"
                        >
                            <X size={20} />
                        </button>
                    </div>
                    
                    {/* Action Bar */}
                    <div className="flex gap-2 mb-6">
                        <button 
                            onClick={() => {
                                setFocusNodeId(selectedNode.id);
                                // setSelectedNode(null); // Optional: close panel if preferred
                            }}
                            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-colors border
                                ${focusNodeId === selectedNode.id 
                                    ? 'bg-primary/10 border-primary/20 text-primary' 
                                    : 'bg-card border-border hover:bg-muted text-muted-foreground hover:text-foreground'}`}
                        >
                            <Focus size={16} /> 
                            {focusNodeId === selectedNode.id ? 'Focused' : 'Isolate Lineage'}
                        </button>
                        <button className="flex items-center justify-center gap-2 px-3 py-2 rounded-md border border-border hover:bg-muted text-muted-foreground hover:text-foreground transition-colors" title="Coming soon">
                           <Download size={16} />
                        </button>
                    </div>

                    <div className="space-y-6">
                        {/* Summary Section */}
                        {selectedNode.data.summary && (
                            <div>
                                <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                    <FileText size={16} /> AI Summary
                                </h3>
                                <div className="bg-muted/50 p-4 rounded-lg text-sm text-muted-foreground leading-relaxed">
                                    {selectedNode.data.summary}
                                </div>
                            </div>
                        )}

                        {/* Metadata Section */}
                        <div>
                            <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                <Database size={16} /> Metadata
                            </h3>
                            <div className="border border-border rounded-lg overflow-hidden">
                                <table className="w-full text-sm">
                                    <tbody>
                                        <tr className="border-b border-border">
                                            <td className="bg-muted/30 px-3 py-2 text-muted-foreground font-medium w-1/3">ID</td>
                                            <td className="px-3 py-2 font-mono text-xs break-all text-foreground">{selectedNode.id}</td>
                                        </tr>
                                        {selectedNode.data.schema && (
                                            <tr className="border-b border-border">
                                                <td className="bg-muted/30 px-3 py-2 text-muted-foreground font-medium">Schema</td>
                                                <td className="px-3 py-2 text-foreground">{selectedNode.data.schema}</td>
                                            </tr>
                                        )}
                                        {/* Display Columns if available */}
                                        {selectedNode.data.columns && selectedNode.data.columns.length > 0 ? (
                                           <tr>
                                               <td className="bg-muted/30 px-3 py-2 text-muted-foreground font-medium align-top">Columns</td>
                                               <td className="px-3 py-2">
                                                   <ul className="list-disc list-inside text-xs space-y-1 text-muted-foreground">
                                                       {selectedNode.data.columns.map((col: string, i: number) => (
                                                           <li key={i} className="break-words">{col}</li>
                                                       ))}
                                                   </ul>
                                               </td>
                                           </tr>
                                        ) : (
                                            /* Fallback for tables without detected columns */
                                            (selectedNode.data.type === 'TABLE' || selectedNode.data.type === 'DATABASE') && (
                                                <tr>
                                                    <td className="bg-muted/30 px-3 py-2 text-muted-foreground font-medium align-top">Columns</td>
                                                    <td className="px-3 py-2 text-xs text-muted-foreground italic">
                                                        No columns detected in code analysis.
                                                    </td>
                                                </tr>
                                            )
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Dependencies Section (New) */}
                        {(nodeDependencies.inputs.length > 0 || nodeDependencies.outputs.length > 0) && (
                           <div>
                               <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                   <ArrowRightLeft size={16} /> Connections
                               </h3>
                               <div className="space-y-4">
                                   {/* Inputs */}
                                   {nodeDependencies.inputs.length > 0 && (
                                       <div>
                                           <h4 className="text-xs font-bold text-muted-foreground uppercase mb-2">Input From (Upstream)</h4>
                                           <div className="space-y-2">
                                               {nodeDependencies.inputs.map((node: any, idx: number) => (
                                                   <button 
                                                       key={idx} 
                                                       onClick={() => setSelectedNode(node)}
                                                       className="w-full bg-card border border-border rounded p-2 text-sm hover:bg-accent hover:border-primary/50 flex justify-between items-center group cursor-pointer transition-all text-left"
                                                   >
                                                       <div className="flex items-center gap-2">
                                                           <span className="w-2 h-2 rounded-full bg-blue-400 group-hover:scale-125 transition-transform"></span>
                                                           <span className="font-medium text-foreground group-hover:text-primary">{node.data.label}</span>
                                                       </div>
                                                       <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded group-hover:bg-background">{node.data.type}</span>
                                                   </button>
                                               ))}
                                           </div>
                                       </div>
                                   )}

                                   {/* Outputs */}
                                   {nodeDependencies.outputs.length > 0 && (
                                       <div>
                                           <h4 className="text-xs font-bold text-muted-foreground uppercase mb-2">Output To (Downstream)</h4>
                                            <div className="space-y-2">
                                               {nodeDependencies.outputs.map((node: any, idx: number) => (
                                                   <button 
                                                       key={idx} 
                                                       onClick={() => setSelectedNode(node)}
                                                       className="w-full bg-card border border-border rounded p-2 text-sm hover:bg-accent hover:border-green-500/50 flex justify-between items-center group cursor-pointer transition-all text-left"
                                                   >
                                                       <div className="flex items-center gap-2">
                                                           <span className="w-2 h-2 rounded-full bg-green-400 group-hover:scale-125 transition-transform"></span>
                                                           <span className="font-medium text-foreground group-hover:text-green-600 dark:group-hover:text-green-400">{node.data.label}</span>
                                                       </div>
                                                       <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded group-hover:bg-background">{node.data.type}</span>
                                                   </button>
                                               ))}
                                           </div>
                                       </div>
                                   )}
                               </div>
                           </div>
                        )}
                    </div>
                </div>
            </div>
        )}
        <ChatAssistant solutionId={id} isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}

export default function SolutionDetailPage({ params }: PageProps) {
  const { id } = params;
  const [solution, setSolution] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'graph' | 'catalog'>('graph');

  const fetchSolution = useCallback(async () => {
    const { data, error } = await supabase
      .from('solutions')
      .select('*')
      .eq('id', id)
      .single();

    if (error) {
      console.error('Error fetching solution:', error);
    } else {
      setSolution(data);
    }
    setLoading(false);
  }, [id]);

  useEffect(() => {
    fetchSolution();
  }, [fetchSolution]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader2 className="animate-spin" size={48} />
      </div>
    );
  }

  if (!solution) {
    return <div className="p-8">Solution not found</div>;
  }

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
        {/* Header */}
        <div className="p-4 border-b border-border bg-background/95 backdrop-blur flex justify-between items-center z-10 shadow-sm">
            <div className="flex items-center gap-4">
                <Link href="/dashboard" className="text-muted-foreground hover:text-foreground transition-colors">
                    <ArrowLeft size={20} />
                </Link>
                <div>
                    <h1 className="font-bold text-lg tracking-tight">{solution.name}</h1>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className={`px-2 py-0.5 rounded-full font-medium border
                            ${solution.status === 'READY' ? 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800' : 
                            solution.status === 'PROCESSING' ? 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800' : 
                            'bg-secondary text-secondary-foreground border-border'}`}>
                            {solution.status}
                        </span>
                        <span>{new Date(solution.created_at).toLocaleString()}</span>
                    </div>
                </div>
            </div>
            
            {/* View Switcher */}
            <div className="flex bg-muted p-1 rounded-md">
                <button
                    onClick={() => setViewMode('graph')}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition-all ${viewMode === 'graph' ? 'bg-background text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                >
                    <Network size={16} /> Graph
                </button>
                <button
                    onClick={() => setViewMode('catalog')}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition-all ${viewMode === 'catalog' ? 'bg-background text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                >
                    <LayoutGrid size={16} /> Catalog
                </button>
            </div>
        </div>

        {/* Content */}
        {viewMode === 'graph' ? (
            <ReactFlowProvider>
                <GraphContent id={id} solution={solution} />
            </ReactFlowProvider>
        ) : (
            <div className="flex-1 overflow-hidden bg-background">
                <CatalogPage params={{ id }} />
            </div>
        )}
    </div>
  );
}