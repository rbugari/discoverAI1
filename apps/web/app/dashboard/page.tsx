'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { Plus, Loader2, Trash2, RefreshCw, MoreVertical } from 'lucide-react';
import axios from 'axios';

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
    }
    setLoading(false);
  }

  useEffect(() => {
    fetchSolutions();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this solution?")) return;
    
    setProcessingId(id);
    try {
      // Use local Proxy API Route to avoid CORS
      await axios.delete(`/api/solutions/${id}`);
      setSolutions(prev => prev.filter(s => s.id !== id));
    } catch (error) {
      console.error("Delete failed", error);
      alert("Failed to delete solution");
    } finally {
      setProcessingId(null);
    }
  };

  const handleReanalyze = async (id: string) => {
    setProcessingId(id);
    try {
      await axios.post(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/solutions/${id}/analyze`);
      alert("Analysis restarted. Status will update shortly.");
      fetchSolutions(); // Refresh status
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
        <h1 className="text-3xl font-bold">Solutions</h1>
        <Link 
          href="/solutions/new"
          className="bg-black text-white px-4 py-2 rounded-md flex items-center gap-2 hover:bg-zinc-800 transition-colors"
        >
          <Plus size={16} />
          New Solution
        </Link>
      </div>

      {loading ? (
        <div className="flex justify-center mt-20">
          <Loader2 className="animate-spin" size={48} />
        </div>
      ) : solutions.length === 0 ? (
        <div className="text-center mt-20 text-gray-500">
          <p className="text-xl mb-4">No solutions found.</p>
          <p>Create your first solution to start discovering your data lineage.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {solutions.map((sol) => (
            <div key={sol.id} className="border p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-zinc-900 relative group">
              <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                 <button 
                  onClick={() => handleReanalyze(sol.id)}
                  disabled={!!processingId}
                  className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                  title="Re-analyze"
                >
                  <RefreshCw size={16} className={processingId === sol.id ? 'animate-spin' : ''} />
                </button>
                <button 
                  onClick={() => handleDelete(sol.id)}
                  disabled={!!processingId}
                  className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                  title="Delete"
                >
                  <Trash2 size={16} />
                </button>
              </div>

              <h2 className="text-xl font-semibold mb-2">{sol.name}</h2>
              <div className="flex items-center gap-2 mb-4">
                <span className={`px-2 py-1 rounded-full text-xs font-medium 
                  ${sol.status === 'READY' ? 'bg-green-100 text-green-800' : 
                    sol.status === 'PROCESSING' ? 'bg-blue-100 text-blue-800' : 
                    'bg-gray-100 text-gray-800'}`}>
                  {sol.status}
                </span>
                <span className="text-xs text-gray-500">
                  {new Date(sol.created_at).toLocaleDateString()}
                </span>
              </div>
              <Link 
                href={`/solutions/${sol.id}`}
                prefetch={false}
                className="text-sm text-blue-600 hover:underline inline-flex items-center gap-1"
              >
                View Graph &rarr;
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}