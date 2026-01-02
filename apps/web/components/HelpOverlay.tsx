'use client';

import React, { useState, useEffect } from 'react';
import { X, HelpCircle, BookOpen, Info, Lightbulb, UserCircle2 } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { usePersona, PERSONAS, PersonaType } from '../hooks/usePersona';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface HelpOverlayProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    docPath: string;
}

export default function HelpOverlay({ isOpen, onClose, title, docPath }: HelpOverlayProps) {
    const { persona, setPersona } = usePersona();
    const [content, setContent] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [currentPath, setCurrentPath] = useState(docPath);

    useEffect(() => {
        if (isOpen) {
            // If base doc is the general guide, maybe we switch to persona doc
            if (docPath.includes('guide')) {
                const personaDoc = `/docs/${persona}_guide.md`;
                setCurrentPath(personaDoc);
            } else {
                setCurrentPath(docPath);
            }
        }
    }, [isOpen, docPath, persona]);

    useEffect(() => {
        if (isOpen) {
            fetchContent();
        }
    }, [isOpen, currentPath]);

    const fetchContent = async () => {
        setLoading(true);
        try {
            const response = await fetch(currentPath);
            const text = await response.text();
            setContent(text);
        } catch (error) {
            console.error('Failed to fetch documentation:', error);
            setContent('Failed to load documentation. Please try again later.');
        } finally {
            setLoading(false);
        }
    };

    const handlePersonaChange = (p: PersonaType) => {
        setPersona(p);
    };

    // Simple Markdown-to-JSX renderer for basic features
    const renderMarkdown = (text: string) => {
        return text.split('\n').map((line, i) => {
            // Headers
            if (line.startsWith('# ')) return <h1 key={i} className="text-2xl font-bold mt-6 mb-4 text-orange-600 border-b border-orange-500/10 pb-2">{line.replace('# ', '')}</h1>;
            if (line.startsWith('## ')) return <h2 key={i} className="text-xl font-bold mt-6 mb-3 text-foreground/90">{line.replace('## ', '')}</h2>;
            if (line.startsWith('### ')) return <h3 key={i} className="text-lg font-bold mt-4 mb-2">{line.replace('### ', '')}</h3>;

            // Alerts (Blockquotes)
            if (line.startsWith('> [!TIP]')) return null; // Skip header
            if (line.startsWith('> [!NOTE]')) return null; // Skip header
            if (line.startsWith('> [!WARNING]')) return null; // Skip header
            if (line.startsWith('> ')) {
                return (
                    <div key={i} className="bg-orange-500/5 border-l-4 border-orange-500 p-4 my-6 italic text-sm text-muted-foreground bg-card">
                        {renderLine(line.replace('> ', ''))}
                    </div>
                );
            }

            // Lists
            if (line.startsWith('- ')) return <li key={i} className="ml-4 mb-2 list-disc marker:text-orange-500">{renderLine(line.replace('- ', ''))}</li>;
            if (line.startsWith('1. ')) return <li key={i} className="ml-4 mb-2 list-decimal marker:text-orange-500">{renderLine(line.replace(/\d+\. /, ''))}</li>;

            // Empty lines
            if (line.trim() === '') return <div key={i} className="h-4" />;

            // Paragraph
            return <p key={i} className="mb-4 leading-relaxed text-muted-foreground">{renderLine(line)}</p>;
        });
    };

    const renderLine = (line: string) => {
        let parts: any[] = [line];
        if (line.includes('**')) {
            const regex = /\*\*(.*?)\*\*/g;
            const fragments = line.split(regex);
            parts = fragments.map((f, idx) => idx % 2 === 1 ? <strong key={idx} className="font-bold text-foreground">{f}</strong> : f);
        }
        return parts;
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex justify-end">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-background/40 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Panel */}
            <div className={cn(
                "relative w-full max-w-lg bg-card border-l border-border h-full shadow-2xl flex flex-col transform transition-transform duration-300 ease-out",
                isOpen ? "translate-x-0" : "translate-x-full"
            )}>
                {/* Header */}
                <div className="p-6 border-b flex flex-col gap-4 bg-muted/20">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="bg-orange-500/10 p-2 rounded-lg text-orange-600">
                                <BookOpen size={20} />
                            </div>
                            <div>
                                <h2 className="font-bold text-lg">{title}</h2>
                                <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">DiscoverAI v6.0 Library</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-muted rounded-full transition-colors text-muted-foreground"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    {/* Persona Switcher */}
                    <div className="flex items-center gap-2 p-1 bg-muted/50 rounded-xl border border-border/50">
                        {PERSONAS.map((p) => (
                            <button
                                key={p.id}
                                onClick={() => handlePersonaChange(p.id)}
                                title={p.description}
                                className={cn(
                                    "flex-1 flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all",
                                    persona === p.id
                                        ? "bg-orange-500 text-white shadow-lg shadow-orange-500/20"
                                        : "hover:bg-muted text-muted-foreground"
                                )}
                            >
                                <span>{p.icon}</span>
                                <span>{p.label}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-8 prose prose-orange dark:prose-invert max-w-none">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-40 gap-3">
                            <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
                            <p className="text-xs font-medium text-muted-foreground">Consulting the archives...</p>
                        </div>
                    ) : (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                            {/* Insight Block */}
                            <div className="bg-orange-500/5 border border-orange-500/10 rounded-2xl p-5 mb-8 flex gap-4 items-start shadow-inner">
                                <div className="bg-orange-500/10 p-2 rounded-xl text-orange-600 shrink-0">
                                    <UserCircle2 size={24} />
                                </div>
                                <div>
                                    <h4 className="font-bold text-sm text-orange-600 mb-1">Tailored for {persona}s</h4>
                                    <p className="text-xs text-muted-foreground leading-relaxed">
                                        You are currently viewing guidance optimized for the <strong>{persona}</strong> profile.
                                        Switch roles in the header for different perspectives.
                                    </p>
                                </div>
                            </div>

                            <div className="help-content">
                                {renderMarkdown(content)}
                            </div>

                            <div className="mt-12 pt-8 border-t text-center space-y-6">
                                <p className="text-[11px] text-muted-foreground italic leading-relaxed px-12">
                                    "Technical complexity is a human problem first. Our tools should speak the language of those who solve it."
                                </p>
                                <button
                                    onClick={onClose}
                                    className="px-8 py-2.5 bg-zinc-900 dark:bg-zinc-100 dark:text-zinc-900 text-white rounded-full text-[10px] font-bold tracking-widest uppercase transition-all hover:scale-105 active:scale-95 shadow-xl"
                                >
                                    Dismiss Library
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
