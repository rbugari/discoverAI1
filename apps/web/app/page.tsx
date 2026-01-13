import Link from "next/link";
import { ArrowRight, Sparkles, BrainCircuit, Network, Database } from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 relative overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute inset-0 bg-background z-0"></div>
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-primary/20 rounded-full blur-[120px] animate-pulse z-0" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] bg-indigo-500/10 rounded-full blur-[150px] z-0" />

      <div className="relative z-10 text-center max-w-4xl flex flex-col items-center">

        {/* Badge */}
        <div className="mb-8 inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-primary/20 bg-primary/5 backdrop-blur-md shadow-sm">
          <Sparkles size={14} className="text-primary animate-pulse" />
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-primary">v7.0 Deep Insight</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-6xl md:text-8xl font-black tracking-tighter mb-8 bg-clip-text text-transparent bg-gradient-to-br from-foreground via-foreground to-muted-foreground/50 drop-shadow-sm">
          Nexus <span className="text-primary">Discovery</span>
        </h1>

        {/* Hero Description */}
        <p className="text-xl md:text-2xl text-muted-foreground mb-12 max-w-2xl leading-relaxed font-light">
          Automated Data Lineage & Reverse Engineering for your legacy data pipelines.
          <span className="block mt-2 font-medium text-foreground">Powered by Autonomous Reasoning Agents.</span>
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-5 w-full justify-center mb-16">
          <Link
            href="/dashboard"
            className="group relative px-8 py-4 rounded-xl bg-primary text-primary-foreground font-black text-sm uppercase tracking-widest overflow-hidden shadow-[0_0_40px_rgba(249,115,22,0.3)] hover:shadow-[0_0_60px_rgba(249,115,22,0.5)] transition-all transform hover:scale-105"
          >
            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 backdrop-blur-sm" />
            <div className="relative flex items-center gap-3">
              Initializing Agent <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
          <a
            href="https://github.com/nexus/discovery"
            target="_blank"
            className="px-8 py-4 rounded-xl glass-card text-foreground font-bold text-sm uppercase tracking-widest hover:bg-white/5 transition-all flex items-center gap-3 border border-border/50 group"
          >
            <Database size={18} className="text-muted-foreground group-hover:text-primary transition-colors" />
            Documentation
          </a>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left">
          {[
            { icon: BrainCircuit, title: "Self-Reasoning", desc: "Agents that understand your business logic, not just code." },
            { icon: Network, title: "Visual Lineage", desc: "Interactive graphs connecting tables, scripts, and intent." },
            { icon: Database, title: "Governance Ready", desc: "Auto-sync with Purview, Unity Catalog, and dbt." }
          ].map((feature, idx) => (
            <div key={idx} className="glass-card p-6 rounded-2xl border border-white/5 hover:border-primary/20 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-primary/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-500">
                <feature.icon className="text-primary" size={24} />
              </div>
              <h3 className="font-bold text-lg mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Element */}
      <div className="absolute bottom-8 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/40">
        System Operational • Latency: 12ms
      </div>
    </main>
  );
}