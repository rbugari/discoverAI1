import { useState, useEffect } from 'react';

export type PersonaType = 'architect' | 'analyst' | 'operator' | 'general';

export interface PersonaInfo {
    id: PersonaType;
    label: string;
    description: string;
    icon: string;
}

export const PERSONAS: PersonaInfo[] = [
    {
        id: 'architect',
        label: 'Architect',
        description: 'Focus on prompt engineering, model tuning, and structural rules.',
        icon: '📐'
    },
    {
        id: 'analyst',
        label: 'Analyst',
        description: 'Focus on data lineage, insights, and impact analysis.',
        icon: '📊'
    },
    {
        id: 'operator',
        label: 'Operator',
        description: 'Focus on job management, reprocessing, and system health.',
        icon: '⚙️'
    }
];

export function usePersona() {
    const [persona, setPersona] = useState<PersonaType>('general');
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        const saved = localStorage.getItem('discover_ai_persona');
        if (saved) {
            setPersona(saved as PersonaType);
        }
        setIsLoaded(true);
    }, []);

    const changePersona = (newPersona: PersonaType) => {
        setPersona(newPersona);
        localStorage.setItem('discover_ai_persona', newPersona);
    };

    return {
        persona,
        setPersona: changePersona,
        isLoaded,
        personaDetails: PERSONAS.find(p => p.id === persona)
    };
}
