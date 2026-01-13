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
  const [filterType, setFilterType] = useState('ALL');

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

  const availableTypes = Array.from(new Set(packages.map(p => p.type))).filter(Boolean).sort();

  const filteredPackages = filterType === 'ALL'
    ? packages
    : packages.filter(p => p.type === filterType);

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>;

  return (
    <div className="flex h-full overflow-hidden bg-slate-950/20 p-4 gap-4">
      {/* Sidebar: Package List */}
      <div className="w-80 flex flex-col gap-4 overflow-hidden">
        <div className="p-4 rounded-2xl bg-card/50 backdrop-blur-sm border border-border/50 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-black text-muted-foreground uppercase tracking-widest flex items-center gap-2">
              <Package size={14} className="text-primary" /> Packages
            </h2>
            <span className="text-[10px] font-bold px-2 py-0.5 bg-primary/10 text-primary rounded-full">
              {filteredPackages.length}
            </span>
          </div>

          <div className="relative">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full bg-background/50 border border-border/50 rounded-xl px-3 py-2 text-xs font-bold focus:outline-none focus:ring-2 focus:ring-primary/20 appearance-none cursor-pointer"
            >
              <option value="ALL">ALL TYPES</option>
              {availableTypes.map(type => (
                <option key={type} value={type}>{type.toUpperCase()}</option>
              ))}
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground">
              <svg width="10" height="6" viewBox="0 0 10 6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 1L5 5L9 1" /></svg>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar pr-1">
          {filteredPackages.length === 0 && <div className="p-8 text-center border border-dashed border-border rounded-2xl text-muted-foreground/50 text-xs uppercase tracking-widest">No packages found</div>}
          {filteredPackages.map((pkg) => (
            <button
              key={pkg.package_id}
              onClick={() => setSelectedPackage(pkg)}
              className={`w-full text-left p-4 rounded-2xl border transition-all duration-300 group relative overflow-hidden ${selectedPackage?.package_id === pkg.package_id
                ? 'bg-primary/10 border-primary/30 shadow-lg shadow-primary/5'
                : 'bg-card/30 border-border/40 hover:bg-card/80 hover:border-primary/20 hover:translate-x-1'
                }`}
            >
              {selectedPackage?.package_id === pkg.package_id && (
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary" />
              )}
              <div className="flex items-center gap-3 mb-2">
                <div className={`p-2 rounded-lg ${selectedPackage?.package_id === pkg.package_id ? 'bg-primary text-white' : 'bg-muted text-muted-foreground group-hover:text-foreground'}`}>
                  <Package size={16} />
                </div>
                <span className={`font-bold text-sm truncate ${selectedPackage?.package_id === pkg.package_id ? 'text-primary' : 'text-foreground'}`}>{pkg.name}</span>
              </div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[9px] font-black opacity-60 px-2 py-0.5 bg-muted rounded-md uppercase tracking-wide">{pkg.type}</span>
              </div>
              {pkg.business_intent && (
                <p className="text-[10px] text-muted-foreground line-clamp-2 leading-relaxed pl-1 border-l-2 border-border/50 ml-1">{pkg.business_intent}</p>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content: Components & Logic */}
      <div className="flex-1 min-w-0 bg-card/40 backdrop-blur-md rounded-[2.5rem] border border-border/50 shadow-2xl flex flex-col relative overflow-hidden">
        {selectedPackage ? (
          <div className="flex flex-col h-full overflow-hidden">
            {/* Header */}
            <div className="p-8 border-b border-border/40 bg-gradient-to-r from-background via-muted/10 to-transparent flex-none">
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-3xl font-black tracking-tight mb-2 text-foreground">{selectedPackage.name}</h1>
                  <p className="text-muted-foreground font-medium max-w-2xl leading-relaxed">{selectedPackage.description || 'No description available for this package.'}</p>
                </div>
                <div className="px-4 py-2 rounded-xl bg-primary/5 border border-primary/10 text-primary text-[10px] font-black uppercase tracking-widest">
                  ACTIVE PACKAGE
                </div>
              </div>

              {selectedPackage.business_intent && (
                <div className="mt-6 p-4 bg-blue-500/5 border border-blue-500/10 rounded-2xl flex gap-4">
                  <div className="p-2 bg-blue-500/10 rounded-lg h-fit text-blue-500">
                    <Boxes size={18} />
                  </div>
                  <div>
                    <span className="text-[10px] font-black text-blue-500 uppercase tracking-widest block mb-1">Functional Objective</span>
                    <p className="text-sm font-medium text-foreground/80 leading-relaxed">{selectedPackage.business_intent}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Components Scroll Area */}
            <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
              <h3 className="text-sm font-black text-muted-foreground uppercase tracking-widest mb-6 flex items-center gap-2 sticky top-0 bg-card/60 backdrop-blur-md py-4 z-10 -mt-2">
                <Boxes size={16} /> Circuit Components
              </h3>

              {compLoading ? (
                <div className="flex flex-col items-center justify-center py-20 gap-4 opacity-50">
                  <Loader2 className="animate-spin text-primary" size={32} />
                  <span className="text-xs font-bold uppercase tracking-widest">Constructing Logic Flow...</span>
                </div>
              ) : (
                <div className="space-y-6">
                  {components.length === 0 && (
                    <div className="p-10 border border-dashed border-border rounded-3xl text-center">
                      <p className="text-muted-foreground font-medium italic">No components found for this package.</p>
                    </div>
                  )}
                  {components.map((comp) => (
                    <div key={comp.component_id} className="group relative bg-card/50 border border-border/30 rounded-3xl overflow-hidden hover:shadow-xl hover:border-primary/20 transition-all duration-300 hover:-translate-y-1">
                      <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                      <div className="bg-muted/30 p-4 flex justify-between items-center border-b border-border/30">
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] font-black font-mono bg-background px-2 py-1 rounded-lg border border-border text-muted-foreground uppercase tracking-wider group-hover:text-primary group-hover:border-primary/20 transition-colors">
                            {comp.type}
                          </span>
                          <span className="font-bold text-foreground tracking-tight">{comp.name}</span>
                        </div>
                      </div>

                      <div className="p-6">
                        {/* Mapping Info if exists */}
                        {(comp.source_mapping?.length > 0 || comp.target_mapping?.length > 0) && (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                            {comp.source_mapping?.length > 0 && (
                              <div className="p-4 bg-background/50 rounded-2xl border border-border/50">
                                <div className="text-[9px] font-black text-muted-foreground uppercase tracking-widest mb-3 flex items-center gap-2">
                                  <div className="w-1.5 h-1.5 rounded-full bg-orange-400" /> Source Input
                                </div>
                                <div className="space-y-2">
                                  {comp.source_mapping.map((m: any, idx: number) => (
                                    <div key={idx} className="text-xs font-mono text-foreground/80 bg-muted/50 px-2 py-1.5 rounded border border-border/30 truncate">
                                      <span className="font-bold text-primary/80">{m.asset_name}</span>
                                      <span className="opacity-50 mx-2">→</span>
                                      <span className="opacity-70">{m.columns?.join(', ')}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            {comp.target_mapping?.length > 0 && (
                              <div className="p-4 bg-background/50 rounded-2xl border border-border/50">
                                <div className="text-[9px] font-black text-muted-foreground uppercase tracking-widest mb-3 flex items-center gap-2">
                                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Target Output
                                </div>
                                <div className="space-y-2">
                                  {comp.target_mapping.map((m: any, idx: number) => (
                                    <div key={idx} className="text-xs font-mono text-foreground/80 bg-muted/50 px-2 py-1.5 rounded border border-border/30 truncate">
                                      <span className="font-bold text-emerald-600 dark:text-emerald-400">{m.asset_name}</span>
                                      <span className="opacity-50 mx-2">→</span>
                                      <span className="opacity-70">{m.columns?.join(', ')}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        {comp.logic_raw && (
                          <div className="mt-2">
                            <span className="text-[9px] font-black text-muted-foreground uppercase tracking-widest mb-3 block">Extracted Logic Circuit</span>
                            <div className="relative group/code">
                              <pre className="p-4 bg-slate-950 text-blue-100/90 font-mono text-[11px] rounded-2xl overflow-x-auto whitespace-pre-wrap max-h-64 overflow-y-auto border border-white/5 shadow-inner leading-relaxed custom-scrollbar">
                                {comp.logic_raw}
                              </pre>
                              <div className="absolute top-2 right-2 px-2 py-1 bg-white/10 rounded text-[9px] text-white/50 opacity-0 group-hover/code:opacity-100 transition-opacity">SQL/EXPR</div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground/30 relative overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-primary/5 via-transparent to-transparent opacity-50" />
            <Package size={64} strokeWidth={1} className="mb-6 opacity-20 animate-pulse" />
            <p className="font-black uppercase tracking-[0.3em] text-xs">Select a package to inspect</p>
          </div>
        )}
      </div>
    </div>
  );
}
