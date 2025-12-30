'use client';

import React, { useState, useEffect } from 'react';
import { X, HelpCircle, BookOpen, Info, Lightbulb } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

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
    const [content, setContent] = useState<string>('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (isOpen) {
            fetchContent();
        }
    }, [isOpen, docPath]);

    const fetchContent = async () => {
        setLoading(true);
        try {
            const response = await fetch(docPath);
            const text = await response.text();
            setContent(text);
        } catch (error) {
            console.error('Failed to fetch documentation:', error);
            setContent('Failed to load documentation. Please try again later.');
        } finally {
            setLoading(false);
        }
    };

    // Simple Markdown-to-JSX renderer for basic features
    // Ideally use react-markdown, but we are keeping dependencies minimal for now.
    const renderMarkdown = (text: string) => {
        return text.split('\n').map((line, i) => {
            // Headers
            if (line.startsWith('# ')) return <h1 key={i} className="text-2xl font-bold mt-6 mb-4 text-primary border-b pb-2">{line.replace('# ', '')}</h1>;
            if (line.startsWith('## ')) return <h2 key={i} className="text-xl font-bold mt-6 mb-3 text-primary/90">{line.replace('## ', '')}</h2>;
            if (line.startsWith('### ')) return <h3 key={i} className="text-lg font-bold mt-4 mb-2">{line.replace('### ', '')}</h3>;

            // Lists
            if (line.startsWith('- ')) return <li key={i} className="ml-4 mb-2 list-disc">{renderLine(line.replace('- ', ''))}</li>;
            if (line.startsWith('1. ')) return <li key={i} className="ml-4 mb-2 list-decimal">{renderLine(line.replace(/\d+\. /, ''))}</li>;

            // Empty lines
            if (line.trim() === '') return <div key={i} className="h-4" />;

            // Paragraph
            return <p key={i} className="mb-4 leading-relaxed text-muted-foreground">{renderLine(line)}</p>;
        });
    };

    const renderLine = (line: string) => {
        // Very basic bold and link rendering
        let parts: any[] = [line];

        // Bold
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
                <div className="p-6 border-b flex items-center justify-between bg-muted/30">
                    <div className="flex items-center gap-3">
                        <div className="bg-primary/10 p-2 rounded-lg text-primary">
                            <BookOpen size={20} />
                        </div>
                        <div>
                            <h2 className="font-bold text-lg">{title}</h2>
                            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Documentation & Help</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-muted rounded-full transition-colors text-muted-foreground"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-8 prose prose-slate dark:prose-invert max-w-none">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-40 gap-3">
                            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                            <p className="text-sm text-muted-foreground">Loading guide...</p>
                        </div>
                    ) : (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                            {docPath.includes('prompts') ? (
                                <div className="bg-primary/5 border border-primary/10 rounded-xl p-4 mb-8 flex gap-4 items-start">
                                    <Lightbulb className="text-primary mt-1 shrink-0" size={20} />
                                    <div>
                                        <h4 className="font-bold text-sm text-primary">Expert Insight</h4>
                                        <p className="text-xs text-muted-foreground">The Prompt Matrix is the most powerful tool in DiscoverAI. Small tweaks here define the analytical IQ of the entire system.</p>
                                    </div>
                                </div>
                            ) : (
                                <div className="bg-blue-500/5 border border-blue-500/10 rounded-xl p-4 mb-8 flex gap-4 items-start">
                                    <Info className="text-blue-500 mt-1 shrink-0" size={20} />
                                    <div>
                                        <h4 className="font-bold text-sm text-blue-500">System Tip</h4>
                                        <p className="text-xs text-muted-foreground">Routings allow you to use cheaper models for simple tasks and reserved "High-IQ" models for deep architectural analysis.</p>
                                    </div>
                                </div>
                            )}
                            {renderMarkdown(content)}

                            <div className="mt-12 pt-8 border-t text-center space-y-4">
                                <p className="text-sm text-muted-foreground italic">"Everything you configure here defines how DiscoverAI perceives and interprets technical complexity."</p>
                                <button
                                    onClick={onClose}
                                    className="px-6 py-2 bg-muted hover:bg-muted/80 rounded-full text-xs font-bold transition-colors"
                                >
                                    Got it, close help
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
