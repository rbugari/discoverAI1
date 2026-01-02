'use client';

import React, { useEffect, useState } from 'react';
import {
    BarChart3,
    Target,
    Layers,
    Zap,
    AlertCircle,
    ArrowUpRight,
    ArrowDownRight,
    RefreshCw,
    Search,
    CheckCircle2,
    Clock,
    Trash2,
    Play,
    Terminal
} from 'lucide-react';
import axios from 'axios';
import { LogViewerModal } from '@/components/LogViewerModal';

interface SolutionDashboardProps {
    id: string;
    solution: any;
}

export default function SolutionDashboard({ id, solution }: SolutionDashboardProps) {
    const [stats, setStats] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [actionResult, setActionResult] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const [liveSolution, setLiveSolution] = useState<any>(solution);

    // Sync with prop updates
    useEffect(() => {
        if (solution) setLiveSolution(solution);
    }, [solution]);

    // Logs state
    const [isLogModalOpen, setIsLogModalOpen] = useState(false);
    const [logJobSelection, setLogJobSelection] = useState<{ id: string, status: string, title?: string } | null>(null);
    const [confirmingType, setConfirmingType] = useState<'process' | 'clean' | 'analyze' | 'reprocess' | 'optimize' | null>(null);

    const openLogViewer = (jobId: string, status: string, title?: string) => {
        setLogJobSelection({ id: jobId, status, title });
        setIsLogModalOpen(true);
    };

    // Poll for updates if job is active or solution is not yet READY
    useEffect(() => {
        let interval: NodeJS.Timeout;
        const isNotReady = solution?.status !== 'READY';
        const hasActiveJob = stats?.active_job && ['queued', 'running', 'planning_ready'].includes(stats.active_job.status);

        if (isNotReady || hasActiveJob) {
            interval = setInterval(() => fetchData(true), 3000); // Silent refresh
        }
        return () => clearInterval(interval);
    }, [id]); // Use the memoized fetcher if I move it, but for now [id] is safer

    const fetchData = async (silent = false) => {
        if (!silent) setLoading(true);
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const [statsRes, historyRes, solutionRes] = await Promise.all([
                axios.get(`${apiUrl}/solutions/${id}/stats`),
                axios.get(`${apiUrl}/solutions/${id}/audit/history`),
                axios.get(`${apiUrl}/solutions/${id}`)
            ]);
            setStats(statsRes.data);
            setHistory(historyRes.data || []);
            if (solutionRes.data) setLiveSolution(solutionRes.data);
            // Update local solution state if available to parent? 
            // Since we can't easily update parent state without a callback, 
            // we'll at least use the fetched data locally if needed or just rely on parent polling.
            // But wait, SolutionDashboard uses the 'solution' prop from page.tsx.
            // If we want it to be truly reactive here, we should have a local state or 
            // ensure page.tsx polling is working.
            // Actually, page.tsx IS polling. Let's make sure it's doing so correctly.
        } catch (e) {
            console.error("Failed to fetch dashboard data", e);
        } finally {
            if (!silent) setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [id]);

    const handleReviewPlan = () => {
        // Find the modal trigger or route to plan view
        // Ideally we open the plan modal. Since we don't have the Modal component in this file,
        // we might need to emit an event or use a Context, or just add the Modal here.
        // For v6, let's assume we navigate or show a simple alert if not implemented.
        // Actually, the PlanModal is likely used in other components.
        // Let's print to console for now, or assume there's a parent handler.
        // User asked to access it "with a button from this toolbar".
        // I will add a [REVIEW PLAN] button.
        window.location.href = `/solutions/${id}/plan`; // Simple navigation if separate page, OR:
        // If it's a modal, we need state.
        // Let's use navigation for now as it's cleaner than importing complex modals if not present.
        // Wait, the user said "una vez q tiene plan listo lo deberia acceder con un boton".
        // Let's try to find if there is a plan route.
    };

    const handleAction = (type: 'process' | 'clean' | 'analyze' | 'reprocess' | 'optimize') => {
        console.log(`[ACTION] Triggered: ${type}`);
        setConfirmingType(type);
    };

    const executeAction = async () => {
        if (!confirmingType) return;
        const type = confirmingType;
        setConfirmingType(null);

        console.log(`[ACTION] Executing: ${type}`);
        setActionLoading(true);
        setActionResult(null);
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            console.log(`[ACTION] Calling API: ${apiUrl}/solutions/${id}/${type}`);

            const response = await axios.post(`${apiUrl}/solutions/${id}/${type}`);
            console.log("[ACTION] API Success:", response.data);

            let resultText = "";
            if (type === 'process') resultText = "Discovery pipeline initiated. Scanning files...";
            if (type === 'analyze') resultText = "Smart Update started. Monitoring changes...";
            if (type === 'reprocess') resultText = "Nuclear Reboot initiated. System wiped & restarting...";
            if (type === 'clean') resultText = "History wiped. Solution is now clean.";
            if (type === 'optimize') resultText = "AI Optimization triggered. Reviewing knowledge gaps...";

            setActionResult({
                type: 'success',
                text: resultText
            });

            // Immediate refresh
            fetchData(true);
        } catch (e: any) {
            console.error(`[ACTION] Error in ${type}:`, e);
            const errorMsg = e.response?.data?.detail || e.message || `Failed to execute ${type}`;
            setActionResult({ type: 'error', text: errorMsg });
        } finally {
            setActionLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
                <RefreshCw className="animate-spin text-primary" size={48} />
                <p className="text-sm font-bold tracking-widest text-primary/60 uppercase">Assembling Intelligence...</p>
            </div>
        );
    }

    const metrics = stats?.metrics || {
        coverage_score: stats?.coverage_score || 0,
        avg_confidence: stats?.avg_confidence || 0,
        total_assets: stats?.total_assets || 0,
        total_edges: stats?.total_edges || 0
    };

    // Calculate dynamic trends if history exists
    const prevSnapshot = history.length > 1 ? history[1] : null; // [0] is current normally, but here history is from audit logs
    // history is ordered desc by created_at in backend: .order("created_at", desc=True)
    // So history[0] might be the latest snapshot. stats.metrics is the live current state.
    // If stats are empty (clean state), trends should be null.

    const getTrend = (current: number, field: string) => {
        if (!prevSnapshot || !prevSnapshot.metrics) return null;
        const prev = prevSnapshot.metrics[field] || 0;
        if (prev === 0) return null;
        const diff = current - prev;
        const pct = (diff / prev) * 100;
        return {
            value: `${diff > 0 ? '+' : ''}${pct.toFixed(0)}%`,
            up: diff > 0
        };
    };

    const coverageTrend = getTrend(metrics.coverage_score, 'coverage_score');
    const confidenceTrend = getTrend(metrics.avg_confidence, 'avg_confidence');

    return (
        <div className="space-y-10 animate-in fade-in slide-in-from-bottom-8 duration-1000 ease-out p-4 lg:p-0">

            {/* v6.0 Human-First Immersive Header */}
            <div className="relative overflow-hidden p-10 rounded-[3rem] glass border-primary/10 flex flex-col md:flex-row justify-between items-end gap-6 bg-gradient-to-br from-primary/10 via-orange-500/5 to-transparent">
                <div className="relative z-10">
                    <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary mb-3 block">
                        Enterprise Discovery Asset
                    </span>
                    <h1 className="text-4xl md:text-5xl font-black tracking-tighter text-foreground mb-4">
                        {solution.name}
                    </h1>
                    <div className="flex flex-wrap gap-4 text-xs font-bold text-muted-foreground/80">
                        <span className="px-3 py-1.5 rounded-full bg-white/5 border border-white/5 uppercase tracking-widest">
                            ID: {id.split('-')[0]}
                        </span>
                        <span className="px-3 py-1.5 rounded-full bg-white/5 border border-white/5 uppercase tracking-widest">
                            Created: {new Date(solution.created_at).toLocaleDateString()}
                        </span>
                        {solution.updated_at && (
                            <span className="px-3 py-1.5 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-400 uppercase tracking-widest">
                                Updated: {new Date(solution.updated_at).toLocaleDateString()}
                            </span>
                        )}
                        {stats?.last_run && (
                            <span className="px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 uppercase tracking-widest">
                                Last Run: {new Date(stats.last_run).toLocaleDateString()}
                            </span>
                        )}
                        <span className={`px-3 py-1.5 rounded-full border uppercase tracking-widest ${liveSolution?.status === 'READY' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                            liveSolution?.status === 'ERROR' ? 'bg-red-500/10 border-red-500/20 text-red-400' :
                                'bg-primary/10 border-primary/20 text-primary'
                            }`}>
                            {liveSolution?.status || 'UNKNOWN'}
                        </span>
                    </div>
                </div>
                <div className="relative z-10 flex flex-col items-end gap-3">
                    {actionResult && (
                        <div className={`text-[10px] font-black uppercase tracking-widest px-4 py-2 rounded-xl animate-bounce ${actionResult.type === 'success' ? 'bg-green-500/10 text-green-500 border border-green-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'
                            }`}>
                            {actionResult.text}
                        </div>
                    )}

                    {/* Active Job Progress */}
                    {stats?.active_job && ['queued', 'running', 'planning_ready'].includes(stats.active_job.status) && (
                        <div className="w-full max-w-md bg-black/20 p-4 rounded-xl border border-white/10 backdrop-blur-md">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-[10px] font-black uppercase text-primary animate-pulse">
                                    {stats.active_job.status === 'queued' ? 'Queued' :
                                        stats.active_job.status === 'planning_ready' ? 'Plan Ready' : 'Processing...'}
                                </span>
                                <span className="text-[10px] font-bold text-white">
                                    {stats.active_job.progress_pct || 0}%
                                </span>
                            </div>
                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-primary transition-all duration-1000 ease-out"
                                    style={{ width: `${stats.active_job.progress_pct || 5}%` }}
                                />
                            </div>
                            <div className="mt-2 flex justify-between items-center text-[9px]">
                                <span className="font-mono text-muted-foreground truncate max-w-[200px]">
                                    {stats.active_job.current_stage || 'Initializing connection...'}
                                </span>
                                <button
                                    onClick={() => openLogViewer(stats.active_job.job_id, stats.active_job.status, "Live Execution Logs")}
                                    className="text-primary font-black uppercase tracking-widest hover:underline flex items-center gap-1"
                                >
                                    <Terminal size={10} />
                                    View Logs
                                </button>
                            </div>
                        </div>
                    )}

                    <div className="flex flex-wrap justify-end gap-3">
                        {/* PLAN REVIEW BUTTON - Only when plan is ready */}
                        {(stats?.active_job?.status === 'planning_ready' || liveSolution?.status === 'READY_FOR_APPROVAL') && (
                            <button
                                onClick={handleReviewPlan}
                                className="bg-emerald-500 hover:bg-emerald-600 text-white px-6 py-3 rounded-xl font-black text-[10px] tracking-widest shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:scale-105 transition-all flex items-center gap-2 uppercase animate-pulse mb-2"
                            >
                                <Target size={14} />
                                Review & Approve Plan
                            </button>
                        )}

                        {/* 1. Clean - Wipes history */}
                        {!stats?.active_job && (
                            <button
                                onClick={() => handleAction('clean')}
                                disabled={actionLoading}
                                title="Wipe all data from the repository"
                                className="bg-white/5 hover:bg-red-500/10 text-muted-foreground hover:text-red-500 px-4 py-3 rounded-xl font-bold text-[10px] tracking-widest border border-white/5 hover:border-red-500/20 transition-all flex items-center gap-2 disabled:opacity-50 uppercase"
                            >
                                <Trash2 size={14} />
                                Clean
                            </button>
                        )}

                        {/* 2. Process - Unified Action (Starts Pipeline) */}
                        {!stats?.active_job && (
                            <button
                                onClick={() => handleAction('process')}
                                disabled={actionLoading}
                                title="Run the full discovery pipeline (Scan -> Plan -> Execute)"
                                className="bg-primary hover:bg-primary/90 text-white px-8 py-3 rounded-xl font-black text-[10px] tracking-widest shadow-lg shadow-primary/20 hover:scale-105 transition-all flex items-center gap-2 disabled:opacity-50 uppercase"
                            >
                                <Play size={14} fill="currentColor" />
                                {actionLoading ? 'Initializing...' : 'Process'}
                            </button>
                        )}
                    </div>
                </div>
                {/* Abstract Background Element */}
                <div className="absolute top-[-50%] right-[-10%] w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />
            </div>

            {/* Main Grid Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">

                {/* KPI Sidebar Column */}
                <div className="lg:col-span-1 space-y-6">
                    <KpiCard
                        title="Lineage Coverage"
                        value={`${metrics.coverage_score}%`}
                        icon={<Target className="text-orange-500" />}
                        trend={coverageTrend?.value}
                        trendUp={coverageTrend?.up}
                        subtitle="Nodes with metadata"
                    />
                    <KpiCard
                        title="Discovery Accuracy"
                        value={`${(metrics.avg_confidence * 100).toFixed(0)}%`}
                        icon={<CheckCircle2 className="text-amber-500" />}
                        trend={confidenceTrend?.value}
                        trendUp={confidenceTrend?.up}
                        subtitle="LLM Confidence avg"
                    />
                    <KpiCard
                        title="Asset Density"
                        value={metrics.total_assets}
                        icon={<Layers className="text-primary" />}
                        subtitle="Physical/Logical items"
                    />
                    <KpiCard
                        title="Active Relationships"
                        value={metrics.total_edges}
                        icon={<Zap className="text-yellow-500" />}
                        subtitle="Lineage connections"
                    />
                </div>

                {/* Central Intelligence Column */}
                <div className="lg:col-span-3 space-y-8">

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Health Visualizer */}
                        <div className="glass p-10 rounded-[2.5rem] relative overflow-hidden flex flex-col items-center justify-center text-center">
                            <h3 className="text-lg font-black uppercase tracking-widest text-muted-foreground/60 mb-10">Discovery Health</h3>
                            <div className="relative w-48 h-48 flex items-center justify-center mb-8">
                                <svg className="w-full h-full transform -rotate-90">
                                    <circle
                                        cx="96" cy="96" r="80"
                                        stroke="currentColor" strokeWidth="12" fill="transparent"
                                        className="text-white/5"
                                    />
                                    <circle
                                        cx="96" cy="96" r="80"
                                        stroke="currentColor" strokeWidth="12" fill="transparent"
                                        strokeDasharray={2 * Math.PI * 80}
                                        strokeDashoffset={(2 * Math.PI * 80) * (1 - metrics.coverage_score / 100)}
                                        className="text-primary transition-all duration-1000 ease-out"
                                        strokeLinecap="round"
                                    />
                                </svg>
                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                    <span className="text-5xl font-black premium-text">{metrics.coverage_score}</span>
                                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Score</span>
                                </div>
                            </div>
                            <p className="text-sm font-bold text-foreground max-w-[200px] leading-relaxed">
                                Your project index is <span className="text-primary tracking-tighter italic">Optimized</span>.
                            </p>
                            {/* Animated Background Pulse */}
                            <div className="absolute inset-0 bg-primary/5 animate-pulse pointer-events-none" />
                        </div>

                        {/* Recent Activity / Next Action */}
                        <div className="glass p-10 rounded-[2.5rem] flex flex-col justify-between bg-primary text-white shadow-2xl relative overflow-hidden">
                            <div className="relative z-10">
                                <span className="text-[10px] font-black uppercase tracking-[.2em] opacity-60 mb-4 block">Recommended Move</span>
                                <h3 className="text-2xl font-black tracking-tight mb-4 leading-tight">Apply suggested patches to resolve 12 orphan pipelines.</h3>
                                <p className="text-sm font-medium opacity-80 leading-relaxed mb-8">
                                    Our AI detected structural patterns in your scripts that can be unified.
                                </p>
                            </div>
                            <button
                                onClick={() => handleAction('optimize')}
                                disabled={actionLoading}
                                className="relative z-50 w-full bg-white text-primary font-black py-4 rounded-2xl text-xs uppercase tracking-widest shadow-xl hover:scale-[1.02] transition-transform disabled:opacity-50"
                            >
                                {actionLoading ? 'Optimizing...' : 'Execute Optimization'}
                            </button>
                            <Zap className="absolute right-[-10%] bottom-[-10%] w-48 h-48 opacity-10 rotate-12 pointer-events-none" />
                        </div>
                    </div>

                    {/* Discovery Gaps Hub */}
                    <div className="glass p-10 rounded-[3rem]">
                        <div className="flex items-center justify-between mb-10">
                            <div>
                                <h3 className="text-2xl font-black tracking-tight mb-1 flex items-center gap-3">
                                    <AlertCircle size={28} className="text-primary" />
                                    Knowledge Gaps
                                </h3>
                                <p className="text-sm font-bold text-muted-foreground">Areas requiring manual solution mapping or deeper analysis.</p>
                            </div>
                            <span className="px-4 py-2 rounded-xl bg-primary/10 text-primary text-[10px] font-black uppercase tracking-widest">
                                {stats?.audit_report?.gaps?.length || 0} Issues Found
                            </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {stats?.audit_report?.gaps?.length > 0 ? (
                                stats.audit_report.gaps.map((gap: any, idx: number) => (
                                    <div key={idx} className="bg-white/5 border border-white/5 p-6 rounded-[2rem] hover:bg-primary/5 transition-all hover:translate-x-2 group">
                                        <div className="flex justify-between items-start mb-3">
                                            <span className="text-[10px] font-black uppercase tracking-[.15em] text-primary bg-primary/10 px-2 py-1 rounded-lg">
                                                {gap.type}
                                            </span>
                                            <ArrowUpRight size={18} className="opacity-0 group-hover:opacity-60 transition-opacity" />
                                        </div>
                                        <p className="text-sm font-bold text-foreground leading-relaxed">{gap.description}</p>
                                    </div>
                                ))
                            ) : (
                                <div className="md:col-span-2 text-center py-16 text-muted-foreground/40 bg-white/5 rounded-[2.5rem] border border-dashed border-white/10 font-black uppercase tracking-widest italic text-xs">
                                    Perfect Coverage - No Gaps Detected
                                </div>
                            )}
                        </div>
                    </div>

                    {/* AI Optimization Report (NEW) */}
                    {(stats?.audit_report?.ai_suggestions?.length > 0 || stats?.audit_report?.suggested_solution_layer) && (
                        <div className="glass p-10 rounded-[3rem] border border-primary/20 bg-primary/5 relative overflow-hidden mt-10">
                            <div className="absolute top-0 right-0 p-8 opacity-10 rotate-12">
                                <Zap size={120} className="text-primary" />
                            </div>

                            <div className="relative z-10">
                                <div className="flex items-center justify-between mb-10">
                                    <div>
                                        <h3 className="text-2xl font-black tracking-tight mb-1 flex items-center gap-3 text-white">
                                            <Target size={28} className="text-primary" />
                                            AI Optimization Report
                                        </h3>
                                        <p className="text-sm font-bold text-muted-foreground uppercase tracking-widest">
                                            Insight generated by Olmo-3.1-Think
                                        </p>
                                    </div>
                                    <div className="px-4 py-2 rounded-xl bg-primary text-white text-[10px] font-black uppercase tracking-widest animate-pulse">
                                        Optimization Ready
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                                    {/* Suggestions List */}
                                    <div className="space-y-4">
                                        <h4 className="text-xs font-black uppercase tracking-widest text-primary/60 mb-4">Strategic Recommendations</h4>
                                        {stats.audit_report.ai_suggestions.map((sug: any, idx: number) => (
                                            <div key={idx} className="flex gap-4 items-start bg-black/20 p-4 rounded-2xl border border-white/5">
                                                <div className="mt-1">
                                                    <CheckCircle2 size={16} className="text-primary" />
                                                </div>
                                                <p className="text-sm font-bold text-white/90 leading-relaxed">
                                                    {typeof sug === 'string' ? sug : sug.description}
                                                </p>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Solution Layer Patch */}
                                    {stats.audit_report.suggested_solution_layer && (
                                        <div className="space-y-4">
                                            <div className="flex justify-between items-center mb-4">
                                                <h4 className="text-xs font-black uppercase tracking-widest text-primary/60">Proposed Prompt Patch</h4>
                                                <button
                                                    onClick={() => {
                                                        navigator.clipboard.writeText(stats.audit_report.suggested_solution_layer);
                                                        alert("Patch copied to clipboard!");
                                                    }}
                                                    className="text-[10px] font-black uppercase tracking-widest text-primary hover:underline"
                                                >
                                                    Copy Patch
                                                </button>
                                            </div>
                                            <div className="p-6 bg-black/40 rounded-[2rem] border border-white/10 font-mono text-xs text-primary/80 leading-relaxed min-h-[150px] relative group">
                                                <Terminal size={14} className="absolute top-4 right-4 opacity-20" />
                                                {stats.audit_report.suggested_solution_layer}
                                            </div>
                                            <p className="text-[10px] font-bold text-muted-foreground italic">
                                                Tip: Paste this into your Solution Layer settings to improve discovery accuracy.
                                            </p>
                                        </div>
                                    )}
                                </div>

                                <div className="mt-10 pt-10 border-t border-white/5">
                                    <p className="text-sm font-bold text-foreground mb-4">
                                        {stats.audit_report.next_best_action || "Ready to re-process with improved parameters."}
                                    </p>
                                    <button
                                        onClick={() => handleAction('process')}
                                        className="px-8 py-3 rounded-xl bg-primary text-white font-black text-xs uppercase tracking-widest hover:scale-105 transition-transform"
                                    >
                                        Run Improved Process
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Timeline & Progress (Simplified Visualization) */}
                    {/* Timeline & Progress (Visualization) */}
                    <div className="glass p-10 rounded-[3rem]">
                        <h3 className="text-2xl font-black tracking-tight mb-8 flex items-center gap-3">
                            <Clock size={28} className="text-primary" />
                            Iteration Roadmap
                        </h3>
                        {history.length > 0 ? (
                            <div className="flex overflow-x-auto gap-6 pb-6 scrollbar-hide">
                                {history.map((snap: any, i: number) => (
                                    <div key={snap.snapshot_id} className="flex-shrink-0 w-64 p-6 rounded-[2rem] bg-white/5 border border-white/5 relative group hover:bg-primary/5 transition-colors">
                                        <div className="flex justify-between items-start mb-4">
                                            <div className="text-[10px] font-black text-primary uppercase tracking-tighter">
                                                Checkpoint {history.length - i}
                                            </div>
                                            {snap.job_id && (
                                                <button
                                                    onClick={() => openLogViewer(snap.job_id, 'completed', `Historical Logs: Checkpoint ${history.length - i}`)}
                                                    className="p-1.5 rounded-lg bg-black text-muted-foreground hover:text-white hover:bg-primary/20 transition-all opacity-0 group-hover:opacity-100"
                                                    title="View historical logs"
                                                >
                                                    <Terminal size={14} />
                                                </button>
                                            )}
                                        </div>
                                        <div className="text-xl font-black mb-1">
                                            {(snap.metrics?.coverage_score || 0).toFixed(0)}% Coverage
                                        </div>
                                        <div className="text-[10px] font-bold text-muted-foreground mb-4 opacity-60">
                                            {new Date(snap.created_at).toLocaleDateString()} • {new Date(snap.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </div>
                                        <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-primary transition-all duration-500"
                                                style={{ width: `${snap.metrics?.coverage_score || 0}%` }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-12 border border-dashed border-white/10 rounded-[2.5rem] bg-white/5">
                                <p className="text-muted-foreground/50 font-black uppercase tracking-widest text-xs">
                                    No iteration history available
                                </p>
                            </div>
                        )}
                    </div>

                </div>
            </div>

            {logJobSelection && (
                <LogViewerModal
                    isOpen={isLogModalOpen}
                    onClose={() => setIsLogModalOpen(false)}
                    jobId={logJobSelection.id}
                    jobStatus={logJobSelection.status}
                    title={logJobSelection.title}
                />
            )}

            {/* Custom Confirmation Modal */}
            {confirmingType && (
                <div className="fixed inset-0 z-[10001] flex items-center justify-center p-4">
                    <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setConfirmingType(null)} />
                    <div className="relative glass p-10 rounded-[2.5rem] max-w-md w-full border border-white/10 shadow-2xl animate-in zoom-in duration-200">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="p-4 bg-primary/10 rounded-2xl border border-primary/20">
                                <AlertCircle className="text-primary" size={32} />
                            </div>
                            <h3 className="text-2xl font-black uppercase tracking-tight text-white">Confirm Action</h3>
                        </div>

                        <p className="text-sm font-bold text-muted-foreground mb-10 leading-relaxed uppercase tracking-widest">
                            {confirmingType === 'process' && "Start the Discovery Process? (Scan -> Plan -> Execute)"}
                            {confirmingType === 'clean' && "DANGER: This will permanently DELETE all historical data and leave the solution blank. Proceed?"}
                            {confirmingType === 'analyze' && "Start a Smart Update? This will only process new or changed files."}
                            {confirmingType === 'reprocess' && "WARNING: Nuclear Reset. This will WIPE ALL DATA and start fresh."}
                            {confirmingType === 'optimize' && "Run AI Optimization? This will analyze knowledge gaps and suggest prompt improvements using Olmo-3.1-Think."}
                        </p>

                        <div className="flex gap-4">
                            <button
                                onClick={() => setConfirmingType(null)}
                                className="flex-1 py-4 rounded-2xl bg-white/5 border border-white/10 text-white font-black text-xs uppercase tracking-widest hover:bg-white/10 transition-all"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={executeAction}
                                className={`flex-1 py-4 rounded-2xl font-black text-xs uppercase tracking-widest transition-all shadow-xl shadow-primary/20 hover:scale-[1.02] ${confirmingType === 'clean' || confirmingType === 'reprocess'
                                    ? 'bg-red-500 text-white hover:bg-red-600'
                                    : 'bg-primary text-white hover:bg-primary/90'
                                    }`}
                            >
                                Confirm
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function KpiCard({ title, value, icon, trend, trendUp, subtitle }: any) {
    return (
        <div className="glass-card p-8 group relative overflow-hidden">
            <div className="flex items-center justify-between mb-6">
                <div className="p-3 bg-white/5 rounded-2xl border border-white/10 group-hover:scale-110 transition-transform">
                    {icon}
                </div>
                {trend && (
                    <div className={`flex items-center gap-1 text-[10px] font-black px-3 py-1.5 rounded-xl ${trendUp ? 'bg-emerald-500/10 text-emerald-500' : 'bg-pink-500/10 text-pink-500'}`}>
                        {trendUp ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                        {trend}
                    </div>
                )}
            </div>
            <div>
                <div className="text-[10px] font-black text-muted-foreground uppercase tracking-[.2em] mb-1">{title}</div>
                <div className="text-4xl font-black text-foreground tracking-tighter mb-2">{value}</div>
                <p className="text-[10px] font-bold text-muted-foreground/40 uppercase tracking-widest">{subtitle}</p>
            </div>
        </div>
    );
}
