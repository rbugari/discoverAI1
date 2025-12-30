'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { Plus, Loader2, Trash2, RefreshCw, Settings, Network, LayoutGrid, FileCode } from 'lucide-react';
import axios from 'axios';
import { ModeToggle } from '@/components/mode-toggle';

interface Solution {
  id: string;
  name: string;
  status: string;
  created_at: string;
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
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-4">
            <LayoutGrid className="text-primary" size={32} />
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Your Solutions</h1>
              <p className="text-muted-foreground">Manage and explore your data lineage projects</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 border-r pr-4 mr-2 border-border">
              <Link href="/admin/model-config" className="p-2 text-muted-foreground hover:text-primary hover:bg-secondary rounded-lg transition-all" title="Model Configuration">
                <Settings size={20} />
              </Link>
              <Link href="/admin/prompts" className="p-2 text-muted-foreground hover:text-primary hover:bg-secondary rounded-lg transition-all" title="Prompts & Agents">
                <FileCode size={20} />
              </Link>
            </div>
            <ModeToggle />
            <Link
              href="/solutions/new"
              className="bg-primary text-primary-foreground px-4 py-2 rounded-lg font-semibold hover:bg-primary/90 transition-all flex items-center gap-2"
            >
              <Plus size={18} />
              New Solution
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {solutions.map((sol) => (
            <div key={sol.id} className="border border-border p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow bg-card text-card-foreground relative group">
              <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                <div className="relative">
                  <button
                    onClick={() => setMenuOpen(menuOpen === sol.id ? null : sol.id)}
                    disabled={!!processingId}
                    className="p-1.5 text-muted-foreground hover:text-primary hover:bg-secondary rounded-md transition-colors"
                    title="Re-analyze Options"
                  >
                    <RefreshCw size={16} className={processingId === sol.id ? 'animate-spin' : ''} />
                  </button>

                  {menuOpen === sol.id && (
                    <div className="absolute right-0 mt-2 w-48 bg-card border border-border rounded-md shadow-lg z-20 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                      <button
                        onClick={() => handleReanalyze(sol.id, 'update')}
                        className="w-full text-left px-4 py-2 text-sm hover:bg-muted transition-colors"
                      >
                        Incremental Update
                      </button>
                      <button
                        onClick={() => handleReanalyze(sol.id, 'full')}
                        className="w-full text-left px-4 py-2 text-sm hover:bg-destructive hover:text-destructive-foreground transition-colors border-t border-border"
                      >
                        Full Reprocess (Clean)
                      </button>
                    </div>
                  )}
                </div>

                <button
                  onClick={() => handleDelete(sol.id)}
                  disabled={!!processingId}
                  className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                  title="Delete"
                >
                  <Trash2 size={16} />
                </button>
              </div>

              <h2 className="text-xl font-semibold mb-2 tracking-tight">{sol.name}</h2>
              <div className="flex items-center gap-2 mb-4">
                {stats[sol.id]?.active_job?.status === 'planning_ready' ? (
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium border bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:border-orange-800 animate-pulse">
                    Ready to Approve
                  </span>
                ) : (
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium border
                    ${sol.status === 'READY' ? 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800' :
                      sol.status === 'PROCESSING' ? 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800' :
                        'bg-secondary text-secondary-foreground border-border'}`}>
                    {sol.status}
                  </span>
                )}
                <span className="text-xs text-muted-foreground">
                  {stats[sol.id]?.last_run ?
                    new Date(stats[sol.id].last_run).toLocaleString() :
                    new Date(sol.created_at).toLocaleDateString()}
                </span>
              </div>

              {/* Active Job Progress Section */}
              {/* Force show if there is an active job in planning_ready status OR if solution is processing */}
              {((sol.status === 'PROCESSING' || sol.status === 'QUEUED') || (stats[sol.id]?.active_job?.status === 'planning_ready')) && stats[sol.id]?.active_job && (
                <div className="mb-4 bg-blue-50 dark:bg-blue-900/20 p-3 rounded-md border border-blue-100 dark:border-blue-800">
                  <div className="flex justify-between text-xs font-medium text-blue-700 dark:text-blue-300 mb-1">
                    <span>
                      {stats[sol.id].active_job.status === 'planning_ready' ? 'Evaluating Plan - Action Required' :
                        stats[sol.id].active_job.current_stage === 'planning' ? 'Generating Execution Plan...' :
                          sol.status === 'QUEUED' ? 'Waiting in queue...' : 'Analyzing...'}
                    </span>
                    <span>{stats[sol.id].active_job.progress_pct}%</span>
                  </div>

                  {/* Show Approval Button if Planning Ready */}
                  {stats[sol.id].active_job.status === 'planning_ready' ? (
                    <div className="mt-2">
                      <Link
                        href={`/solutions/${sol.id}/plan`}
                        className="w-full block text-center bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-1.5 rounded transition-colors"
                      >
                        Review Plan
                      </Link>
                    </div>
                  ) : (
                    <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-1.5 mb-2 overflow-hidden">
                      <div
                        className="bg-blue-600 h-1.5 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${stats[sol.id].active_job.progress_pct}%` }}
                      ></div>
                    </div>
                  )}



                  {/* Detailed Stats */}
                  {stats[sol.id].active_job.error_details && stats[sol.id].active_job.error_details.total_files > 0 && (
                    <div className="text-[10px] text-blue-600/80 dark:text-blue-400/80 truncate font-mono">
                      {stats[sol.id].active_job.error_details.processed_files}/{stats[sol.id].active_job.error_details.total_files} files
                      {stats[sol.id].active_job.error_details.current_file && (
                        <span className="block truncate mt-0.5 opacity-75">
                          → {stats[sol.id].active_job.error_details.current_file}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Stats Section (Only show if NOT processing to avoid clutter, or show minimal) */}
              {sol.status === 'READY' && stats[sol.id] && (
                <div className="mb-4 grid grid-cols-3 gap-2 text-center text-sm">
                  <div className="bg-muted/50 p-2 rounded border border-border/50">
                    <div className="font-bold text-foreground">{stats[sol.id].total_assets}</div>
                    <div className="text-xs text-muted-foreground">Assets</div>
                  </div>
                  <div className="bg-muted/50 p-2 rounded border border-border/50">
                    <div className="font-bold text-foreground">{stats[sol.id].total_edges}</div>
                    <div className="text-xs text-muted-foreground">Rels</div>
                  </div>
                  <div className="bg-muted/50 p-2 rounded border border-border/50">
                    <div className="font-bold text-foreground">{stats[sol.id].pipelines || 0}</div>
                    <div className="text-xs text-muted-foreground">Pipelines</div>
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                <Link
                  href={`/solutions/${sol.id}?view=graph`}
                  className="flex-1 bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs font-medium py-2 rounded-md transition-colors flex items-center justify-center gap-1.5"
                >
                  <Network size={14} className="group-hover:rotate-180 transition-transform duration-700" />
                  View Graph
                </Link>
                <Link
                  href={`/solutions/${sol.id}?view=catalog`}
                  className="flex-1 bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs font-medium py-2 rounded-md transition-colors flex items-center justify-center gap-1.5"
                >
                  <LayoutGrid size={14} />
                  View Catalog
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}