'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import {
    FileCode, Loader2, Save, Plus, ChevronRight,
    Layers, Settings, AlertCircle, CheckCircle2,
    Trash2, Edit3, BookOpen
} from 'lucide-react';
import Link from 'next/link';
import HelpOverlay from '@/components/HelpOverlay';

interface PromptLayer {
    id: string;
    name: string;
    layer_type: 'BASE' | 'DOMAIN' | 'ORG' | 'SOLUTION';
    content: string;
    project_id?: string;
}

interface ActionMapping {
    action_name: string;
    base_layer_id: string;
    domain_layer_id?: string;
    org_layer_id?: string;
}

interface ProjectMapping {
    project_id: string;
    action_name: string;
    solution_layer_id: string;
}

interface Project {
    id: string;
    name: string;
}

export default function AdminPromptsPage() {
    const [layers, setLayers] = useState<PromptLayer[]>([]);
    const [mappings, setMappings] = useState<ActionMapping[]>([]);
    const [projects, setProjects] = useState<Project[]>([]);
    const [projectMappings, setProjectMappings] = useState<ProjectMapping[]>([]);
    const [selectedProjectId, setSelectedProjectId] = useState<string | 'GLOBAL'>('GLOBAL');
    const [loading, setLoading] = useState(true);
    const [editingLayer, setEditingLayer] = useState<Partial<PromptLayer> | null>(null);
    const [nav, setNav] = useState<'layers' | 'mappings'>('layers');
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const [helpOpen, setHelpOpen] = useState(false);

    const api_url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    useEffect(() => {
        fetchData();
    }, []);

    useEffect(() => {
        if (selectedProjectId !== 'GLOBAL') {
            fetchProjectMappings(selectedProjectId);
        } else {
            setProjectMappings([]);
        }
    }, [selectedProjectId]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [layersRes, mappingsRes, projectsRes] = await Promise.all([
                axios.get(`${api_url}/admin/prompts/layers`),
                axios.get(`${api_url}/admin/prompts/config`),
                axios.get(`${api_url}/solutions`) // Assuming /solutions returns all projects
            ]);
            setLayers(layersRes.data);
            setMappings(mappingsRes.data);
            setProjects(projectsRes.data);
        } catch (e) {
            console.error(e);
            setStatusMsg({ type: 'error', text: 'Failed to fetch prompt data' });
        } finally {
            setLoading(false);
        }
    };

    const fetchProjectMappings = async (pid: string) => {
        try {
            const res = await axios.get(`${api_url}/admin/prompts/solutions/${pid}/config`);
            setProjectMappings(res.data);
        } catch (e) {
            console.error(e);
        }
    };

    const handleSaveLayer = async () => {
        if (!editingLayer?.name || !editingLayer?.content) return;
        try {
            await axios.post(`${api_url}/admin/prompts/layers`, editingLayer);
            setStatusMsg({ type: 'success', text: 'Layer saved successfully' });
            setEditingLayer(null);
            fetchData();
        } catch (e) {
            setStatusMsg({ type: 'error', text: 'Error saving layer' });
        }
    };

    const handleUpdateMapping = async (mapping: ActionMapping) => {
        try {
            await axios.patch(`${api_url}/admin/prompts/config`, mapping);
            setStatusMsg({ type: 'success', text: `Mapping for ${mapping.action_name} updated` });
            fetchData();
        } catch (e) {
            setStatusMsg({ type: 'error', text: 'Error updating mapping' });
        }
    };

    const handleUpdateProjectMapping = async (mapping: ProjectMapping) => {
        try {
            await axios.patch(`${api_url}/admin/prompts/solutions/config`, mapping);
            setStatusMsg({ type: 'success', text: `Project rule for ${mapping.action_name} updated` });
            fetchProjectMappings(mapping.project_id);
        } catch (e) {
            setStatusMsg({ type: 'error', text: 'Error updating project mapping' });
        }
    };

    if (loading) return <div className="flex justify-center p-12"><Loader2 className="animate-spin text-primary" size={48} /></div>;

    return (
        <div className="min-h-screen bg-background text-foreground p-8">
            <div className="max-w-6xl mx-auto space-y-8">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="bg-primary/10 p-3 rounded-xl text-primary">
                            <FileCode size={32} />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold">Prompt Management</h1>
                            <p className="text-muted-foreground">Configure Agent Layers (Base, Domain, Org)</p>
                        </div>
                    </div>
                    <div className="flex gap-4">
                        <Link href="/admin/model-config" className="text-sm font-medium hover:underline flex items-center gap-1">
                            <Settings size={14} /> Model Routing
                        </Link>
                        <Link href="/dashboard" className="text-sm font-medium hover:underline text-muted-foreground">
                            Dashboard
                        </Link>
                    </div>
                </div>

                {statusMsg && (
                    <div className={`p-4 rounded-lg border flex items-center justify-between gap-3 ${statusMsg.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-600' : 'bg-red-500/10 border-red-500/20 text-red-600'
                        }`}>
                        <div className="flex items-center gap-3">
                            {statusMsg.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
                            <span className="text-sm font-medium">{statusMsg.text}</span>
                        </div>
                        <button onClick={() => setStatusMsg(null)} className="text-xs opacity-50 hover:opacity-100">Dismiss</button>
                    </div>
                )}

                {/* Tab Navigation */}
                <div className="flex border-b border-border">
                    <button
                        onClick={() => setNav('layers')}
                        className={`px-6 py-3 font-semibold transition-colors border-b-2 ${nav === 'layers' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground'}`}
                    >
                        Prompt Layers
                    </button>
                    <button
                        onClick={() => setNav('mappings')}
                        className={`px-6 py-3 font-semibold transition-colors border-b-2 ${nav === 'mappings' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground'}`}
                    >
                        Action Mappings
                    </button>
                </div>

                {nav === 'layers' && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Layers List */}
                        <div className="lg:col-span-1 space-y-4">
                            <button
                                onClick={() => setEditingLayer({ layer_type: 'BASE', name: '', content: '' })}
                                className="w-full flex items-center justify-center gap-2 py-3 border-2 border-dashed rounded-xl hover:border-primary hover:bg-primary/5 transition-all text-muted-foreground hover:text-primary"
                            >
                                <Plus size={20} /> Add New Layer
                            </button>
                            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
                                {layers.map(layer => (
                                    <div
                                        key={layer.id}
                                        onClick={() => setEditingLayer(layer)}
                                        className={`p-5 border rounded-2xl cursor-pointer transition-all hover:shadow-lg ${editingLayer?.id === layer.id ? 'border-primary bg-primary/5 ring-1 ring-primary/20' : 'bg-card hover:bg-muted/30 border-border'}`}
                                    >
                                        <div className="flex justify-between items-start">
                                            <span className={`text-[9px] px-2 py-0.5 rounded-md font-black uppercase tracking-wider ${layer.layer_type === 'BASE' ? 'bg-orange-500/10 text-orange-600 border border-orange-500/20' :
                                                layer.layer_type === 'DOMAIN' ? 'bg-amber-500/10 text-amber-600 border border-amber-500/20' : 'bg-slate-500/10 text-slate-600 border border-slate-500/20'
                                                }`}>
                                                {layer.layer_type}
                                            </span>
                                        </div>
                                        <h3 className="font-black text-sm mt-4 tracking-tight">{layer.name}</h3>
                                        <p className="text-[10px] text-muted-foreground/60 mt-2 line-clamp-2 font-medium italic leading-relaxed">
                                            {layer.content.substring(0, 100)}...
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Editor Area */}
                        <div className="lg:col-span-2">
                            {editingLayer ? (
                                <div className="bg-card border rounded-xl p-8 shadow-md space-y-6 flex flex-col h-full">
                                    <div className="flex justify-between items-center">
                                        <h2 className="text-xl font-bold flex items-center gap-2">
                                            <Edit3 size={20} className="text-primary" />
                                            {editingLayer.id ? 'Edit Layer' : 'Create New Layer'}
                                        </h2>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => setEditingLayer(null)}
                                                className="px-4 py-2 text-sm text-muted-foreground hover:bg-muted rounded-lg"
                                            >
                                                Cancel
                                            </button>
                                            <button
                                                onClick={handleSaveLayer}
                                                className="px-6 py-2 text-sm bg-primary text-primary-foreground font-semibold rounded-lg hover:bg-primary/90 flex items-center gap-2"
                                            >
                                                <Save size={18} /> Save Layer
                                            </button>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-muted-foreground uppercase">Layer Type</label>
                                            <select
                                                value={editingLayer.layer_type}
                                                onChange={(e) => setEditingLayer({ ...editingLayer, layer_type: e.target.value as any })}
                                                className="w-full bg-muted/50 border rounded-lg p-2 outline-none focus:ring-2 focus:ring-primary"
                                            >
                                                <option value="BASE">BASE (Fundamental Logic)</option>
                                                <option value="DOMAIN">DOMAIN (SSIS, SQL expert)</option>
                                                <option value="ORG">ORG (Guidelines/Org Context)</option>
                                                <option value="SOLUTION">SOLUTION (Project Specific)</option>
                                            </select>
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-muted-foreground uppercase">Unique Name</label>
                                            <input
                                                type="text"
                                                value={editingLayer.name}
                                                onChange={(e) => setEditingLayer({ ...editingLayer, name: e.target.value })}
                                                className="w-full bg-muted/50 border rounded-lg p-2 outline-none focus:ring-2 focus:ring-primary"
                                                placeholder="e.g. base_analysis_v4"
                                            />
                                        </div>
                                    </div>

                                    <div className="flex-1 space-y-1 flex flex-col">
                                        <label className="text-xs font-bold text-muted-foreground uppercase">Content (Markdown)</label>
                                        <textarea
                                            className="w-full flex-1 bg-muted/30 border rounded-xl p-6 font-mono text-sm outline-none focus:ring-2 focus:ring-primary resize-none min-h-[400px]"
                                            value={editingLayer.content}
                                            onChange={(e) => setEditingLayer({ ...editingLayer, content: e.target.value })}
                                            placeholder="# System Instructions..."
                                        />
                                    </div>
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center border-2 border-dashed rounded-xl bg-muted/5 p-12 text-center text-muted-foreground">
                                    <Layers size={48} className="mb-4 opacity-20" />
                                    <p className="text-lg font-medium">Select a layer to edit or create a new one</p>
                                    <p className="text-sm">Prompt layers are shared fragments used to compose final instructions.</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {nav === 'mappings' && (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between bg-card p-4 border rounded-xl shadow-sm">
                            <div className="flex items-center gap-4">
                                <div className="bg-primary/10 p-2 rounded-lg text-primary">
                                    <Settings size={20} />
                                </div>
                                <div>
                                    <label className="text-[10px] font-bold text-muted-foreground uppercase block">Configuration Scope</label>
                                    <select
                                        value={selectedProjectId}
                                        onChange={(e) => setSelectedProjectId(e.target.value)}
                                        className="bg-transparent border-none font-bold text-lg outline-none cursor-pointer focus:ring-0 p-0"
                                    >
                                        <option value="GLOBAL">🌐 Global Standards</option>
                                        {projects.map(p => (
                                            <option key={p.id} value={p.id}>📂 Project: {p.name}</option>
                                        ))}
                                    </select>
                                </div>
                                <button
                                    onClick={() => setHelpOpen(true)}
                                    className="bg-primary/10 hover:bg-primary/20 p-2 rounded-lg text-primary transition-colors flex items-center gap-2 text-xs font-bold"
                                    title="Open Guide"
                                >
                                    <BookOpen size={16} />
                                    Guide
                                </button>
                            </div>
                            <div className="text-right">
                                <span className="text-[10px] font-bold text-muted-foreground uppercase block">Hierarchy depth</span>
                                <span className="text-xs font-medium">
                                    {selectedProjectId === 'GLOBAL' ? '3 Layers (Base → Dom → Org)' : '4 Layers (Base → Dom → Org → Sol)'}
                                </span>
                            </div>
                        </div>

                        <div className="bg-card border rounded-xl shadow-sm overflow-hidden">
                            <table className="w-full border-collapse">
                                <thead className="bg-muted/50 text-[10px] font-bold text-muted-foreground uppercase tracking-wider text-left border-b">
                                    <tr>
                                        <th className="px-6 py-4 w-1/4">Action / Feature</th>
                                        <th className="px-6 py-4">1. Base Layer</th>
                                        <th className="px-6 py-4">2. Domain Layer</th>
                                        <th className="px-6 py-4">3. Org Guidelines</th>
                                        {selectedProjectId !== 'GLOBAL' && <th className="px-6 py-4 bg-primary/5 text-primary">4. Solution Rules</th>}
                                    </tr>
                                </thead>
                                <tbody className="text-sm divide-y divide-border">
                                    {mappings.length > 0 ? mappings.map((mapping, idx) => {
                                        const projMapping = projectMappings.find(pm => pm.action_name === mapping.action_name);

                                        return (
                                            <tr key={idx} className="hover:bg-muted/5 transition-colors group">
                                                <td className="px-6 py-4 font-mono font-bold text-primary group-hover:translate-x-1 transition-transform">
                                                    {mapping.action_name}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <select
                                                        disabled={selectedProjectId !== 'GLOBAL'}
                                                        value={mapping.base_layer_id || ''}
                                                        onChange={(e) => handleUpdateMapping({ ...mapping, base_layer_id: e.target.value })}
                                                        className="bg-muted/30 border rounded-md p-1.5 outline-none focus:border-primary text-xs w-full disabled:opacity-50"
                                                    >
                                                        <option value="">None</option>
                                                        {layers.filter(l => l.layer_type === 'BASE').map(l => (
                                                            <option key={l.id} value={l.id}>{l.name}</option>
                                                        ))}
                                                    </select>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <select
                                                        disabled={selectedProjectId !== 'GLOBAL'}
                                                        value={mapping.domain_layer_id || ''}
                                                        onChange={(e) => handleUpdateMapping({ ...mapping, domain_layer_id: e.target.value })}
                                                        className="bg-muted/30 border rounded-md p-1.5 outline-none focus:border-primary text-xs w-full disabled:opacity-50"
                                                    >
                                                        <option value="">None / Auto</option>
                                                        {layers.filter(l => l.layer_type === 'DOMAIN').map(l => (
                                                            <option key={l.id} value={l.id}>{l.name}</option>
                                                        ))}
                                                    </select>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <select
                                                        disabled={selectedProjectId !== 'GLOBAL'}
                                                        value={mapping.org_layer_id || ''}
                                                        onChange={(e) => handleUpdateMapping({ ...mapping, org_layer_id: e.target.value })}
                                                        className="bg-muted/30 border rounded-md p-1.5 outline-none focus:border-primary text-xs w-full disabled:opacity-50"
                                                    >
                                                        <option value="">None</option>
                                                        {layers.filter(l => l.layer_type === 'ORG').map(l => (
                                                            <option key={l.id} value={l.id}>{l.name}</option>
                                                        ))}
                                                    </select>
                                                </td>
                                                {selectedProjectId !== 'GLOBAL' && (
                                                    <td className="px-6 py-4 bg-primary/5">
                                                        <select
                                                            value={projMapping?.solution_layer_id || ''}
                                                            onChange={(e) => handleUpdateProjectMapping({
                                                                project_id: selectedProjectId,
                                                                action_name: mapping.action_name,
                                                                solution_layer_id: e.target.value
                                                            })}
                                                            className="bg-primary/10 border-primary/20 border rounded-md p-1.5 outline-none focus:ring-1 focus:ring-primary text-xs w-full font-bold text-primary"
                                                        >
                                                            <option value="">+ Add Project Rule</option>
                                                            {layers.filter(l => l.layer_type === 'SOLUTION' && (!l.project_id || l.project_id === selectedProjectId)).map(l => (
                                                                <option key={l.id} value={l.id}>{l.name}</option>
                                                            ))}
                                                        </select>
                                                    </td>
                                                )}
                                            </tr>
                                        );
                                    }) : (
                                        <tr>
                                            <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                                                No action configurations found.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>

            <HelpOverlay
                isOpen={helpOpen}
                onClose={() => setHelpOpen(false)}
                title="Prompt Architect Guide"
                docPath="/docs/prompts_help.md"
            />
        </div>
    );
}
