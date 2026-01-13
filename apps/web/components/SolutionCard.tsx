'use client';

import React from 'react';
import Link from 'next/link';
import {
    Network,
    LayoutGrid,
    RefreshCw,
    Trash2,
    Zap,
    Target,
    BarChart3,
    Calendar,
    Clock
} from 'lucide-react';

interface SolutionCardProps {
    solution: {
        id: string;
        name: string;
        status: string;
        created_at: string;
        updated_at?: string;
    };
    stats: any;
    onDelete: (id: string) => void;
    onReanalyze: (id: string, mode: 'full' | 'update') => void;
    onCancel: (id: string) => void;
    processingId: string | null;
}

import { useRouter } from 'next/navigation';

export const SolutionCard: React.FC<SolutionCardProps> = ({
    solution,
    stats,
    onDelete,
    onReanalyze,
    onCancel,
    processingId
}) => {
    const router = useRouter();
    const [menuOpen, setMenuOpen] = React.useState(false);
    const activeJob = stats?.active_job;
    const isProcessing = solution.status === 'PROCESSING' || solution.status === 'QUEUED';
    const isPlanning = activeJob?.status === 'planning_ready';

    // v5.0 Metrics fallback if not present
    const docCoverage = stats?.metrics?.coverage_score ?? stats?.coverage_score ?? 0;
    const avgConfidence = stats?.metrics?.avg_confidence ?? stats?.avg_confidence ?? 0;

    const handleCardClick = () => {
        router.push(`/solutions/${solution.id}`);
    };

    return (
        <div
            onClick={handleCardClick}
            className="glass-card p-8 relative group cursor-pointer border border-white/5 bg-white/5 backdrop-blur-3xl overflow-hidden"
        >
            {/* Animated Glow Effect */}
            <div className="absolute top-[-20%] right-[-10%] w-48 h-48 bg-primary/20 rounded-full blur-[100px] group-hover:bg-primary/30 transition-all duration-700 pointer-events-none" />

            {/* Header Actions (Stop Propagation to prevent card click) */}
            <div className="absolute top-6 right-6 opacity-0 group-hover:opacity-100 transition-all duration-300 flex gap-2 z-30" onClick={(e) => e.stopPropagation()}>
                <div className="relative">
                    <button
                        onClick={() => setMenuOpen(!menuOpen)}
                        disabled={!!processingId}
                        className="p-2.5 bg-white/5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-2xl transition-all border border-white/10"
                        title="Analysis Options"
                    >
                        <RefreshCw size={18} className={processingId === solution.id ? 'animate-spin' : ''} />
                    </button>

                    {menuOpen && (
                        <div className="absolute right-0 mt-3 w-56 glass rounded-2xl shadow-2xl z-50 overflow-hidden border border-primary/20 animate-in fade-in zoom-in-95 duration-300">
                            <button
                                onClick={() => { onReanalyze(solution.id, 'update'); setMenuOpen(false); }}
                                className="w-full text-left px-5 py-4 text-sm hover:bg-primary/10 transition-colors flex items-center gap-3"
                            >
                                <Zap size={16} className="text-amber-500 fill-amber-500" />
                                <span className="font-bold">Incremental Update</span>
                            </button>
                            <button
                                onClick={() => { onReanalyze(solution.id, 'full'); setMenuOpen(false); }}
                                className="w-full text-left px-5 py-4 text-sm hover:bg-destructive/10 text-destructive-foreground transition-colors border-t border-white/5 flex items-center gap-3"
                            >
                                <Trash2 size={16} />
                                <span className="font-bold">Full Reprocess</span>
                            </button>
                        </div>
                    )}
                </div>

                <button
                    onClick={() => onDelete(solution.id)}
                    disabled={!!processingId}
                    className="p-2.5 bg-white/5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-2xl transition-all border border-white/10"
                >
                    <Trash2 size={18} />
                </button>
            </div>

            <div className="mb-8 relative z-10">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/60 mb-2 block">
                    Discovery Solution
                </span>
                <h2 className="text-2xl font-black tracking-tight text-foreground line-clamp-2 pr-16 leading-tight mb-4 group-hover:text-primary transition-colors">
                    {solution.name}
                </h2>

                <div className="space-y-2.5">
                    <div className="flex items-center gap-2 group/meta">
                        <Calendar size={12} className="text-muted-foreground/40 group-hover/meta:text-primary transition-colors" />
                        <span className="text-[10px] font-bold text-muted-foreground/50 uppercase tracking-widest">
                            Created: <span className="text-foreground/70">{new Date(solution.created_at).toLocaleDateString()}</span>
                        </span>
                    </div>
                    {solution.updated_at && (
                        <div className="flex items-center gap-2 group/meta">
                            <Clock size={12} className="text-muted-foreground/40 group-hover/meta:text-orange-400 transition-colors" />
                            <span className="text-[10px] font-bold text-muted-foreground/50 uppercase tracking-widest">
                                Updated: <span className="text-foreground/70">{new Date(solution.updated_at).toLocaleDateString()}</span>
                            </span>
                        </div>
                    )}
                    {stats?.last_run && (
                        <div className="flex items-center gap-2 group/meta">
                            <RefreshCw size={12} className="text-muted-foreground/40 group-hover/meta:text-amber-500 transition-colors" />
                            <span className="text-[10px] font-bold text-muted-foreground/50 uppercase tracking-widest">
                                Last Run: <span className="text-foreground/70">{new Date(stats.last_run).toLocaleDateString()}</span>
                            </span>
                        </div>
                    )}
                    <div className="flex items-center gap-2 pt-1">
                        <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/5 text-[9px] font-black text-muted-foreground/60 uppercase tracking-tighter">
                            ID: {solution.id.split('-')[0]}
                        </span>
                    </div>
                </div>
            </div>

            {/* Status & Metrics Flow */}
            <div className="relative z-10">
                {isProcessing || isPlanning ? (
                    <div className="mb-2 p-5 rounded-3xl bg-primary/5 border border-primary/10 backdrop-blur-xl">
                        <div className="flex justify-between items-center mb-3">
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
                                <span className="text-sm font-black text-primary uppercase tracking-wider">
                                    {isPlanning ? 'READY TO APPROVE' : 'ANALYZING PROJECT'}
                                </span>
                            </div>
                            <span className="text-sm font-black text-primary">{activeJob?.progress_pct || 0}%</span>
                        </div>
                        <div className="w-full bg-primary/10 rounded-full h-2 overflow-hidden mb-4">
                            <div
                                className="bg-primary h-full rounded-full transition-all duration-1000 ease-in-out shadow-[0_0_15px_rgba(249,115,22,0.5)]"
                                style={{ width: `${activeJob?.progress_pct || 0}%` }}
                            />
                        </div>
                        {isPlanning && (
                            <Link
                                href={`/solutions/${solution.id}/plan`}
                                onClick={(e) => e.stopPropagation()}
                                className="w-full block text-center bg-primary text-white text-xs font-black py-3 rounded-2xl hover:shadow-[0_10px_20px_rgba(249,115,22,0.4)] transition-all uppercase tracking-widest"
                            >
                                REVIEW EXECUTION PLAN
                            </Link>
                        )}
                        {isProcessing && !isPlanning && (
                            <button
                                onClick={(e) => { e.stopPropagation(); onCancel(solution.id); }}
                                className="w-full mt-3 block text-center bg-red-500/10 text-red-500 text-[10px] font-black py-2.5 rounded-xl hover:bg-red-500/20 transition-all uppercase tracking-widest border border-red-500/20"
                            >
                                Stop Analysis
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="grid grid-cols-2 gap-4 mb-8">
                        <div className="bg-white/5 p-5 rounded-3xl border border-white/5 flex flex-col items-center group/metric hover:bg-primary/5 transition-colors">
                            <div className="flex items-center gap-2 text-muted-foreground mb-2">
                                <Target size={14} className="text-orange-500" />
                                <span className="text-[10px] font-black uppercase tracking-widest">Coverage</span>
                            </div>
                            <div className="text-3xl font-black premium-text group-hover/metric:scale-110 transition-transform">
                                {docCoverage}%
                            </div>
                        </div>
                        <div className="bg-white/5 p-5 rounded-3xl border border-white/5 flex flex-col items-center group/metric hover:bg-primary/5 transition-colors">
                            <div className="flex items-center gap-2 text-muted-foreground mb-2">
                                <BarChart3 size={14} className="text-amber-500" />
                                <span className="text-[10px] font-black uppercase tracking-widest">Accuracy</span>
                            </div>
                            <div className="text-3xl font-black premium-text group-hover/metric:scale-110 transition-transform">
                                {(avgConfidence * 100).toFixed(0)}%
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Decorative Link */}
            <div className="flex items-center justify-between text-muted-foreground group">
                <div className="flex items-center gap-4">
                    <div className="flex -space-x-2">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="w-6 h-6 rounded-full border border-zinc-950 bg-zinc-900 flex items-center justify-center">
                                <Network size={10} className="text-primary" />
                            </div>
                        ))}
                    </div>
                    <span className="text-xs font-bold uppercase tracking-wider opacity-60 group-hover:opacity-100 transition-opacity">
                        Explore Lineage
                    </span>
                </div>
                <div className="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center group-hover:bg-primary group-hover:text-white transition-all transform group-hover:rotate-45">
                    <Network size={18} />
                </div>
            </div>
        </div>
    );
};
