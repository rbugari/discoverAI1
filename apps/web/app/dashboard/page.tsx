'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { Plus, Loader2, Trash2, RefreshCw, Settings, Network, LayoutGrid, FileCode } from 'lucide-react';
import axios from 'axios';
import { ModeToggle } from '@/components/mode-toggle';
import { SolutionCard } from '@/components/SolutionCard';

interface Solution {
  id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

export default function DashboardPage() {
  const [solutions, setSolutions] = useState<Solution[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [menuOpen, setMenuOpen] = useState<string | null>(null);

  const [stats, setStats] = useState<Record<string, any>>({});

  async function fetchSolutions() {
    // Assuming you have an organization, for MVP we fetch all visible
    const { data, error } = await supabase
      .from('solutions')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error fetching solutions:', error);
    } else {
      setSolutions(data || []);
      // Fetch stats for each solution (could be optimized with a view or backend aggregation)
      if (data) {
        data.forEach(sol => fetchStats(sol.id));
      }
    }
    setLoading(false);
  }

  async function fetchStats(solutionId: string) {
    try {
      const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/solutions/${solutionId}/stats`);
      setStats(prev => ({ ...prev, [solutionId]: res.data }));
    } catch (e) {
      console.error(`Failed to fetch stats for ${solutionId}`, e);
    }
  }

  useEffect(() => {
    fetchSolutions();

    // Polling for active jobs to update progress
    const interval = setInterval(() => {
      setSolutions(prev => {
        // Only poll if there are processing solutions or solutions waiting for planning
        const hasProcessing = prev.some(s => s.status === 'PROCESSING' || s.status === 'QUEUED');
        // We should also poll if we are in 'planning_ready' but status might still be PROCESSING in frontend?
        // Actually backend updates solution status to PROCESSING during job.
        // But if job is planning_ready, solution is still PROCESSING.
        // So polling continues.
        if (hasProcessing) {
          // Fetch stats for all solutions again to catch status updates
          prev.forEach(sol => fetchStats(sol.id));
          fetchSolutions();
        }
        return prev;
      });
    }, 5000); // 5 seconds poll

    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this solution?")) return;

    setProcessingId(id);
    try {
      // Direct call to Backend API (bypassing Next.js proxy if it doesn't exist yet, or ensuring it works)
      // Usually better to use the env var for consistency
      const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/solutions/${id}`;
      await axios.delete(apiUrl);

      // Update UI immediately
      setSolutions(prev => prev.filter(s => s.id !== id));
      // Also remove stats to clean up memory
      setStats(prev => {
        const newStats = { ...prev };
        delete newStats[id];
        return newStats;
      });
    } catch (error) {
      console.error("Delete failed", error);
      alert("Failed to delete solution. Please try again.");
    } finally {
      setProcessingId(null);
    }
  };

  const handleReanalyze = async (id: string, mode: 'full' | 'update') => {
    if (mode === 'full') {
      if (!confirm("Are you sure? This will DELETE all existing data for this solution.")) return;
    }

    setProcessingId(id);
    setMenuOpen(null);
    try {
      await axios.post(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/solutions/${id}/analyze`, {
        mode: mode
      });
      alert(`Analysis started in ${mode.toUpperCase()} mode. Status will update shortly.`);
      fetchSolutions();
    } catch (error) {
      console.error("Re-analyze failed", error);
      alert("Failed to restart analysis");
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="p-6 lg:pl-4 lg:pr-12 lg:py-12 min-h-screen relative overflow-hidden bg-background">
      {/* Extreme Premium Background Decorative Elements */}
      {/* v6.0 Human-First Decorative Elements */}
      <div className="absolute -top-32 -left-32 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[160px] pointer-events-none animate-pulse" />
      <div className="absolute top-[20%] -right-32 w-[500px] h-[500px] bg-orange-500/5 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[10%] left-[10%] w-[400px] h-[400px] bg-amber-500/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="relative z-10 mb-16 max-w-[1400px]">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8">
          <div className="space-y-4">
            <span className="text-[10px] font-black uppercase tracking-[0.4em] text-primary block">
              Intelligence Command Center
            </span>
            <h1 className="text-5xl lg:text-6xl font-black tracking-tight leading-[0.9]">
              Your <span className="text-primary italic">Solutions</span>
            </h1>
            <p className="text-base lg:text-lg font-bold text-muted-foreground/60 max-w-2xl leading-relaxed">
              Discover, audit, and optimize your enterprise data lineage with human-centric AI reasoning.
            </p>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 p-2 glass rounded-2xl border-primary/10 bg-white/5">
              <Link href="/admin/model-config" className="p-3 text-muted-foreground hover:text-primary hover:bg-primary/5 rounded-xl transition-all" title="Model Configuration">
                <Settings size={22} />
              </Link>
              <Link href="/admin/prompts" className="p-3 text-muted-foreground hover:text-primary hover:bg-primary/5 rounded-xl transition-all" title="Prompts & Agents">
                <FileCode size={22} />
              </Link>
            </div>
            <div className="h-12 w-[1px] bg-border mx-2" />
            <ModeToggle />
            <Link
              href="/solutions/new"
              className="bg-primary hover:bg-primary/90 text-white px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-widest shadow-[0_20px_40px_-10px_rgba(249,115,22,0.4)] hover:scale-105 transition-transform"
            >
              <div className="flex items-center gap-2">
                <Plus size={20} className="stroke-[3px]" />
                New Discovery
              </div>
            </Link>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center mt-20">
          <Loader2 className="animate-spin text-muted-foreground" size={48} />
        </div>
      ) : solutions.length === 0 ? (
        <div className="text-center mt-20 text-muted-foreground">
          <p className="text-xl mb-4 font-medium">No solutions found.</p>
          <p>Create your first solution to start discovering your data lineage.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {solutions.map((sol) => (
            <SolutionCard
              key={sol.id}
              solution={sol}
              stats={stats[sol.id]}
              onDelete={handleDelete}
              onReanalyze={handleReanalyze}
              processingId={processingId}
            />
          ))}
        </div>
      )}
    </div>
  );
}