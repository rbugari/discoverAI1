import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Settings, Database, Code, FileText, Activity, Workflow, Table as TableIcon, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils'; // Assuming cn utility exists, otherwise standard className

const NodeWrapper = ({ children, className, selected }: { children: React.ReactNode, className?: string, selected?: boolean }) => (
    <div className={cn(
        "relative group rounded-xl border-2 transition-all duration-300 shadow-sm hover:shadow-md min-w-[200px] overflow-hidden bg-card",
        selected ? "ring-2 ring-primary ring-offset-2 border-primary" : "border-border",
        className
    )}>
        {children}
    </div>
);

const NodeHeader = ({ icon: Icon, label, colorClass }: { icon: any, label: string, colorClass: string }) => (
    <div className={cn("px-3 py-2 flex items-center gap-2 border-b border-border/50 bg-gradient-to-r", colorClass)}>
        <div className="p-1.5 rounded-md bg-white/20 text-white backdrop-blur-sm shadow-sm">
            <Icon size={14} strokeWidth={2.5} />
        </div>
        <span className="font-semibold text-xs text-white truncate w-full tracking-wide shadow-sm">{label}</span>
    </div>
);

const NodeBody = ({ children }: { children: React.ReactNode }) => (
    <div className="p-3 text-xs space-y-1">
        {children}
    </div>
);

// --- 1. Deep Transform Node (The Core Logic) ---
export const DeepTransformNode = memo(({ data, selected }: NodeProps) => {
    return (
        <NodeWrapper selected={selected} className="border-purple-200 dark:border-purple-900/50">
            <Handle type="target" position={Position.Left} id="target" className="w-3 h-3 border-2 border-purple-500 bg-background !-left-1.5" />

            <NodeHeader
                icon={Workflow}
                label="TRANSFORMATION"
                colorClass="from-purple-500 to-indigo-500"
            />

            <NodeBody>
                <div className="font-bold text-foreground text-sm mb-1">{data.label}</div>
                <div className="flex items-center gap-2 text-muted-foreground">
                    <Code size={10} />
                    <span className="font-mono text-[10px] opacity-75">{data.original_type || 'Unknown Logic'}</span>
                </div>
                {/* Micro-Interaction for Logic Preview */}
                {data.attributes?.expression_raw && (
                    <div className="mt-2 text-[10px] bg-muted/50 p-1.5 rounded border border-border/50 font-mono text-muted-foreground truncate max-w-[180px]">
                        fn: {data.attributes.expression_raw}
                    </div>
                )}
            </NodeBody>

            <Handle type="source" position={Position.Right} id="source" className="w-3 h-3 border-2 border-purple-500 bg-background !-right-1.5" />
        </NodeWrapper>
    );
});
DeepTransformNode.displayName = "DeepTransformNode";

// --- 2. Deep Table Node (Data Assets) ---
export const DeepTableNode = memo(({ data, selected }: NodeProps) => {
    const normalizedType = data.type?.replace('COMPONENT_', '') || 'TABLE';
    const isSource = normalizedType === 'SOURCE';
    const isSink = normalizedType === 'SINK';

    return (
        <NodeWrapper selected={selected} className="border-emerald-200 dark:border-emerald-900/50">
            <Handle type="target" position={Position.Left} id="target" className="w-3 h-3 border-2 border-emerald-500 bg-background !-left-1.5" />

            <NodeHeader
                icon={isSource ? Database : (isSink ? TableIcon : Activity)}
                label={isSource ? "SOURCE" : (isSink ? "DESTINATION" : "TABLE")}
                colorClass={isSource ? "from-emerald-500 to-teal-500" : (isSink ? "from-cyan-500 to-blue-500" : "from-slate-500 to-slate-600")}
            />

            <NodeBody>
                <div className="font-bold text-foreground text-sm mb-1">{data.label}</div>
                {data.schema && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <span className="text-[10px] bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-400 px-1.5 rounded-full">
                            {data.schema}
                        </span>
                    </div>
                )}
                <div className="text-[10px] text-muted-foreground mt-1 flex items-center gap-1">
                    <Database size={10} />
                    {data.system || 'SQL Server'}
                </div>
            </NodeBody>

            <Handle type="source" position={Position.Right} id="source" className="w-3 h-3 border-2 border-emerald-500 bg-background !-right-1.5" />
        </NodeWrapper>
    );
});
DeepTableNode.displayName = "DeepTableNode";

// --- 3. Package Group Node (Hierarchical Containers) ---
export const PackageGroupNode = memo(({ data, selected }: NodeProps) => {
    return (
        <div className={cn(
            "w-full h-full border-[3px] border-dashed rounded-[2rem] transition-all duration-500 relative overflow-hidden bg-background/50",
            selected ? "border-primary bg-primary/[0.03] shadow-2xl" : "border-primary/20 hover:border-primary/40"
        )}>
            {/* Top-Left Stacked Labels */}
            <div className="absolute top-0 left-0 p-6 flex flex-col gap-2 z-10">
                <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-indigo-600 text-white shadow-lg ring-4 ring-indigo-500/20">
                        <Workflow size={18} strokeWidth={2.5} />
                    </div>
                    <div className="flex flex-col">
                        <span className="font-black text-lg uppercase tracking-tight text-indigo-600 dark:text-indigo-400 drop-shadow-sm leading-none">
                            {data.label || 'Unnamed Package'}
                        </span>
                        <span className="text-[9px] font-bold text-muted-foreground/60 uppercase tracking-[0.2em] mt-1 ml-0.5">
                            SSIS :: PACKAGE
                        </span>
                    </div>
                </div>
            </div>

            {/* Subtle Gradient Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent pointer-events-none" />

            {/* Background Icon Watermark (smaller and more subtle) */}
            <div className="absolute bottom-[-20px] right-[-20px] pointer-events-none opacity-[0.05] rotate-12">
                <Workflow size={240} />
            </div>

            {/* Selection/Focus Indicator */}
            {selected && (
                <div className="absolute top-4 right-6 animate-pulse">
                    <div className="flex items-center gap-2 text-primary font-bold text-[10px] uppercase tracking-widest bg-primary/10 px-3 py-1 rounded-full border border-primary/20 backdrop-blur-sm">
                        <Sparkles size={12} />
                        Active Focus
                    </div>
                </div>
            )}

            {/* Handles for Group-level connections (e.g. Star Topology) */}
            <Handle
                type="target"
                position={Position.Left}
                id="target"
                className="w-4 h-4 border-4 border-indigo-500 bg-background !-left-2 opacity-0 group-hover:opacity-100 transition-opacity"
            />
            <Handle
                type="source"
                position={Position.Right}
                id="source"
                className="w-4 h-4 border-4 border-indigo-500 bg-background !-right-2 opacity-0 group-hover:opacity-100 transition-opacity"
            />
        </div>
    );
});
PackageGroupNode.displayName = "PackageGroupNode";
