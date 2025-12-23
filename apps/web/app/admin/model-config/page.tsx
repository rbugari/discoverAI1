'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Settings, Loader2, Save, RefreshCw, 
  Shield, Server, Activity, CheckCircle2, AlertCircle
} from 'lucide-react';
import Link from 'next/link';

interface ConfigInfo {
  providers: string[];
  routings: string[];
  active: {
    provider: string;
    routing: string;
  };
}

export default function AdminConfigPage() {
  const [config, setConfig] = useState<ConfigInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeProvider, setActiveProvider] = useState('');
  const [activeRouting, setActiveRouting] = useState('');
  const [statusMsg, setStatusMsg] = useState<{type: 'success' | 'error', text: string} | null>(null);

  const api_url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${api_url}/admin/model-config`);
      setConfig(res.data);
      setActiveProvider(res.data.active.provider);
      setActiveRouting(res.data.active.routing);
    } catch (e) {
      console.error(e);
      setStatusMsg({type: 'error', text: 'Failed to load configuration'});
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setStatusMsg(null);
    try {
      await axios.post(`${api_url}/admin/model-config/activate`, {
        provider_path: activeProvider,
        routing_path: activeRouting
      });
      setStatusMsg({type: 'success', text: 'Configuration updated successfully'});
      fetchConfig();
    } catch (e: any) {
      console.error(e);
      setStatusMsg({type: 'error', text: e.response?.data?.detail || 'Failed to update configuration'});
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-background">
        <Loader2 className="animate-spin text-primary" size={48} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-primary/10 p-3 rounded-xl text-primary">
              <Settings size={32} />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Model Configuration</h1>
              <p className="text-muted-foreground">Manage LLM providers and action routings (v3.0)</p>
            </div>
          </div>
          <Link href="/dashboard" className="text-sm font-medium hover:underline text-muted-foreground">
            Back to Dashboard
          </Link>
        </div>

        {statusMsg && (
          <div className={`p-4 rounded-lg border flex items-center gap-3 ${
            statusMsg.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-600' : 'bg-red-500/10 border-red-500/20 text-red-600'
          }`}>
            {statusMsg.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
            <span className="text-sm font-medium">{statusMsg.text}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Active Config Pointing */}
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex items-center gap-2 font-semibold">
              <Shield className="text-primary" size={20} />
              <h2>Active Profile</h2>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Provider</label>
                <select 
                  value={activeProvider}
                  onChange={(e) => setActiveProvider(e.target.value)}
                  className="w-full bg-muted/50 border border-border rounded-lg p-2 focus:ring-2 focus:ring-primary outline-none"
                >
                  {config?.providers.map(p => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Routing Strategy</label>
                <select 
                  value={activeRouting}
                  onChange={(e) => setActiveRouting(e.target.value)}
                  className="w-full bg-muted/50 border border-border rounded-lg p-2 focus:ring-2 focus:ring-primary outline-none"
                >
                  {config?.routings.map(r => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>

              <button 
                onClick={handleSave}
                disabled={saving}
                className="w-full bg-primary text-primary-foreground font-semibold py-2 rounded-lg flex items-center justify-center gap-2 hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
                Apply Configuration
              </button>
            </div>
          </div>

          {/* System Status */}
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex items-center gap-2 font-semibold">
              <Activity className="text-primary" size={20} />
              <h2>System Inventory</h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-muted/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <Server size={18} className="text-muted-foreground" />
                  <span className="text-sm font-medium">Available Providers</span>
                </div>
                <span className="bg-background px-2 py-0.5 rounded border border-border text-xs font-bold">
                  {config?.providers.length}
                </span>
              </div>

              <div className="flex justify-between items-center p-3 bg-muted/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <RefreshCw size={18} className="text-muted-foreground" />
                  <span className="text-sm font-medium">Routing Profiles</span>
                </div>
                <span className="bg-background px-2 py-0.5 rounded border border-border text-xs font-bold">
                  {config?.routings.length}
                </span>
              </div>

              <div className="p-4 bg-primary/5 rounded-lg border border-primary/10">
                <p className="text-xs text-muted-foreground mb-2 italic">
                  Note: Models are routed per action (Planner, Extractor, QA) as defined in the selected Routing profile.
                </p>
                <Link href={`${api_url}/docs`} target="_blank" className="text-xs text-primary font-medium hover:underline">
                  View API Documentation →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
