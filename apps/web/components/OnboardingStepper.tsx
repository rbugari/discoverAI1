'use client';

import React, { useState, useEffect } from 'react';
import { X, ChevronRight, ChevronLeft, Sparkles, Brain, Database, Users, ShieldCheck } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { PERSONAS, PersonaType, usePersona } from '../hooks/usePersona';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface Step {
    title: string;
    description: string;
    icon: React.ReactNode;
}

const STEPS: Step[] = [
    {
        title: "Welcome to DiscoverAI v6.0",
        description: "We've rebuilt the interface with a 'Human-First' aesthetic. Organic tones and a cleaner layout help you focus on what matters: the data.",
        icon: <Sparkles className="text-orange-500" size={32} />
    },
    {
        title: "Meet the Reasoning Brain",
        description: "The new persistent sidebar houses our Reasoning Agent. It's no longer just an extractor; it's a senior architect that thinks before it speaks.",
        icon: <Brain className="text-orange-500" size={32} />
    },
    {
        title: "The Enterprise Hub",
        description: "Manage the full lifecycle of your solutions. Every discovery run now generates professional PDF and Markdown artifacts in its private sandbox.",
        icon: <Database className="text-orange-500" size={32} />
    },
    {
        title: "Pick Your Persona",
        description: "Tell us who you are so we can tailor the guidance and system insights to your specific needs.",
        icon: <Users className="text-orange-500" size={32} />
    }
];

export default function OnboardingStepper() {
    const [isOpen, setIsOpen] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const { setPersona } = usePersona();

    useEffect(() => {
        const hasSeenOnboarding = localStorage.getItem('discover_ai_onboarding_v6');
        if (!hasSeenOnboarding) {
            // Delay slightly for better UX
            const timer = setTimeout(() => setIsOpen(true), 1500);
            return () => clearTimeout(timer);
        }
    }, []);

    const handleClose = () => {
        setIsOpen(false);
        localStorage.setItem('discover_ai_onboarding_v6', 'true');
    };

    const handleNext = () => {
        if (currentStep < STEPS.length - 1) {
            setCurrentStep(currentStep + 1);
        } else {
            handleClose();
        }
    };

    const handleBack = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1);
        }
    };

    const selectPersona = (p: PersonaType) => {
        setPersona(p);
        handleNext();
    };

    if (!isOpen) return null;

    const step = STEPS[currentStep];

    return (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-background/60 backdrop-blur-md transition-opacity" />

            {/* Modal */}
            <div className="relative w-full max-w-xl bg-card border border-border shadow-2xl rounded-3xl overflow-hidden flex flex-col animate-in fade-in zoom-in duration-300">
                {/* Visual Header */}
                <div className="h-40 bg-gradient-to-br from-orange-500/10 via-amber-500/5 to-transparent flex items-center justify-center relative overflow-hidden">
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-orange-500/10 blur-3xl rounded-full" />
                    <div className="relative z-10 bg-card/80 backdrop-blur-sm p-5 rounded-2xl border border-orange-500/20 shadow-xl">
                        {step.icon}
                    </div>
                    <button
                        onClick={handleClose}
                        className="absolute top-6 right-6 p-2 hover:bg-muted rounded-full transition-colors text-muted-foreground"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Body */}
                <div className="p-10 flex flex-col items-center text-center">
                    <h2 className="text-3xl font-bold mb-4 tracking-tight">{step.title}</h2>
                    <p className="text-muted-foreground leading-relaxed max-w-md mx-auto">
                        {step.description}
                    </p>

                    {/* Step Specific: Persona Selection */}
                    {currentStep === STEPS.length - 1 && (
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8 w-full">
                            {PERSONAS.map((p) => (
                                <button
                                    key={p.id}
                                    onClick={() => selectPersona(p.id)}
                                    className="p-5 rounded-2xl border border-border bg-muted/30 hover:bg-orange-500/5 hover:border-orange-500/30 transition-all text-center group"
                                >
                                    <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">{p.icon}</div>
                                    <div className="font-bold text-sm mb-1">{p.label}</div>
                                    <div className="text-[10px] text-muted-foreground line-clamp-2">{p.description}</div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-8 bg-muted/30 border-t flex items-center justify-between">
                    <div className="flex gap-1.5">
                        {STEPS.map((_, i) => (
                            <div
                                key={i}
                                className={cn(
                                    "h-1.5 rounded-full transition-all",
                                    i === currentStep ? "w-8 bg-orange-500" : "w-1.5 bg-border"
                                )}
                            />
                        ))}
                    </div>

                    <div className="flex gap-3">
                        {currentStep > 0 && currentStep < STEPS.length - 1 && (
                            <button
                                onClick={handleBack}
                                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold hover:bg-muted rounded-xl transition-colors"
                            >
                                <ChevronLeft size={18} />
                                Back
                            </button>
                        )}
                        {currentStep < STEPS.length - 1 ? (
                            <button
                                onClick={handleNext}
                                className="flex items-center gap-2 px-6 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-orange-500/20 transition-all active:scale-95"
                            >
                                Next
                                <ChevronRight size={18} />
                            </button>
                        ) : (
                            <button
                                onClick={handleClose}
                                className="px-6 py-2 bg-zinc-900 dark:bg-zinc-100 dark:text-zinc-900 text-white rounded-xl text-sm font-bold transition-all active:scale-95"
                            >
                                Skip & Explore
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
