'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { ArrowRight, Loader2, Table } from 'lucide-react';

export default function LineageView({ solutionId }: { solutionId: string }) {
    const [lineage, setLineage] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchLineage() {
            setLoading(true);
            // We use the foreign key aliases defined in the DB or default mappings
            // Using .select with relation hints
            const { data, error } = await supabase
                .from('column_lineage')
                .select(`
          lineage_id,
          source_column,
          target_column,
          transformation_rule,
          confidence,
          source:asset!column_lineage_source_asset_id_fkey(name_display),
          target:asset!column_lineage_target_asset_id_fkey(name_display),
          package(name)
        `)
                .eq('project_id', solutionId);

            if (error) {
                console.error("Error fetching lineage", error);
                // Fallback if aliases fail (e.g. if fkey names are different)
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

    if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>;

    return (
        <div className="p-6 h-full overflow-y-auto bg-background">
            <div className="mb-6">
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <Table size={24} /> Column-Level Lineage
                </h1>
                <p className="text-muted-foreground mt-1">
                    Detailed mapping of how data flows between columns across systems.
                </p>
            </div>

            {lineage.length === 0 ? (
                <div className="bg-card border border-dashed border-border p-12 text-center rounded-lg">
                    <p className="text-muted-foreground">No column lineage data detected yet for this solution.</p>
                </div>
            ) : (
                <div className="bg-card border border-border rounded-lg overflow-hidden shadow-sm">
                    <table className="w-full text-left text-sm border-collapse">
                        <thead className="bg-muted/50 border-b border-border">
                            <tr>
                                <th className="p-3 font-bold uppercase text-[10px] text-muted-foreground">Source Asset / Column</th>
                                <th className="p-3 w-10 text-center"></th>
                                <th className="p-3 font-bold uppercase text-[10px] text-muted-foreground">Target Asset / Column</th>
                                <th className="p-3 font-bold uppercase text-[10px] text-muted-foreground">Transformation Rule</th>
                                <th className="p-3 font-bold uppercase text-[10px] text-muted-foreground">Origin</th>
                                <th className="p-3 font-bold uppercase text-[10px] text-muted-foreground">Conf.</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {lineage.map((row) => (
                                <tr key={row.lineage_id} className="hover:bg-accent/30 transition-colors">
                                    <td className="p-3">
                                        <div className="font-semibold text-primary">{row.source?.name_display || 'Unknown Asset'}</div>
                                        <div className="text-xs font-mono">{row.source_column || '*'}</div>
                                    </td>
                                    <td className="p-3 text-center opacity-30">
                                        <ArrowRight size={16} />
                                    </td>
                                    <td className="p-3">
                                        <div className="font-semibold text-green-600 dark:text-green-400">{row.target?.name_display || 'Unknown Asset'}</div>
                                        <div className="text-xs font-mono">{row.target_column || '*'}</div>
                                    </td>
                                    <td className="p-3">
                                        <div className="p-1 px-2 rounded bg-muted border border-border text-[11px] max-w-md">
                                            {row.transformation_rule || 'Direct Mapping'}
                                        </div>
                                    </td>
                                    <td className="p-3">
                                        <span className="text-[10px] bg-background border border-border px-1.5 py-0.5 rounded whitespace-nowrap">
                                            {row.package?.name || 'Manual/Global'}
                                        </span>
                                    </td>
                                    <td className="p-3">
                                        <span className={`text-[10px] font-bold ${row.confidence > 0.8 ? 'text-green-500' : 'text-orange-500'}`}>
                                            {Math.round(row.confidence * 100)}%
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
