'use client';

import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
    Node,
    Edge,
    Background,
    Controls,
    ConnectionLineType,
    MarkerType,
    useNodesState,
    useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import { X, Loader2, GitBranch, Database, Table, Info } from 'lucide-react';

interface ColumnTraceModalProps {
    isOpen: boolean;
    onClose: () => void;
    solutionId: string;
    assetId: string;
    columnName: string;
}

export default function ColumnTraceModal({ isOpen, onClose, solutionId, assetId, columnName }: ColumnTraceModalProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [loading, setLoading] = useState(true);

    const fetchTrace = useCallback(async () => {
        if (!isOpen || !assetId || !columnName) return;

        setLoading(true);
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await axios.get(`${apiUrl}/solutions/${solutionId}/lineage/trace`, {
                params: { asset_id: assetId, column_name: columnName }
            });

            const { nodes: rawNodes, edges: rawEdges } = res.data;

            // Transform to React Flow format with basic Tree Layout
            // We calculate X based on depth, and Y based on index within depth
            const depthGroups: Record<number, number> = {};

            const formattedNodes: Node[] = rawNodes.map((n: any) => {
                const depth = n.depth || 0;
                const indexAtDepth = depthGroups[depth] || 0;
                depthGroups[depth] = indexAtDepth + 1;

                return {
                    id: n.id,
                    position: { x: (depth * -300), y: (indexAtDepth * 100) }, // Negative X to go Left (Upstream)
                    data: {
                        label: (
                            <div className="flex flex-col items-start">
                                <div className="flex items-center gap-1.5 mb-1">
                                    <span className="text-[8px] bg-primary/20 p-0.5 px-1 rounded uppercase font-bold text-primary">
                                        {n.asset_type}
                                    </span>
                                    <span className="text-[10px] font-bold text-muted-foreground truncate max-w-[120px]">
                                        {n.asset_name && n.asset_name !== 'Unknown'
                                            ? n.asset_name
                                            : (n.column_name ? n.column_name.replace(/[\[\]"]/g, '').split('.').slice(0, -1).join('.') : 'External')}
                                    </span>
                                </div>
                                <div className="text-sm font-mono font-bold text-foreground">
                                    {n.column_name}
                                </div>
                            </div>
                        )
                    },
                    className: `glass-card border-none shadow-xl ${depth === 0 ? 'ring-2 ring-primary ring-offset-2 ring-offset-background' : ''}`,
                    style: { width: 180, borderRadius: '12px', padding: '12px' }
                };
            });

            const formattedEdges: Edge[] = rawEdges.map((e: any) => ({
                id: e.id,
                source: e.source,
                target: e.target,
                type: ConnectionLineType.SmoothStep,
                markerEnd: { type: MarkerType.ArrowClosed },
                animated: true,
                label: e.transformation_rule || 'Maps to',
                labelStyle: { fontSize: 8, fill: '#94a3b8', fontStyle: 'italic' },
                labelBgPadding: [2, 4],
                labelBgBorderRadius: 4,
                style: { stroke: '#6366f1', strokeWidth: 1.5 }
            }));

            setNodes(formattedNodes);
            setEdges(formattedEdges);
        } catch (err) {
            console.error("Failed to fetch column trace", err);
        } finally {
            setLoading(false);
        }
    }, [isOpen, solutionId, assetId, columnName, setNodes, setEdges]);

    useEffect(() => {
        fetchTrace();
    }, [fetchTrace]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-300">
            <div className="bg-background border border-border w-full max-w-6xl h-[80vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden glass-card">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-border bg-muted/30">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                            <GitBranch size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold">Column Lineage Trace</h2>
                            <p className="text-sm text-muted-foreground">
                                Tracing upstream origins for <span className="text-foreground font-mono font-bold">{columnName}</span>
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-muted rounded-full transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 relative bg-slate-950/20">
                    {loading ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
                            <Loader2 className="animate-spin text-primary" size={40} />
                            <p className="text-muted-foreground animate-pulse">Scanning knowledge base...</p>
                        </div>
                    ) : (
                        <ReactFlow
                            nodes={nodes}
                            edges={edges}
                            onNodesChange={onNodesChange}
                            onEdgesChange={onEdgesChange}
                            fitView
                            fitViewOptions={{ padding: 0.5 }}
                        >
                            <Background color="#334155" gap={20} />
                            <Controls />

                            {/* Overlay Info */}
                            <div className="absolute bottom-4 left-4 bg-background/80 backdrop-blur border border-border p-3 rounded-lg text-[10px] text-muted-foreground flex items-center gap-2">
                                <Info size={14} className="text-primary" />
                                <span>Showing up to 5 levels of upstream dependencies. Nodes on the left are sources.</span>
                            </div>
                        </ReactFlow>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-border bg-muted/30 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-foreground text-background font-bold rounded-lg hover:opacity-90 transition-all"
                    >
                        Close Insight
                    </button>
                </div>
            </div>
        </div>
    );
}
