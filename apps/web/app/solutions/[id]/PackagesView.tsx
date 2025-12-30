'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { Package, Boxes } from 'lucide-react';
import { Loader2 } from 'lucide-react';

export default function PackagesView({ solutionId }: { solutionId: string }) {
  const [packages, setPackages] = useState<any[]>([]);
  const [selectedPackage, setSelectedPackage] = useState<any>(null);
  const [components, setComponents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [compLoading, setCompLoading] = useState(false);

  useEffect(() => {
    async function fetchPackages() {
      setLoading(true);
      const { data, error } = await supabase
        .from('package')
        .select('*')
        .eq('project_id', solutionId);

      if (!error && data) {
        setPackages(data);
      }
      setLoading(false);
    }
    fetchPackages();
  }, [solutionId]);

  useEffect(() => {
    async function fetchComponents() {
      if (!selectedPackage) return;
      setCompLoading(true);
      const { data, error } = await supabase
        .from('package_component')
        .select('*')
        .eq('package_id', selectedPackage.package_id)
        .order('order_index');

      if (!error && data) {
        setComponents(data);
      }
      setCompLoading(false);
    }
    fetchComponents();
  }, [selectedPackage]);

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>;

  return (
    <div className="flex h-full overflow-hidden bg-background">
      {/* Sidebar: Package List */}
      <div className="w-80 border-r border-border overflow-y-auto p-4 space-y-2">
        <h2 className="text-sm font-bold text-muted-foreground uppercase mb-4">Packages</h2>
        {packages.length === 0 && <p className="text-xs text-muted-foreground italic">No packages found.</p>}
        {packages.map((pkg) => (
          <button
            key={pkg.package_id}
            onClick={() => setSelectedPackage(pkg)}
            className={`w-full text-left p-3 rounded-md border transition-all ${selectedPackage?.package_id === pkg.package_id
              ? 'bg-primary/10 border-primary text-primary'
              : 'bg-card border-border hover:bg-accent'
              }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <Package size={16} />
              <span className="font-semibold text-sm truncate">{pkg.name}</span>
            </div>
            <div className="text-[10px] opacity-70 px-1 py-0.5 bg-muted rounded w-fit capitalize">{pkg.type}</div>
            {pkg.business_intent && (
              <p className="text-xs mt-2 line-clamp-2 opacity-80">{pkg.business_intent}</p>
            )}
          </button>
        ))}
      </div>

      {/* Main Content: Components & Logic */}
      <div className="flex-1 overflow-y-auto p-6">
        {selectedPackage ? (
          <div>
            <div className="mb-6 border-b border-border pb-4">
              <h1 className="text-2xl font-bold mb-2">{selectedPackage.name}</h1>
              <p className="text-muted-foreground">{selectedPackage.description || 'No description available.'}</p>
              {selectedPackage.business_intent && (
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
                  <span className="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase">Functional Objective</span>
                  <p className="text-sm mt-1">{selectedPackage.business_intent}</p>
                </div>
              )}
            </div>

            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Boxes size={20} /> Internal Components
            </h3>

            {compLoading ? <Loader2 className="animate-spin mx-auto" /> : (
              <div className="space-y-4">
                {components.length === 0 && <p className="text-muted-foreground italic">No components found for this package.</p>}
                {components.map((comp) => (
                  <div key={comp.component_id} className="bg-card border border-border rounded-lg overflow-hidden">
                    <div className="bg-muted/50 p-3 flex justify-between items-center border-b border-border">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold bg-background px-2 py-0.5 rounded border border-border">
                          {comp.type}
                        </span>
                        <span className="font-semibold">{comp.name}</span>
                      </div>
                    </div>

                    <div className="p-4">
                      {/* Mapping Info if exists */}
                      {(comp.source_mapping?.length > 0 || comp.target_mapping?.length > 0) && (
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <div className="p-3 bg-accent/30 rounded border border-border">
                            <div className="text-[10px] font-bold text-muted-foreground uppercase mb-1">Source Mapping</div>
                            {comp.source_mapping.map((m: any, idx: number) => (
                              <div key={idx} className="text-xs font-medium">{m.asset_name}: {m.columns?.join(', ')}</div>
                            ))}
                          </div>
                          <div className="p-3 bg-accent/30 rounded border border-border">
                            <div className="text-[10px] font-bold text-muted-foreground uppercase mb-1">Target Mapping</div>
                            {comp.target_mapping.map((m: any, idx: number) => (
                              <div key={idx} className="text-xs font-medium">{m.asset_name}: {m.columns?.join(', ')}</div>
                            ))}
                          </div>
                        </div>
                      )}

                      {comp.logic_raw && (
                        <div className="mt-2">
                          <span className="text-xs font-bold text-muted-foreground uppercase mb-2 block">Extracted Logic</span>
                          <pre className="p-3 bg-black text-green-400 font-mono text-xs rounded overflow-x-auto whitespace-pre-wrap max-h-64 overflow-y-auto">
                            {comp.logic_raw}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
            <Package size={48} strokeWidth={1} className="mb-4 opacity-20" />
            <p>Select a package to see its internal structure and logic.</p>
          </div>
        )}
      </div>
    </div>
  );
}
