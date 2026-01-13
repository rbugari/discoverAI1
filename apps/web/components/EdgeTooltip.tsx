import React from 'react';
import { ShieldCheck, HelpCircle, AlertTriangle } from 'lucide-react';

interface EdgeTooltipProps {
    x: number;
    y: number;
    data: {
        label?: string;
        rationale?: string;
        confidence?: number;
        is_hypothesis?: boolean;
        sourceLabel?: string;
        targetLabel?: string;
    };
    visible: boolean;
}

export function EdgeTooltip({ x, y, data, visible }: EdgeTooltipProps) {
    if (!visible) return null;

    const confidence = data.confidence !== undefined ? data.confidence : 1.0;
    const isHypothesis = data.is_hypothesis;

    // Style based on confidence
    let borderColor = 'border-green-500/30';
    let badgeColor = 'bg-green-500/10 text-green-500';
    let Icon = ShieldCheck;

    if (isHypothesis) {
        borderColor = 'border-orange-500/30';
        badgeColor = 'bg-orange-500/10 text-orange-500';
        Icon = HelpCircle;
    } else if (confidence < 0.8) {
        borderColor = 'border-yellow-500/30';
        badgeColor = 'bg-yellow-500/10 text-yellow-500';
        Icon = AlertTriangle;
    }

    return (
        <div
            className={`fixed z-50 pointer-events-none transition-opacity duration-200 ${visible ? 'opacity-100' : 'opacity-0'}`}
            style={{ left: x, top: y, transform: 'translate(-50%, -100%)', marginTop: '-12px' }}
        >
            <div className={`glass-card p-3 rounded-lg shadow-xl border ${borderColor} min-w-[200px] max-w-[300px]`}>
                {/* Header: Link Type */}
                <div className="flex items-center justify-between mb-2 pb-2 border-b border-white/10">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                        {data.label || 'LINK'}
                    </span>
                    <div className={`flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded-full ${badgeColor}`}>
                        <Icon size={10} />
                        {isHypothesis ? 'HYPOTHESIS' : `${Math.round(confidence * 100)}% CONF.`}
                    </div>
                </div>

                {/* Connection Details */}
                <div className="text-xs text-foreground mb-1">
                    <span className="opacity-50">From: </span> <span className="font-semibold">{data.sourceLabel || '?'}</span>
                </div>
                <div className="text-xs text-foreground mb-2">
                    <span className="opacity-50">To: </span> <span className="font-semibold">{data.targetLabel || '?'}</span>
                </div>

                {/* Rationale / Logic Snippet */}
                {data.rationale ? (
                    <div className="bg-black/20 p-2 rounded text-[10px] font-mono text-blue-200 leading-tight">
                        {data.rationale}
                    </div>
                ) : (
                    <div className="text-[10px] text-muted-foreground italic">
                        {isHypothesis ? 'Inferred from indirect usage.' : 'Direct structural dependency.'}
                    </div>
                )}
            </div>

            {/* Arrow */}
            <div
                className={`absolute left-1/2 bottom-0 w-3 h-3 border-r border-b ${borderColor} bg-card -translate-x-1/2 translate-y-1/2 rotate-45`}
            ></div>
        </div>
    );
}
