'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
    Loader2, CheckCircle, AlertCircle, FileText,
    Database, Package, Settings, DollarSign, Clock, Play, ArrowLeft,
    ChevronDown, ChevronRight, ToggleLeft, ToggleRight
} from 'lucide-react';

interface Estimate {
    tokens: number;
    cost_usd: number;
    time_seconds: number;
}

interface PlanItem {
    item_id: string;
    path: string;
    file_type: string;
    size_bytes: number;
    strategy: string;
    recommended_action: string;
    enabled: boolean;
    estimate: Estimate;
    classifier: {
        reason: string;
    };
}

interface PlanArea {
    area_id: string;
    area_key: string;
    title: string;
    items: PlanItem[];
}

interface JobPlan {
    plan_id: string;
    status: string;
    summary: {
        total_files: number;
        total_cost: number;
        total_time: number;
    };
    areas: PlanArea[];
}

export default function PlanReviewPage({ params }: { params: { id: string } }) {
    const [plan, setPlan] = useState<JobPlan | null>(null);
    const [loading, setLoading] = useState(true);
    const [approving, setApproving] = useState(false);
    const [expandedAreas, setExpandedAreas] = useState<Record<string, boolean>>({});
    const router = useRouter();
    const solutionId = params.id;

    useEffect(() => {
        const fetchPlan = async () => {
            try {
                const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/solutions/${solutionId}/active-plan`);

                if (res.data.plan) {
                    setPlan(res.data.plan);

                    // Expand all areas by default
                    const initialExpanded: Record<string, boolean> = {};
                    res.data.plan.areas.forEach((a: any) => initialExpanded[a.area_id] = true);
                    setExpandedAreas(initialExpanded);
                } else {
                    console.warn("No active plan found for this solution.");
                }
            } catch (e) {
                console.error("Error fetching active-plan:", e);
            } finally {
                setLoading(false);
            }
        };
        fetchPlan();
    }, [solutionId]);

    const toggleItem = async (itemId: string, currentEnabled: boolean) => {
        if (!plan) return;

        // Optimistic update
        const newPlan = { ...plan };
        let found = false;
        newPlan.areas.forEach(area => {
            const item = area.items.find(i => i.item_id === itemId);
            if (item) {
                item.enabled = !currentEnabled;
                found = true;
            }
        });

        if (found) setPlan(newPlan);

        try {
            await axios.patch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/plans/${plan.plan_id}/items/${itemId}`, {
                enabled: !currentEnabled
            });
        } catch (e) {
            console.error("Failed to toggle item", e);
        }
    };

    const moveItem = async (itemId: string, newAreaId: string) => {
        if (!plan) return;

        // Optimistic update: Move item from current area to new area
        const newPlan = { ...plan };
        let itemToMove: PlanItem | undefined;
        let sourceAreaIndex = -1;

        // 1. Find and remove item
        newPlan.areas.forEach((area, idx) => {
            const itemIndex = area.items.findIndex(i => i.item_id === itemId);
            if (itemIndex !== -1) {
                itemToMove = area.items[itemIndex];
                area.items.splice(itemIndex, 1);
                sourceAreaIndex = idx;
            }
        });

        // 2. Add to new area
        if (itemToMove) {
            const targetArea = newPlan.areas.find(a => a.area_id === newAreaId);
            if (targetArea) {
                targetArea.items.push(itemToMove);
                setPlan(newPlan);

                try {
                    await axios.patch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/plans/${plan.plan_id}/items/${itemId}`, {
                        area_id: newAreaId
                    });
                } catch (e) {
                    console.error("Failed to move item", e);
                    // Revert logic would be complex, just alert for now or silent fail
                }
            }
        }
    };

    const handleApprove = async () => {
        if (!plan) return;
        setApproving(true);
        try {
            await axios.post(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/plans/${plan.plan_id}/approve`);
            // Redirect to dashboard as requested by user
            router.push(`/solutions/${solutionId}`);
        } catch (e) {
            console.error("Failed to approve plan", e);
            alert("Failed to approve plan. Check console.");
            setApproving(false);
        }
    };

    const toggleArea = (areaId: string) => {
        setExpandedAreas(prev => ({ ...prev, [areaId]: !prev[areaId] }));
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-screen bg-background">
                <Loader2 className="animate-spin text-primary" size={48} />
            </div>
        );
    }

    if (!plan) {
        return (
            <div className="p-8 flex flex-col items-center justify-center h-screen bg-background text-foreground">
                <h1 className="text-xl font-bold mb-2">No Plan Found</h1>
                <p className="text-muted-foreground mb-4">There is no active planning session for this solution.</p>
                <Link href={`/solutions/${solutionId}`} className="text-primary hover:underline">
                    Return to Solution
                </Link>
            </div>
        );
    }

    // Calculate dynamic summary based on enabled items
    const summary = plan.areas.reduce((acc, area) => {
        area.items.forEach(item => {
            if (item.enabled) {
                acc.files++;
                acc.cost += item.estimate.cost_usd || 0;
                acc.time += item.estimate.time_seconds || 0;
            }
        });
        return acc;
    }, { files: 0, cost: 0, time: 0 });

    return (
        <div className="min-h-screen bg-background text-foreground flex flex-col">
            {/* Header */}
            <div className="border-b border-border bg-card p-6 sticky top-0 z-10 shadow-sm">
                <div className="max-w-6xl mx-auto">
                    <div className="flex justify-between items-center mb-6">
                        <div className="flex items-center gap-4">
                            <Link href={`/solutions/${solutionId}`} className="text-muted-foreground hover:text-foreground">
                                <ArrowLeft size={24} />
                            </Link>
                            <div>
                                <h1 className="text-2xl font-bold">Execution Plan Review</h1>
                                <p className="text-sm text-muted-foreground">Review and approve files for processing.</p>
                            </div>
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={handleApprove}
                                disabled={approving}
                                className="bg-primary text-primary-foreground hover:bg-primary/90 px-6 py-2 rounded-md font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
                            >
                                {approving ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
                                Approve & Run
                            </button>
                        </div>
                    </div>

                    {/* Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-muted/30 p-4 rounded-lg border border-border flex items-center gap-4">
                            <div className="bg-blue-100 dark:bg-blue-900/30 p-2 rounded-full text-blue-600 dark:text-blue-400">
                                <FileText size={24} />
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground font-medium">Files to Process</p>
                                <p className="text-2xl font-bold">{summary.files}</p>
                            </div>
                        </div>
                        <div className="bg-muted/30 p-4 rounded-lg border border-border flex items-center gap-4">
                            <div className="bg-green-100 dark:bg-green-900/30 p-2 rounded-full text-green-600 dark:text-green-400">
                                <DollarSign size={24} />
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground font-medium">Est. Cost</p>
                                <p className="text-2xl font-bold">${summary.cost.toFixed(4)}</p>
                            </div>
                        </div>
                        <div className="bg-muted/30 p-4 rounded-lg border border-border flex items-center gap-4">
                            <div className="bg-orange-100 dark:bg-orange-900/30 p-2 rounded-full text-orange-600 dark:text-orange-400">
                                <Clock size={24} />
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground font-medium">Est. Time</p>
                                <p className="text-2xl font-bold">{Math.ceil(summary.time)}s</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 p-6 max-w-6xl mx-auto w-full space-y-6">
                {plan.areas.map(area => (
                    <div key={area.area_id} className="border border-border rounded-lg bg-card overflow-hidden">
                        <div
                            className="p-4 bg-muted/50 flex justify-between items-center cursor-pointer hover:bg-muted/70 transition-colors"
                            onClick={() => toggleArea(area.area_id)}
                        >
                            <div className="flex items-center gap-2">
                                {expandedAreas[area.area_id] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                                <h2 className="font-semibold text-lg">{area.title}</h2>
                                <span className="bg-background border border-border text-xs px-2 py-0.5 rounded-full text-muted-foreground">
                                    {area.items.length} items
                                </span>
                            </div>
                        </div>

                        {expandedAreas[area.area_id] && (
                            <div className="divide-y divide-border">
                                {area.items.length === 0 ? (
                                    <div className="p-8 text-center text-muted-foreground italic">No items in this area.</div>
                                ) : (
                                    area.items.map(item => (
                                        <div key={item.item_id} className={`p-4 flex items-center justify-between hover:bg-muted/20 transition-colors ${!item.enabled ? 'opacity-50 grayscale' : ''}`}>
                                            <div className="flex items-center gap-4 flex-1 min-w-0">
                                                <div className="bg-muted p-2 rounded text-muted-foreground">
                                                    {item.file_type === 'SQL' ? <Database size={18} /> :
                                                        item.file_type === 'DTSX' ? <Package size={18} /> :
                                                            <FileText size={18} />}
                                                </div>
                                                <div className="min-w-0">
                                                    <p className="font-medium truncate" title={item.path}>{item.path}</p>
                                                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                        <span className="border border-border px-1.5 rounded">{item.file_type}</span>
                                                        <span>{(item.size_bytes / 1024).toFixed(1)} KB</span>
                                                        <span className="flex items-center gap-1">
                                                            <span className={`w-1.5 h-1.5 rounded-full ${item.strategy === 'LLM_ONLY' ? 'bg-orange-500' : 'bg-blue-500'}`}></span>
                                                            {item.strategy}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-6">
                                                <div className="text-right text-sm">
                                                    <p className="font-medium">${item.estimate.cost_usd.toFixed(5)}</p>
                                                    <p className="text-xs text-muted-foreground">{item.estimate.tokens} toks</p>
                                                </div>

                                                {/* Move to Area Dropdown */}
                                                <select
                                                    className="text-xs border border-border rounded bg-background p-1 max-w-[100px] truncate"
                                                    value={area.area_id}
                                                    onChange={(e) => moveItem(item.item_id, e.target.value)}
                                                    onClick={(e) => e.stopPropagation()}
                                                >
                                                    {plan.areas.map(a => (
                                                        <option key={a.area_id} value={a.area_id}>
                                                            Move to {a.title.split(' ')[0]}
                                                        </option>
                                                    ))}
                                                </select>

                                                <button
                                                    onClick={() => toggleItem(item.item_id, item.enabled)}
                                                    className={`text-2xl transition-colors ${item.enabled ? 'text-primary' : 'text-muted-foreground'}`}
                                                >
                                                    {item.enabled ? <ToggleRight size={32} /> : <ToggleLeft size={32} />}
                                                </button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
