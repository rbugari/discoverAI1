'use client';

import { useState, useEffect, useMemo } from 'react';
import { supabase } from '@/lib/supabase';
import { ArrowRight, Loader2, Table, Search, Filter, Database, AlertCircle } from 'lucide-react';

export default function LineageView({ solutionId }: { solutionId: string }) {
    const [lineage, setLineage] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [minConfidence, setMinConfidence] = useState(0);
    const searchParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;

    useEffect(() => {
        const initialSearch = searchParams?.get('search');
        if (initialSearch) setSearchTerm(initialSearch);
    }, []);

    useEffect(() => {
        async function fetchLineage() {
            setLoading(true);
            const { data, error } = await supabase
                .from('column_lineage')
                .select(`
          lineage_id,
          source_column,
          target_column,
          transformation_rule,
          confidence,
          source:asset!column_lineage_source_asset_id_fkey(name_display, asset_type),
          target:asset!column_lineage_target_asset_id_fkey(name_display, asset_type),
          package(name)
        `)
                .eq('project_id', solutionId);

            if (error) {
                console.error("Error fetching lineage", error);
                const { data: fallbackData } = await supabase
                    .from('column_lineage')
                    .select('*')
                    .eq('project_id', solutionId);
                setLineage(fallbackData || []);
            } else {
                setLineage(data || []);
            }
            setLoading(false);
        }
        fetchLineage();
    }, [solutionId]);

    // Helper to parse asset name from column path if asset is missing
    const resolveAssetName = (asset: any, column: string) => {
        if (asset?.name_display && asset.name_display !== 'Unknown') return asset.name_display;
        if (!column) return 'Unknown Asset';

        // Clean column name (remove brackets, quotes)
        const cleanCol = column.replace(/[\[\]"]/g, '');
        const parts = cleanCol.split('.');

        // If it looks like schema.table.column, return schema.table
        if (parts.length >= 3) return parts.slice(0, -1).join('.');
        if (parts.length === 2) return parts[0];
        return 'External Source';
    };

    const filteredLineage = useMemo(() => {
        return lineage.filter(row => {
            const matchesSearch =
                (row.source_column?.toLowerCase().includes(searchTerm.toLowerCase())) ||
                (row.target_column?.toLowerCase().includes(searchTerm.toLowerCase())) ||
                (row.source?.name_display?.toLowerCase().includes(searchTerm.toLowerCase())) ||
                (row.target?.name_display?.toLowerCase().includes(searchTerm.toLowerCase()));

            const matchesConfidence = (row.confidence || 1) >= minConfidence;

            return matchesSearch && matchesConfidence;
        });
    }, [lineage, searchTerm, minConfidence]);

    if (loading) return <div className="p-8 flex justify-center h-full items-center"><Loader2 className="animate-spin text-primary" size={40} /></div>;

    return (
        <div className="flex flex-col h-full bg-slate-950/20 px-6 py-6">
            {/* Header */}
            <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="flex flex-col gap-1">
                    <h1 className="text-3xl font-bold flex items-center gap-3 text-foreground tracking-tight">
                        <Database className="text-primary" size={28} /> Column-Level Lineage
                    </h1>
                    <p className="text-muted-foreground text-sm max-w-xl">
                        Explore how data flows between system columns. Use filters to narrow down large datasets.
                    </p>
                </div>

                {/* Filters UI */}
                <div className="flex flex-wrap gap-3 items-center">
                    <div className="relative group">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                        <input
                            type="text"
                            placeholder="Search by asset or column..."
                            className="pl-10 h-10 w-[250px] lg:w-[350px] rounded-xl border border-border bg-muted/40 backdrop-blur-sm px-4 py-2 text-sm shadow-inner transition-all focus:outline-none focus:ring-2 focus:ring-primary/40 focus:bg-muted/60"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>

                    <div className="relative">
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                        <select
                            className="h-10 pl-10 pr-8 rounded-xl border border-border bg-muted/40 backdrop-blur-sm text-sm shadow-inner transition-all focus:outline-none focus:ring-2 focus:ring-primary/40 focus:bg-muted/60 appearance-none cursor-pointer"
                            value={minConfidence}
                            onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                        >
                            <option value="0">All Confidence</option>
                            <option value="0.7">High Conf. (&gt;70%)</option>
                            <option value="0.9">Verified (&gt;90%)</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Content Table */}
            <div className="flex-1 overflow-hidden flex flex-col">
                {lineage.length === 0 ? (
                    <div className="bg-card/40 backdrop-blur-md border border-dashed border-border/50 p-20 flex flex-col items-center justify-center rounded-[3rem] text-center shadow-2xl">
                        <AlertCircle className="text-muted-foreground/30 mb-4" size={48} />
                        <p className="text-muted-foreground font-medium text-lg">No lineage discovered yet.</p>
                        <p className="text-muted-foreground/60 text-sm">Make sure to run a Deep Dive analysis on your assets.</p>
                    </div>
                ) : (
                    <div className="bg-card/40 backdrop-blur-xl border border-border/50 rounded-[2.5rem] overflow-hidden shadow-2xl flex-1 flex flex-col relative">
                        <div className="overflow-y-auto flex-1 custom-scrollbar">
                            <table className="w-full text-left text-sm border-collapse">
                                <thead className="bg-muted/80 backdrop-blur-xl border-b border-border/50 sticky top-0 z-10 text-[10px] font-black uppercase tracking-widest text-muted-foreground">
                                    <tr>
                                        <th className="p-6 font-bold">Source Asset / Column</th>
                                        <th className="p-6 w-12 text-center"></th>
                                        <th className="p-6 font-bold">Target Asset / Column</th>
                                        <th className="p-6 font-bold">Transformation Rule</th>
                                        <th className="p-6 font-bold">Origin</th>
                                        <th className="p-6 font-bold text-right">Conf.</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border/30">
                                    {filteredLineage.map((row) => (
                                        <tr key={row.lineage_id} className="hover:bg-primary/[0.03] transition-colors group">
                                            <td className="p-4">
                                                <div className="font-bold text-foreground mb-0.5">
                                                    {resolveAssetName(row.source, row.source_column)}
                                                </div>
                                                <div className="text-xs font-mono text-muted-foreground bg-muted/30 px-1.5 py-0.5 rounded-md inline-block">
                                                    {row.source_column || '*'}
                                                </div>
                                            </td>
                                            <td className="p-4 text-center">
                                                <ArrowRight size={14} className="text-muted-foreground/30 group-hover:text-primary transition-colors" />
                                            </td>
                                            <td className="p-4">
                                                <div className="font-bold text-green-500/90 dark:text-green-400/90 mb-0.5">
                                                    {resolveAssetName(row.target, row.target_column)}
                                                </div>
                                                <div className="text-xs font-mono text-muted-foreground bg-muted/30 px-1.5 py-0.5 rounded-md inline-block">
                                                    {row.target_column || '*'}
                                                </div>
                                            </td>
                                            <td className="p-4">
                                                <div className="p-2 px-3 rounded-xl bg-muted/40 border border-border/40 text-[11px] text-foreground/80 leading-relaxed font-medium">
                                                    {row.transformation_rule || 'Direct Mapping'}
                                                </div>
                                            </td>
                                            <td className="p-4">
                                                <span className="text-[10px] font-bold text-primary/70 bg-primary/5 border border-primary/20 px-2 py-1 rounded-full uppercase tracking-tight">
                                                    {row.package?.name || 'Global Context'}
                                                </span>
                                            </td>
                                            <td className="p-4 text-right">
                                                <div className={`text-xs font-black tabular-nums ${row.confidence > 0.8 ? 'text-green-500' : 'text-orange-500'}`}>
                                                    {Math.round(row.confidence * 100)}%
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                    {filteredLineage.length === 0 && (
                                        <tr>
                                            <td colSpan={6} className="p-20 text-center text-muted-foreground italic bg-muted/10">
                                                No results match your search filters.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                        {/* Footer stats */}
                        <div className="p-4 bg-muted/30 border-t border-border flex justify-between items-center">
                            <span className="text-xs text-muted-foreground font-medium">
                                Showing {filteredLineage.length} of {lineage.length} connections
                            </span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
