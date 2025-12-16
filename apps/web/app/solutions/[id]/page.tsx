'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { supabase } from '@/lib/supabase';
import Link from 'next/link';
import { ArrowLeft, Loader2, RefreshCw, X, FileText, Database, Table, Download, ArrowRightLeft } from 'lucide-react';
import ReactFlow, { 
  Node, 
  Edge, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState,
  MarkerType,
  useReactFlow,
  ReactFlowProvider
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import dagre from 'dagre';
import { ChatAssistant } from '@/components/ChatAssistant';

interface PageProps {
  params: {
    id: string;
  };
}

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
  const [isChatOpen, setIsChatOpen] = useState(false);
  
  // ReactFlow State
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const { fitView } = useReactFlow();

  const fetchGraph = useCallback(async () => {
    setGraphLoading(true);
    try {
      const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/solutions/${id}/graph`;
      console.log("Fetching graph from:", apiUrl);
      
      const response = await axios.get(apiUrl);
      console.log("Graph API Response:", response.data);
      
      const { nodes: rawNodes, edges: rawEdges } = response.data;

      if (!rawNodes || rawNodes.length === 0) {
        console.warn("No nodes found in response");
      }

      // Transform nodes for ReactFlow
      const initialNodes: Node[] = rawNodes.map((n: any) => {
        let bgColor = '#fff';
        let borderColor = '#777';
        let labelColor = '#000';

        // Color coding by TYPE
        switch (n.data.type) {
          case 'PIPELINE':
            bgColor = '#f3e8ff'; // Purple
            borderColor = '#9333ea';
            break;
          case 'SCRIPT':
            bgColor = '#e0f2fe'; // Blue
            borderColor = '#0284c7';
            break;
          case 'TABLE':
            bgColor = '#dcfce7'; // Green
            borderColor = '#16a34a';
            break;
          case 'DATABASE':
            bgColor = '#ffedd5'; // Orange
            borderColor = '#ea580c';
            break;
          default:
            bgColor = '#f3f4f6'; // Gray
            borderColor = '#9ca3af';
        }

        return {
          id: n.id,
          position: { x: 0, y: 0 }, // Initial position, will be fixed by dagre
          data: { ...n.data, fullData: n }, // Pass full data for sidebar
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
        type: 'smoothstep', // Better edge style
        markerEnd: { type: MarkerType.ArrowClosed },
        animated: true,
        style: { stroke: '#64748b', strokeWidth: 1.5 }
      }));

      // Apply Auto-Layout
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        initialNodes,
        initialEdges
      );

      setNodes(layoutedNodes);
      setEdges(layoutedEdges);

      // Fit view after a small delay to ensure rendering
      setTimeout(() => {
        window.requestAnimationFrame(() => fitView());
      }, 100);

    } catch (error) {
      console.error("Error fetching graph:", error);
      alert("Failed to load graph data. Check console for details.");
    } finally {
      setGraphLoading(false);
    }
  }, [id, setNodes, setEdges, fitView]);

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
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="p-4 border-b bg-white dark:bg-zinc-900 flex justify-between items-center z-10 shadow-sm">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="text-gray-500 hover:text-gray-900">
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="font-bold text-lg">{solution.name}</h1>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className={`px-2 py-0.5 rounded-full font-medium 
                ${solution.status === 'READY' ? 'bg-green-100 text-green-800' : 
                  solution.status === 'PROCESSING' ? 'bg-blue-100 text-blue-800' : 
                  'bg-gray-100 text-gray-800'}`}>
                {solution.status}
              </span>
              <span>{new Date(solution.created_at).toLocaleString()}</span>
              <span className="ml-4 text-xs bg-gray-100 px-2 py-1 rounded">
                Nodes: {nodes.length} | Edges: {edges.length}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
            <button 
                onClick={handleExportCSV}
                className="flex items-center gap-2 px-3 py-2 bg-white border hover:bg-gray-50 text-gray-700 rounded-md transition-colors text-sm font-medium"
                title="Export to CSV"
            >
                <Download size={16} /> Export
            </button>
            <div className="h-6 w-px bg-gray-300 mx-1"></div>
            <button 
                onClick={() => setIsChatOpen(!isChatOpen)} 
                className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${isChatOpen ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
                title="Chat with Data"
            >
            <MessageSquare size={18} />
            <span className="text-sm font-medium">Chat</span>
            </button>
            <button 
            onClick={fetchGraph} 
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            title="Refresh Graph"
            >
            <RefreshCw size={20} className={graphLoading ? 'animate-spin' : ''} />
            </button>
        </div>
      </div>

      {/* Graph Area */}
      <div className="flex-1 bg-gray-50 dark:bg-zinc-950 relative flex overflow-hidden">
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
            </ReactFlow>
        </div>

        {/* Side Panel */}
        {selectedNode && (
            <div className="w-96 border-l bg-white dark:bg-zinc-900 overflow-y-auto shadow-xl z-20 absolute right-0 top-0 bottom-0 transition-transform transform translate-x-0">
                <div className="p-6">
                    <div className="flex justify-between items-start mb-6">
                        <div>
                            <span className="text-xs font-bold text-blue-600 uppercase tracking-wider bg-blue-50 px-2 py-1 rounded">
                                {selectedNode.data.type}
                            </span>
                            <h2 className="text-xl font-bold mt-2 break-words">{selectedNode.data.label}</h2>
                        </div>
                        <button 
                            onClick={() => setSelectedNode(null)}
                            className="text-gray-400 hover:text-gray-600 p-1 hover:bg-gray-100 rounded-full"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    <div className="space-y-6">
                        {/* Summary Section */}
                        {selectedNode.data.summary && (
                            <div>
                                <h3 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                                    <FileText size={16} /> AI Summary
                                </h3>
                                <div className="bg-gray-50 dark:bg-zinc-800 p-4 rounded-lg text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                                    {selectedNode.data.summary}
                                </div>
                            </div>
                        )}

                        {/* Metadata Section */}
                        <div>
                            <h3 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                                <Database size={16} /> Metadata
                            </h3>
                            <div className="border rounded-lg overflow-hidden">
                                <table className="w-full text-sm">
                                    <tbody>
                                        <tr className="border-b">
                                            <td className="bg-gray-50 px-3 py-2 text-gray-500 font-medium w-1/3">ID</td>
                                            <td className="px-3 py-2 font-mono text-xs break-all">{selectedNode.id}</td>
                                        </tr>
                                        {selectedNode.data.schema && (
                                            <tr className="border-b">
                                                <td className="bg-gray-50 px-3 py-2 text-gray-500 font-medium">Schema</td>
                                                <td className="px-3 py-2">{selectedNode.data.schema}</td>
                                            </tr>
                                        )}
                                        {/* Display Columns if available */}
                                        {selectedNode.data.columns && selectedNode.data.columns.length > 0 ? (
                                           <tr>
                                               <td className="bg-gray-50 px-3 py-2 text-gray-500 font-medium align-top">Columns</td>
                                               <td className="px-3 py-2">
                                                   <ul className="list-disc list-inside text-xs space-y-1 text-gray-600">
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
                                                    <td className="bg-gray-50 px-3 py-2 text-gray-500 font-medium align-top">Columns</td>
                                                    <td className="px-3 py-2 text-xs text-gray-400 italic">
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
                               <h3 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                                   <ArrowRightLeft size={16} /> Connections
                               </h3>
                               <div className="space-y-4">
                                   {/* Inputs */}
                                   {nodeDependencies.inputs.length > 0 && (
                                       <div>
                                           <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Input From (Upstream)</h4>
                                           <div className="space-y-2">
                                               {nodeDependencies.inputs.map((node: any, idx: number) => (
                                                   <button 
                                                       key={idx} 
                                                       onClick={() => setSelectedNode(node)}
                                                       className="w-full bg-white border rounded p-2 text-sm hover:bg-blue-50 hover:border-blue-300 flex justify-between items-center group cursor-pointer transition-all text-left"
                                                   >
                                                       <div className="flex items-center gap-2">
                                                           <span className="w-2 h-2 rounded-full bg-blue-400 group-hover:scale-125 transition-transform"></span>
                                                           <span className="font-medium text-gray-700 group-hover:text-blue-700">{node.data.label}</span>
                                                       </div>
                                                       <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded group-hover:bg-white">{node.data.type}</span>
                                                   </button>
                                               ))}
                                           </div>
                                       </div>
                                   )}

                                   {/* Outputs */}
                                   {nodeDependencies.outputs.length > 0 && (
                                       <div>
                                           <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Output To (Downstream)</h4>
                                            <div className="space-y-2">
                                               {nodeDependencies.outputs.map((node: any, idx: number) => (
                                                   <button 
                                                       key={idx} 
                                                       onClick={() => setSelectedNode(node)}
                                                       className="w-full bg-white border rounded p-2 text-sm hover:bg-green-50 hover:border-green-300 flex justify-between items-center group cursor-pointer transition-all text-left"
                                                   >
                                                       <div className="flex items-center gap-2">
                                                           <span className="w-2 h-2 rounded-full bg-green-400 group-hover:scale-125 transition-transform"></span>
                                                           <span className="font-medium text-gray-700 group-hover:text-green-700">{node.data.label}</span>
                                                       </div>
                                                       <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded group-hover:bg-white">{node.data.type}</span>
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
      </div>

      <ChatAssistant solutionId={id} isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}

export default function SolutionDetailPage({ params }: PageProps) {
  const { id } = params;
  const [solution, setSolution] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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

  // Wrapped in Provider for useReactFlow hook
  return (
    <ReactFlowProvider>
      <div className="relative h-screen w-full">
        <GraphContent id={id} solution={solution} />
      </div>
    </ReactFlowProvider>
  );
}