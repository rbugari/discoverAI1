'use client';

import { useState } from 'react';
import { Database, Share2, FileCode, CheckCircle2, AlertCircle } from 'lucide-react';

interface GovernanceViewProps {
  solutionId: string;
}

export default function GovernanceView({ solutionId }: GovernanceViewProps) {
  const [integrations] = useState([
    {
      id: 'dbt',
      name: 'dbt Cloud / Core',
      icon: <FileCode className="text-orange-500" />,
      status: 'pending',
      description: 'Ingest manifest.json to enrich lineage with dbt models and meta.'
    },
    {
      id: 'unity',
      name: 'Databricks Unity Catalog',
      icon: <Database className="text-blue-500" />,
      status: 'not_configured',
      description: 'Sync discovered assets to Unity Catalog as external tables.'
    },
    {
      id: 'purview',
      name: 'Microsoft Purview',
      icon: <Share2 className="text-purple-500" />,
      status: 'not_configured',
      description: 'Push technical metadata to Purview Data Map.'
    }
  ]);

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div className="space-y-1">
        <h2 className="text-2xl font-bold tracking-tight">Governance & Integrations</h2>
        <p className="text-muted-foreground">
          Connect Nexus with your data stack and export technical lineage.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {integrations.map((it) => (
          <div key={it.id} className="border rounded-[2rem] p-8 bg-card hover:bg-primary/5 hover:border-primary/20 transition-all flex flex-col justify-between group">
            <div className="space-y-6">
              <div className="flex justify-between items-start">
                <div className="p-4 bg-muted rounded-2xl group-hover:bg-primary/10 transition-colors">
                  {it.icon}
                </div>
                {it.status === 'not_configured' ? (
                  <span className="text-[9px] bg-muted text-muted-foreground/60 px-3 py-1.5 rounded-lg uppercase font-black tracking-widest">Not Configured</span>
                ) : (
                  <span className="text-[9px] bg-primary/10 text-primary px-3 py-1.5 rounded-lg uppercase font-black tracking-widest border border-primary/20">Ready to connect</span>
                )}
              </div>
              <div>
                <h3 className="text-lg font-black tracking-tight">{it.name}</h3>
                <p className="text-xs font-medium text-muted-foreground/60 mt-3 leading-relaxed">
                  {it.description}
                </p>
              </div>
            </div>
            <button className="w-full mt-8 py-3 px-6 bg-primary text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-primary/10 hover:shadow-primary/20 transition-all hover:scale-[1.02]">
              Configure Integration
            </button>
          </div>
        ))}
      </div>

      <div className="mt-12 p-8 border border-primary/10 rounded-[2.5rem] bg-primary/5 relative overflow-hidden group">
        <div className="flex items-center gap-6 relative z-10">
          <div className="p-4 bg-primary/10 rounded-2xl">
            <AlertCircle className="text-primary" />
          </div>
          <div>
            <h4 className="font-black text-xs uppercase tracking-widest text-primary mb-2">Next Steps & Intelligence</h4>
            <p className="text-[11px] font-medium text-muted-foreground/80 leading-relaxed italic">
              Unity Catalog and Microsoft Purview integrations require Service Principal credentials for deep sync.
              The dbt ingestion engine supports direct `manifest.json` uploads to enrich logical lineage and metadata tags.
            </p>
          </div>
        </div>
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
      </div>
    </div>
  );
}
