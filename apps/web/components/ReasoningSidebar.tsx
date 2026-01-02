'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    LayoutDashboard,
    PlusCircle,
    Settings,
    Cpu,
    ChevronRight,
    ChevronLeft,
    BrainCircuit,
    Zap,
    MessageSquareText,
    Activity
} from 'lucide-react';

export const ReasoningSidebar = () => {
    const [collapsed, setCollapsed] = useState(false);
    const pathname = usePathname();

    const menuItems = [
        { icon: <LayoutDashboard size={20} />, label: 'Dashboard', href: '/dashboard' },
        { icon: <PlusCircle size={20} />, label: 'New Discovery', href: '/solutions/new' },
        { icon: <MessageSquareText size={20} />, label: 'Reasoning Logs', href: '#' },
        { icon: <Activity size={20} />, label: 'System Health', href: '/admin/model-config' },
        { icon: <Settings size={20} />, label: 'Admin Settings', href: '/admin/prompts' },
    ];

    const toggleSidebar = () => {
        const newState = !collapsed;
        setCollapsed(newState);
        // Sync with global layout
        document.documentElement.style.setProperty('--sidebar-width', newState ? '5rem' : '18rem');
    };

    React.useEffect(() => {
        // Ensure initial sync
        document.documentElement.style.setProperty('--sidebar-width', collapsed ? '5rem' : '18rem');
    }, []);

    return (
        <aside className={`fixed left-0 top-0 h-screen bg-background border-r border-primary/5 z-[9999] transition-all duration-500 ease-in-out flex flex-col ${collapsed ? 'w-20' : 'w-72'}`}>
            {/* Human Agent Header */}
            <div className={`p-6 flex items-center justify-between transition-all duration-500 ${collapsed ? 'px-4' : 'px-6'}`}>
                <div className={`flex items-center gap-3 transition-all duration-300 ${collapsed ? 'opacity-0 scale-50 pointer-events-none' : 'opacity-100 scale-100'}`}>
                    <div className="relative">
                        <div className="w-10 h-10 rounded-2xl bg-primary flex items-center justify-center shadow-[0_0_20px_rgba(249,115,22,0.4)] animate-pulse">
                            <BrainCircuit className="text-white" size={24} />
                        </div>
                        <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-background" title="Agent Online" />
                    </div>
                    {!collapsed && (
                        <div className="flex flex-col">
                            <span className="text-sm font-black tracking-tight text-foreground uppercase">DiscoverAI <span className="text-primary italic">v6.0</span></span>
                            <span className="text-[10px] font-bold text-muted-foreground/60 uppercase tracking-widest">Sentient Assistant</span>
                        </div>
                    )}
                </div>
                <button
                    onClick={toggleSidebar}
                    className={`p-2 hover:bg-primary/5 rounded-xl text-muted-foreground hover:text-primary transition-all ${collapsed ? 'mx-auto' : ''}`}
                >
                    {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                </button>
            </div>

            {/* Main Navigation */}
            <nav className="flex-1 px-4 mt-8 space-y-2">
                {menuItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.label}
                            href={item.href}
                            className={`flex items-center gap-4 px-4 py-3.5 rounded-2xl transition-all group relative ${isActive
                                ? 'bg-primary text-white shadow-[0_10px_20px_rgba(249,115,22,0.2)]'
                                : 'text-muted-foreground/60 hover:bg-primary/5 hover:text-primary'
                                }`}
                        >
                            <div className={`transition-transform duration-300 group-hover:scale-110 ${isActive ? 'rotate-6' : ''}`}>
                                {item.icon}
                            </div>
                            {!collapsed && (
                                <span className={`text-[11px] font-black uppercase tracking-widest transition-opacity duration-300 ${collapsed ? 'opacity-0' : 'opacity-100'}`}>
                                    {item.label}
                                </span>
                            )}
                            {isActive && !collapsed && (
                                <div className="ml-auto">
                                    <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                                </div>
                            )}
                            {collapsed && (
                                <div className="absolute left-full ml-4 px-3 py-2 bg-zinc-900 text-white text-[10px] font-black uppercase tracking-widest rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50 shadow-2xl">
                                    {item.label}
                                </div>
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Agent "Thinking" Presence Indicator */}
            <div className={`mt-auto p-6 transition-all duration-500 ${collapsed ? 'opacity-0 translate-y-4' : 'opacity-100 translate-y-0'}`}>
                {!collapsed && (
                    <div className="p-5 rounded-[2rem] glass-card border-primary/10 bg-primary/5 overflow-hidden relative">
                        <div className="relative z-10">
                            <div className="flex items-center gap-2 mb-3">
                                <Zap size={12} className="text-primary animate-pulse" />
                                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Live Monitor</span>
                            </div>
                            <p className="text-[10px] font-bold text-muted-foreground leading-relaxed italic">
                                "Synthesizing metadata clusters across 4 enterprise solutions..."
                            </p>
                        </div>
                        {/* Decorative background element for the card */}
                        <div className="absolute top-[-20%] right-[-10%] w-20 h-20 bg-primary/10 rounded-full blur-2xl pointer-events-none" />
                    </div>
                )}
            </div>

            {/* Footer / User Profile Placeholder */}
            {!collapsed && (
                <div className="p-6 border-t border-primary/5">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center font-black text-xs text-primary">
                            JD
                        </div>
                        <div className="flex flex-col">
                            <span className="text-xs font-black text-foreground">John Doe</span>
                            <span className="text-[9px] font-bold text-muted-foreground/60 uppercase">System Architect</span>
                        </div>
                    </div>
                </div>
            )}
        </aside>
    );
};
