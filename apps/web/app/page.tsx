import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-zinc-50 dark:bg-zinc-950">
      <div className="text-center max-w-3xl">
        <h1 className="text-6xl font-bold tracking-tight mb-6">
          Nexus <span className="text-blue-600">Discovery</span>
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 mb-10">
          Automated Data Lineage & Reverse Engineering for your legacy data pipelines.
          Powered by AI.
        </p>
        
        <div className="flex gap-4 justify-center">
          <Link 
            href="/dashboard"
            className="bg-black text-white px-8 py-3 rounded-lg font-medium flex items-center gap-2 hover:bg-zinc-800 transition-all"
          >
            Get Started <ArrowRight size={18} />
          </Link>
          <a 
            href="https://github.com/nexus/discovery"
            target="_blank"
            className="bg-white border border-gray-300 text-gray-900 px-8 py-3 rounded-lg font-medium hover:bg-gray-50 transition-all"
          >
            Documentation
          </a>
        </div>
      </div>
    </main>
  );
}