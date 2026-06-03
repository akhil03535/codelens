import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Settings() {
  const { user, logout } = useAuth();
  const [copied, setCopied] = useState(false);

  const copyId = () => {
    navigator.clipboard.writeText(user?.id || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-bg">
      <header className="border-b border-bg-border px-6 py-4 flex items-center gap-4">
        <Link to="/dashboard" className="text-text-dim hover:text-text text-sm">← Dashboard</Link>
        <div className="h-4 w-px bg-bg-border" />
        <span className="font-semibold">Settings</span>
      </header>
      <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
        <div className="card p-6 space-y-4">
          <h2 className="font-bold">Profile</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-bg-border">
              <span className="text-text-dim">Email</span><span>{user?.email}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-bg-border">
              <span className="text-text-dim">Username</span><span>@{user?.username}</span>
            </div>
            {user?.full_name && (
              <div className="flex justify-between py-2 border-b border-bg-border">
                <span className="text-text-dim">Full name</span><span>{user.full_name}</span>
              </div>
            )}
            <div className="flex justify-between py-2">
              <span className="text-text-dim">User ID</span>
              <button onClick={copyId} className="font-mono text-xs text-muted hover:text-text">
                {copied ? "Copied!" : user?.id}
              </button>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h2 className="font-bold mb-4">API Configuration</h2>
          <p className="text-sm text-text-dim mb-3">Configure your Groq API key in the backend <code className="text-accent">.env</code> file:</p>
          <pre className="bg-bg-2 border border-bg-border rounded-lg p-4 text-xs font-mono text-accent">
            GROQ_API_KEY=your_groq_api_key_here
          </pre>
          <p className="text-xs text-muted mt-2">
            Get a free key at{" "}
            <a href="https://console.groq.com" target="_blank" rel="noreferrer" className="text-accent hover:underline">
              console.groq.com
            </a>
          </p>
        </div>

        <div className="card p-6">
          <h2 className="font-bold mb-4 text-danger">Danger Zone</h2>
          <button onClick={logout} className="text-sm text-danger border border-danger/30 hover:bg-danger/10 px-4 py-2 rounded-lg transition-colors">
            Sign out of all devices
          </button>
        </div>
      </div>
    </div>
  );
}
