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
          <div key={it.id} className="border rounded-xl p-6 bg-card hover:shadow-md transition-shadow flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex justify-between items-start">
                <div className="p-3 bg-muted rounded-lg">
                  {it.icon}
                </div>
                {it.status === 'not_configured' ? (
                  <span className="text-[10px] bg-muted text-muted-foreground px-2 py-1 rounded-full uppercase font-bold tracking-wider">Not Configured</span>
                ) : (
                  <span className="text-[10px] bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 px-2 py-1 rounded-full uppercase font-bold tracking-wider">Ready to connect</span>
                )}
              </div>
              <div>
                <h3 className="font-bold">{it.name}</h3>
                <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                  {it.description}
                </p>
              </div>
            </div>
            <button className="w-full mt-6 py-2 px-4 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity">
              Configure
            </button>
          </div>
        ))}
      </div>

      <div className="mt-12 p-6 border border-dashed rounded-xl bg-muted/30">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-primary/10 rounded-full">
            <AlertCircle className="text-primary" />
          </div>
          <div>
            <h4 className="font-bold text-sm">Próximos Pasos</h4>
            <p className="text-xs text-muted-foreground mt-1">
              Las integraciones con Unity Catalog y Purview requieren credenciales de Service Principal. 
              La ingesta de dbt permite cargar el archivo `manifest.json` directamente.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
