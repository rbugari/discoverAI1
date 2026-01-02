'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { Upload, Loader2, ArrowLeft, Github, Folder } from 'lucide-react';
import Link from 'next/link';
import axios from 'axios';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { ModeToggle } from '@/components/mode-toggle';

export function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

type SourceType = 'ZIP' | 'GITHUB';

export default function NewSolutionPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [sourceType, setSourceType] = useState<SourceType>('ZIP');

  // ZIP State
  const [file, setFile] = useState<File | null>(null);

  // GitHub State
  const [repoUrl, setRepoUrl] = useState('');

  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'IDLE' | 'UPLOADING' | 'STARTING' | 'DONE'>('IDLE');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) return;
    if (sourceType === 'ZIP' && !file) return;
    if (sourceType === 'GITHUB' && !repoUrl) return;

    try {
      setLoading(true);
      setStep('UPLOADING');

      // 0. Get Org ID (Hardcoded for MVP)
      let orgId = '';
      const { data: orgs } = await supabase.from('organizations').select('id').limit(1);
      if (orgs && orgs.length > 0) {
        orgId = orgs[0].id;
      } else {
        const { data: newOrg, error: orgError } = await supabase
          .from('organizations')
          .insert({ name: 'My Organization' })
          .select()
          .single();
        if (orgError) throw orgError;
        orgId = newOrg.id;
      }

      let finalPath = '';

      if (sourceType === 'ZIP' && file) {
        // 1. Upload File
        finalPath = `uploads/${orgId}/${Date.now()}_${file.name}`;
        const { error: uploadError } = await supabase.storage
          .from('source-code')
          .upload(finalPath, file);

        if (uploadError) throw new Error(`Upload failed: ${uploadError.message}`);
      } else {
        // GitHub URL
        finalPath = repoUrl;
      }

      // 2. Create Solution Record
      const { data: solution, error: dbError } = await supabase
        .from('solutions')
        .insert({
          name,
          org_id: orgId,
          storage_path: finalPath,
          status: 'QUEUED',
          config: { source_type: sourceType } // Optional metadata
        })
        .select()
        .single();

      if (dbError) throw dbError;

      // 3. Trigger Backend Job
      setStep('STARTING');
      await axios.post(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/jobs`, {
        solution_id: solution.id,
        file_path: finalPath
      });

      setStep('DONE');
      router.push('/dashboard');

    } catch (error: any) {
      console.error(error);
      alert('Error creating solution: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <div className="flex justify-between items-start mb-6">
        <Link href="/dashboard" className="flex items-center text-sm text-gray-500 hover:text-gray-900 dark:hover:text-gray-100">
          <ArrowLeft size={16} className="mr-1" /> Back to Dashboard
        </Link>
        <ModeToggle />
      </div>

      <h1 className="text-3xl font-bold mb-2">New Discovery</h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8 font-medium">Connect your data sources to start the autonomous reasoning phase.</p>

      <form onSubmit={handleSubmit} className="space-y-6 border p-8 rounded-[2rem] bg-card shadow-sm dark:bg-zinc-900/50 dark:border-zinc-800 backdrop-blur-xl">
        <div>
          <label className="block text-sm font-black uppercase tracking-widest mb-2 text-muted-foreground">Solution Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full border rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-primary dark:bg-zinc-800 dark:border-zinc-700 transition-all font-bold"
            placeholder="e.g. Sales Data Migration"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-black uppercase tracking-widest mb-4 text-muted-foreground">Source Type</label>
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => setSourceType('ZIP')}
              className={cn(
                "flex-1 p-6 border rounded-2xl flex flex-col items-center gap-2 transition-all",
                sourceType === 'ZIP'
                  ? "border-primary bg-primary/5 text-primary"
                  : "border-gray-200 hover:bg-gray-50 dark:border-zinc-700 dark:hover:bg-zinc-800 text-muted-foreground"
              )}
            >
              <Folder size={28} />
              <span className="font-black text-xs uppercase tracking-widest">Upload ZIP</span>
            </button>
            <button
              type="button"
              onClick={() => setSourceType('GITHUB')}
              className={cn(
                "flex-1 p-6 border rounded-2xl flex flex-col items-center gap-2 transition-all",
                sourceType === 'GITHUB'
                  ? "border-primary bg-primary/5 text-primary"
                  : "border-gray-200 hover:bg-gray-50 dark:border-zinc-700 dark:hover:bg-zinc-800 text-muted-foreground"
              )}
            >
              <Github size={28} />
              <span className="font-black text-xs uppercase tracking-widest">GitHub Repo</span>
            </button>
          </div>
        </div>

        {sourceType === 'ZIP' ? (
          <div>
            <label className="block text-sm font-black uppercase tracking-widest mb-2 text-muted-foreground">Source Code (ZIP)</label>
            <div className="border-2 border-dashed border-border rounded-2xl p-10 text-center cursor-pointer hover:bg-primary/5 hover:border-primary/50 transition-all relative group">
              <input
                type="file"
                accept=".zip"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                required={sourceType === 'ZIP'}
              />
              <div className="flex flex-col items-center pointer-events-none">
                <Upload className="text-muted-foreground/40 group-hover:text-primary transition-colors mb-4" size={40} />
                <p className="text-sm font-bold text-foreground">
                  {file ? file.name : "Click to upload or drag and drop"}
                </p>
                <p className="text-xs text-muted-foreground mt-2 font-medium">ZIP files only</p>
              </div>
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-sm font-black uppercase tracking-widest mb-2 text-muted-foreground">Repository URL</label>
            <input
              type="url"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="w-full border rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-primary dark:bg-zinc-800 dark:border-zinc-700 font-bold"
              placeholder="https://github.com/username/repo"
              required={sourceType === 'GITHUB'}
            />
            <p className="text-xs text-muted-foreground mt-2 font-medium uppercase tracking-tighter">Public repositories only.</p>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-primary text-white py-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] shadow-lg shadow-primary/20 hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center transition-all hover:scale-[1.01]"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin mr-3" size={20} />
              {step === 'UPLOADING' ? 'PREPARING ARTIFACTS...' : 'AWAKENING AGENTS...'}
            </>
          ) : (
            'START DISCOVERY'
          )}
        </button>
      </form>
    </div>
  );
}