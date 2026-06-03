import { Link } from "react-router-dom";

const features = [
  { icon: "🔍", title: "Semantic Code Search", desc: "Find any logic, pattern, or concept across the entire codebase using natural language." },
  { icon: "🏗️", title: "Architecture Analysis", desc: "Automatically detect MVC, layered, microservices, and other architectural patterns." },
  { icon: "🔀", title: "Flow Tracing", desc: "Ask 'how does login work?' and get a step-by-step trace through real files." },
  { icon: "🐛", title: "Bug Investigation", desc: "Paste a stack trace and get root cause analysis with suggested fixes." },
  { icon: "📄", title: "Doc Generation", desc: "Generate README, API docs, and onboarding guides automatically from source code." },
  { icon: "🕸️", title: "Dependency Graph", desc: "Visualize import relationships and service dependencies as an interactive graph." },
];

const stats = [
  { value: "10+", label: "AI Features" },
  { value: "6", label: "Languages" },
  { value: "100%", label: "Context-Grounded" },
  { value: "RAG", label: "Powered" },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-bg text-text">
      {/* Nav */}
      <nav className="border-b border-bg-border px-6 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🔭</span>
          <span className="font-bold text-lg">CodeLens AI</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="btn-ghost text-sm">Sign in</Link>
          <Link to="/signup" className="btn-primary text-sm">Get Started Free</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 pt-24 pb-16 text-center">
        <div className="inline-flex items-center gap-2 bg-bg-2 border border-bg-border rounded-full px-4 py-1.5 text-sm text-text-dim mb-8">
          <span className="w-2 h-2 rounded-full bg-success inline-block" />
          Powered by Groq · llama3-70b · ChromaDB
        </div>
        <h1 className="text-5xl font-bold leading-tight mb-6">
          Understand Any Codebase<br />
          <span className="text-accent">Instantly with AI</span>
        </h1>
        <p className="text-xl text-text-dim max-w-2xl mx-auto mb-10">
          Upload a GitHub repository or ZIP file. Ask questions, trace flows, investigate bugs,
          and generate documentation — all grounded in your actual code.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link to="/signup" className="btn-primary text-base px-6 py-3">
            Start for Free →
          </Link>
          <Link to="/login" className="text-text-dim hover:text-text text-sm underline underline-offset-4">
            Sign in to existing account
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-6 mt-16 max-w-2xl mx-auto">
          {stats.map(s => (
            <div key={s.label} className="text-center">
              <div className="text-2xl font-bold text-accent">{s.value}</div>
              <div className="text-xs text-muted mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">Everything you need to understand code</h2>
        <div className="grid grid-cols-3 gap-6">
          {features.map(f => (
            <div key={f.title} className="card p-6 hover:border-accent/40 transition-colors">
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-base mb-2">{f.title}</h3>
              <p className="text-sm text-text-dim leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-4xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">How it works</h2>
        <div className="flex items-start gap-4">
          {[
            { n: "1", title: "Upload Repository", desc: "Paste a GitHub URL or upload a ZIP file" },
            { n: "2", title: "AI Processes Code", desc: "Parses, chunks, and embeds your entire codebase" },
            { n: "3", title: "Ask Anything", desc: "Chat, trace flows, analyze architecture, debug bugs" },
          ].map((step, i) => (
            <div key={step.n} className="flex-1 text-center">
              <div className="w-10 h-10 rounded-full bg-accent-dim flex items-center justify-center text-white font-bold mx-auto mb-3">
                {step.n}
              </div>
              <h3 className="font-semibold mb-1">{step.title}</h3>
              <p className="text-sm text-text-dim">{step.desc}</p>
              {i < 2 && <div className="hidden md:block absolute" />}
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-4xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold text-center mb-4">Simple pricing</h2>
        <p className="text-center text-text-dim mb-12">Self-hosted, bring your own Groq API key (free tier available)</p>
        <div className="grid grid-cols-2 gap-6 max-w-2xl mx-auto">
          <div className="card p-8">
            <div className="text-lg font-bold mb-1">Open Source</div>
            <div className="text-4xl font-bold mb-4">$0</div>
            <ul className="space-y-2 text-sm text-text-dim mb-6">
              <li>✓ Unlimited repositories</li>
              <li>✓ All AI features</li>
              <li>✓ Self-hosted</li>
              <li>✓ Your own API key</li>
            </ul>
            <Link to="/signup" className="btn-primary block text-center text-sm py-2">Get Started</Link>
          </div>
          <div className="card p-8 border-accent/40 relative">
            <div className="absolute -top-3 left-6 badge bg-accent text-white">Popular</div>
            <div className="text-lg font-bold mb-1">Groq Free Tier</div>
            <div className="text-4xl font-bold mb-4">Free</div>
            <ul className="space-y-2 text-sm text-text-dim mb-6">
              <li>✓ Free Groq API key</li>
              <li>✓ llama3-70b-8192</li>
              <li>✓ Generous rate limits</li>
              <li>✓ Production quality</li>
            </ul>
            <a href="https://console.groq.com" target="_blank" rel="noreferrer"
              className="btn-ghost block text-center text-sm py-2 border border-bg-border rounded-lg">
              Get Free API Key →
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-bg-border py-8 text-center text-sm text-muted">
        <p>CodeLens AI · FastAPI · ChromaDB · SentenceTransformers · Groq · React</p>
      </footer>
    </div>
  );
}
