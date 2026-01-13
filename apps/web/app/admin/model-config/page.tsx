'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Settings, Loader2, Save, RefreshCw,
  Shield, Server, Activity, CheckCircle2, AlertCircle,
  BookOpen
} from 'lucide-react';
import Link from 'next/link';
import HelpOverlay from '@/components/HelpOverlay';

interface RoutingInfo {
  path: string;
  name: string;
  provider: string;
}

interface ConfigInfo {
  providers: string[];
  routings: RoutingInfo[];
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
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [helpOpen, setHelpOpen] = useState(false);

  // Editor State
  const [editingFile, setEditingFile] = useState<string | null>(null);
  const [editorContent, setEditorContent] = useState('');
  const [isEditorLoading, setIsEditorLoading] = useState(false);
  const [isSaveAs, setIsSaveAs] = useState(false);
  const [newFileName, setNewFileName] = useState('');

  const api_url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${api_url}/admin/model-config`);
      const data = res.data;
      setConfig(data);
      // Only set initial active if not already interacting
      if (!activeProvider) {
        setActiveProvider(data.active.provider);
        setActiveRouting(data.active.routing);
      }
    } catch (e) {
      console.error(e);
      setStatusMsg({ type: 'error', text: 'Failed to load configuration' });
    } finally {
      setLoading(false);
    }
  };

  // 1:N Filtering Logic
  const filteredRoutings = config?.routings.filter(r => r.provider === activeProvider) || [];

  // Security: Auto-correct routing if provider changes
  useEffect(() => {
    if (activeProvider && config) {
      const currentRoutingObj = config.routings.find(r => r.path === activeRouting);
      if (currentRoutingObj && currentRoutingObj.provider !== activeProvider) {
        // Find first compatible routing for the new provider
        const firstCompatible = config.routings.find(r => r.provider === activeProvider);
        if (firstCompatible) setActiveRouting(firstCompatible.path);
      }
    }
  }, [activeProvider, config]);

  const handleSave = async () => {
    setSaving(true);
    setStatusMsg(null);
    try {
      await axios.post(`${api_url}/admin/model-config/activate`, {
        provider_path: activeProvider,
        routing_path: activeRouting
      });
      setStatusMsg({ type: 'success', text: 'Configuration updated successfully' });
      fetchConfig();
    } catch (e: any) {
      console.error(e);
      setStatusMsg({ type: 'error', text: e.response?.data?.detail || 'Failed to update configuration' });
    } finally {
      setSaving(false);
    }
  };

  const handleEditFile = async (path: string) => {
    setEditingFile(path);
    setIsEditorLoading(true);
    try {
      const res = await axios.get(`${api_url}/admin/model-config/file`, { params: { path } });
      setEditorContent(res.data.content);
    } catch (e: any) {
      console.error(e);
      setStatusMsg({ type: 'error', text: 'Failed to load file content' });
      setEditingFile(null);
    } finally {
      setIsEditorLoading(false);
    }
  };

  const handleSaveFile = async () => {
    if (!editingFile) return;
    setSaving(true);

    // Determine path: original or new if clone
    let targetPath = editingFile;
    if (isSaveAs) {
      if (!newFileName) {
        setStatusMsg({ type: 'error', text: 'Please enter a name for the new file' });
        setSaving(false);
        return;
      }
      // Ensure path prefix matches (providers/ or routings/)
      const prefix = editingFile.split('/')[0];
      const cleanName = newFileName.endsWith('.yml') ? newFileName : `${newFileName}.yml`;
      targetPath = `${prefix}/${cleanName}`;
    }

    try {
      await axios.post(`${api_url}/admin/model-config/file`, {
        path: targetPath,
        content: editorContent
      });
      setStatusMsg({ type: 'success', text: isSaveAs ? `File ${targetPath} created successfully` : `File ${targetPath} saved successfully` });
      setEditingFile(null);
      setIsSaveAs(false);
      setNewFileName('');
      fetchConfig(); // Refresh inventory
    } catch (e: any) {
      console.error(e);
      setStatusMsg({ type: 'error', text: e.response?.data?.detail || 'Failed to save file' });
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
          <div className="flex items-center gap-4">
            <button
              onClick={() => setHelpOpen(true)}
              className="bg-primary/10 hover:bg-primary/20 p-2 px-3 rounded-lg text-primary transition-colors flex items-center gap-2 text-xs font-bold"
            >
              <BookOpen size={16} />
              Guide
            </button>
            <Link href="/dashboard" className="text-sm font-medium hover:underline text-muted-foreground">
              Back to Dashboard
            </Link>
          </div>
        </div>

        {statusMsg && (
          <div className={`p-4 rounded-lg border flex items-center gap-3 ${statusMsg.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-600' : 'bg-red-500/10 border-red-500/20 text-red-600'
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
                  {filteredRoutings.map(r => (
                    <option key={r.path} value={r.path}>{r.name} ({r.path.split('/').pop()})</option>
                  ))}
                  {filteredRoutings.length === 0 && (
                    <option disabled>No routings for this provider</option>
                  )}
                </select>
                {filteredRoutings.length === 0 && (
                  <p className="text-[10px] text-orange-500 font-bold mt-1 uppercase italic">
                    ⚠️ Critical: No compatible routing found for this provider.
                  </p>
                )}
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

          {/* System Status & Editor */}
          <div className="space-y-8">
            <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-6">
              <div className="flex items-center gap-2 font-semibold">
                <Activity className="text-primary" size={20} />
                <h2>Environment Inventory</h2>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest pl-1">Available Providers</span>
                  <div className="space-y-2">
                    {config?.providers.map(p => (
                      <div key={p} className="flex justify-between items-center p-3 bg-muted/30 rounded-lg group">
                        <div className="flex items-center gap-3">
                          <Server size={14} className="text-muted-foreground" />
                          <span className="text-xs font-medium">{p}</span>
                        </div>
                        <button
                          onClick={() => handleEditFile(p)}
                          className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-primary/10 rounded-md text-primary transition-all text-[10px] font-bold uppercase tracking-tighter"
                        >
                          Raw Edit
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest pl-1">Routing Profiles (for current provider)</span>
                  <div className="space-y-2">
                    {filteredRoutings.map(r => (
                      <div key={r.path} className="flex justify-between items-center p-3 bg-muted/30 rounded-lg group border border-transparent hover:border-primary/20 transition-all">
                        <div className="flex items-center gap-3">
                          <RefreshCw size={14} className="text-primary" />
                          <div className="flex flex-col">
                            <span className="text-xs font-bold leading-none">{r.name}</span>
                            <span className="text-[9px] font-mono text-muted-foreground">{r.path}</span>
                          </div>
                        </div>
                        <button
                          onClick={() => handleEditFile(r.path)}
                          className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-primary/10 rounded-md text-primary transition-all text-[10px] font-bold uppercase tracking-tighter"
                        >
                          Raw Edit
                        </button>
                      </div>
                    ))}
                    {filteredRoutings.length === 0 && (
                      <p className="text-xs text-center text-muted-foreground py-4 italic border border-dashed border-border rounded-lg">
                        No routing profiles configured for this provider.
                      </p>
                    )}
                  </div>
                </div>

                <div className="p-4 bg-primary/5 rounded-lg border border-primary/10">
                  <p className="text-xs text-muted-foreground mb-2 italic leading-relaxed">
                    Note: Models are routed per action (Planner, Extractor, QA) as defined in the selected Routing profile. Editing these files requires YAML knowledge.
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

      {/* Premium YAML Editor Modal */}
      {editingFile && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 md:p-8 animate-in fade-in duration-300">
          <div className="absolute inset-0 bg-black/80 backdrop-blur-md" onClick={() => setEditingFile(null)} />

          <div className="relative w-full max-w-7xl h-[85vh] bg-card border border-white/10 rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-300">
            {/* Modal Header */}
            <div className="p-6 border-b border-border flex items-center justify-between bg-muted/20">
              <div className="flex items-center gap-4">
                <div className="bg-primary/20 p-2 rounded-xl text-primary">
                  <Save size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-black tracking-tight leading-none mb-1">YAML Configuration Editor</h3>
                  <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">
                    {isSaveAs ? "Cloning Profile" : `Editing: ${editingFile}`}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {!isSaveAs && (
                  <button
                    onClick={() => setIsSaveAs(true)}
                    className="px-4 py-2 text-xs font-bold text-primary hover:bg-primary/10 rounded-xl transition-all border border-primary/20"
                  >
                    Save As...
                  </button>
                )}
                <button
                  onClick={() => { setEditingFile(null); setIsSaveAs(false); }}
                  className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-full transition-all"
                >
                  <Settings size={20} className="rotate-45" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-hidden flex flex-col">
              {isEditorLoading ? (
                <div className="flex-1 flex items-center justify-center">
                  <Loader2 className="animate-spin text-primary" size={48} />
                </div>
              ) : (
                <div className="flex-1 flex flex-col p-6 space-y-4">
                  {isSaveAs && (
                    <div className="bg-primary/5 p-4 rounded-2xl border border-primary/20 flex items-center gap-4 animate-in slide-in-from-top-2 duration-300">
                      <div className="flex-1">
                        <label className="text-[10px] font-black uppercase text-primary tracking-widest block mb-1">New Filename</label>
                        <div className="flex items-center gap-2 bg-background/50 border border-border rounded-lg px-3 py-2">
                          <span className="text-xs text-muted-foreground font-mono">{editingFile.split('/')[0]}/</span>
                          <input
                            type="text"
                            value={newFileName}
                            onChange={(e) => setNewFileName(e.target.value)}
                            placeholder="my-new-config"
                            className="bg-transparent border-none outline-none text-sm font-mono flex-1 text-foreground"
                            autoFocus
                          />
                          <span className="text-xs text-muted-foreground font-mono">.yml</span>
                        </div>
                      </div>
                      <div className="flex gap-2 pt-4">
                        <button
                          onClick={() => setIsSaveAs(false)}
                          className="px-4 py-2 text-xs font-bold text-muted-foreground bg-muted rounded-lg"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleSaveFile}
                          disabled={saving}
                          className="px-6 py-2 text-xs font-black bg-primary text-white rounded-lg shadow-lg shadow-primary/20"
                        >
                          Confirm Clone
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="flex-1 relative group bg-slate-950 rounded-2xl border border-white/5 overflow-hidden">
                    <textarea
                      className="w-full h-full bg-transparent text-emerald-400 font-mono text-base p-8 outline-none resize-none selection:bg-primary/30 leading-relaxed custom-scrollbar"
                      value={editorContent}
                      onChange={(e) => setEditorContent(e.target.value)}
                      spellCheck={false}
                    />
                    <div className="absolute top-4 right-4 text-[9px] font-black text-white/20 uppercase tracking-widest pointer-events-none">
                      Raw View Mode
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            {!isSaveAs && (
              <div className="p-6 border-t border-border flex justify-end gap-3 bg-muted/10">
                <button
                  onClick={() => setEditingFile(null)}
                  className="px-6 py-2 text-xs font-bold text-muted-foreground hover:bg-muted rounded-xl transition-all"
                >
                  Discard Changes
                </button>
                <button
                  onClick={handleSaveFile}
                  disabled={saving}
                  className="bg-primary text-white px-8 py-2 rounded-xl text-xs font-black uppercase tracking-widest hover:shadow-xl hover:shadow-primary/20 transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <HelpOverlay
        isOpen={helpOpen}
        onClose={() => setHelpOpen(false)}
        title="Model Routing Guide"
        docPath="/docs/model_routing_help.md"
      />
    </div>
  );
}
