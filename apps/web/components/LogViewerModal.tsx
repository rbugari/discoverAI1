'use client';

import React, { useEffect, useState, useRef } from 'react';
import { X, Terminal, Clock, CheckCircle2, AlertCircle, Search } from 'lucide-react';
import axios from 'axios';

interface LogEntry {
    created_at: string;
    action_taken: string;
    file_path: string;
    strategy_used: string;
    success: boolean;
    model_used?: string;
}

interface LogViewerModalProps {
    isOpen: boolean;
    onClose: () => void;
    jobId: string;
    jobStatus: string;
    title?: string;
}

export const LogViewerModal = ({ isOpen, onClose, jobId, jobStatus, title = "Process Execution Logs" }: LogViewerModalProps) => {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);
    const isJobActive = ['queued', 'running'].includes(jobStatus);

    const fetchLogs = async () => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await axios.get(`${apiUrl}/solutions/jobs/${jobId}/logs`);
            setLogs(response.data || []);
        } catch (error) {
            console.error('Error fetching logs:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isOpen && jobId) {
            fetchLogs();
            let interval: NodeJS.Timeout;
            if (isJobActive) {
                interval = setInterval(fetchLogs, 3000);
            }
            return () => clearInterval(interval);
        }
    }, [isOpen, jobId, jobStatus]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    if (!isOpen) return null;

    const filteredLogs = logs.filter(log =>
        log.file_path.toLowerCase().includes(filter.toLowerCase()) ||
        log.action_taken.toLowerCase().includes(filter.toLowerCase())
    );

    return (
        <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4 md:p-8">
            <div className="absolute inset-0 bg-black/80" onClick={onClose} />

            <div className="relative w-full max-w-5xl h-[80vh] flex flex-col bg-[#0a0a0b] border border-white/10 rounded-[2.5rem] shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-300">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-white/10 bg-[#16161a]">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-[#242428] rounded-2xl border border-primary/30">
                            <Terminal className="text-primary" size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-black tracking-tight text-white uppercase">{title}</h2>
                            <p className="text-[10px] font-bold text-primary uppercase tracking-widest leading-none mt-1">
                                Job ID: {jobId} • Status: <span className={isJobActive ? "text-orange-400 animate-pulse" : "text-emerald-400"}>{jobStatus.toUpperCase()}</span>
                            </p>
                        </div>
                    </div>

                    <button
                        onClick={onClose}
                        className="p-3 hover:bg-[#2a2a2e] rounded-2xl text-white/50 hover:text-white transition-all border border-white/5 hover:border-white/20"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Toolbar */}
                <div className="flex flex-col md:flex-row gap-4 p-4 bg-[#1c1c20] border-b border-white/10">
                    <div className="relative flex-1">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-primary/50" size={18} />
                        <input
                            type="text"
                            placeholder="Filter by filename or action..."
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="w-full bg-[#111113] border border-white/10 rounded-xl py-3 pl-12 pr-4 text-xs font-bold text-white placeholder:text-white/20 focus:outline-none focus:border-primary/50 transition-all uppercase tracking-widest"
                        />
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 bg-[#111113] border border-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest text-primary">
                        <Clock size={14} />
                        Total: {filteredLogs.length} Entries
                    </div>
                </div>

                {/* Content */}
                <div
                    ref={scrollRef}
                    className="flex-1 overflow-y-auto p-6 space-y-2 font-mono bg-[#0d0d0f]"
                >
                    {loading && logs.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full gap-4 text-white/20">
                            <Terminal className="animate-pulse" size={48} />
                            <p className="text-xs font-black uppercase tracking-[0.3em]">Connecting to log stream...</p>
                        </div>
                    ) : filteredLogs.length === 0 ? (
                        <div className="flex items-center justify-center h-full text-white/20">
                            <p className="text-xs font-black uppercase tracking-[0.3em]">No matching logs found</p>
                        </div>
                    ) : (
                        filteredLogs.map((log, i) => (
                            <div key={i} className="group flex items-start gap-4 p-4 rounded-xl bg-[#141416] hover:bg-[#1a1a1c] transition-all border border-white/5 hover:border-primary/20">
                                <span className="text-[10px] text-white/30 mt-1 flex-shrink-0 font-bold">
                                    {new Date(log.created_at).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                                <div className="flex-shrink-0 mt-1">
                                    {log.success ? (
                                        <CheckCircle2 size={14} className="text-emerald-400 drop-shadow-[0_0_5px_rgba(52,211,153,0.3)]" />
                                    ) : (
                                        <AlertCircle size={14} className="text-red-400 drop-shadow-[0_0_5px_rgba(248,113,113,0.3)]" />
                                    )}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex flex-wrap items-center gap-2 mb-1">
                                        <span className="text-[11px] font-black text-white truncate max-w-sm uppercase tracking-tight">
                                            {log.file_path.split('/').pop() || log.file_path}
                                        </span>
                                        <span className="text-[9px] font-black px-2 py-0.5 rounded bg-primary/20 text-primary uppercase tracking-widest border border-primary/20">
                                            {log.action_taken}
                                        </span>
                                        <span className="text-[9px] font-bold text-white/40">
                                            VIA {log.strategy_used} {log.model_used ? `(${log.model_used})` : ''}
                                        </span>
                                    </div>
                                    <div className="text-[9px] text-white/30 truncate font-bold">
                                        {log.file_path}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Footer Info */}
                <div className="p-4 bg-white/5 border-t border-white/5 flex justify-between items-center">
                    <p className="text-[9px] font-bold text-muted-foreground/40 uppercase tracking-widest">
                        Process Monitor v1.0 • System Secure Log
                    </p>
                    {isJobActive && (
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-primary animate-ping" />
                            <span className="text-[9px] font-black text-primary uppercase tracking-widest">Live Feed Active</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
