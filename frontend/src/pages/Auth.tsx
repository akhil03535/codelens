import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { extractError } from "../services/api";

function AuthCard({ children, title, sub }: { children: React.ReactNode; title: string; sub: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Link to="/" className="text-2xl font-bold inline-flex items-center gap-2">
            <span>🔭</span> CodeLens AI
          </Link>
          <p className="text-text-dim text-sm mt-2">{sub}</p>
        </div>
        <div className="card p-8">{children}</div>
      </div>
    </div>
  );
}

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(extractError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthCard title="Sign in" sub="Sign in to your CodeLens AI account">
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="text-sm text-text-dim block mb-1">Email</label>
          <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)}
            placeholder="you@example.com" required />
        </div>
        <div>
          <label className="text-sm text-text-dim block mb-1">Password</label>
          <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)}
            placeholder="••••••••" required />
        </div>
        {error && <p className="text-danger text-sm bg-danger/10 px-3 py-2 rounded-lg">{error}</p>}
        <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="text-center text-sm text-text-dim mt-4">
        No account?{" "}
        <Link to="/signup" className="text-accent hover:underline">Create one free</Link>
      </p>
    </AuthCard>
  );
}

export function Signup() {
  const [form, setForm] = useState({ email: "", username: "", password: "", full_name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      await signup(form.email, form.username, form.password, form.full_name || undefined);
      navigate("/dashboard");
    } catch (err) {
      setError(extractError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthCard title="Create account" sub="Start understanding codebases with AI">
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="text-sm text-text-dim block mb-1">Full name (optional)</label>
          <input className="input" value={form.full_name} onChange={set("full_name")} placeholder="Ada Lovelace" />
        </div>
        <div>
          <label className="text-sm text-text-dim block mb-1">Email</label>
          <input className="input" type="email" value={form.email} onChange={set("email")}
            placeholder="you@example.com" required />
        </div>
        <div>
          <label className="text-sm text-text-dim block mb-1">Username</label>
          <input className="input" value={form.username} onChange={set("username")}
            placeholder="ada_dev" required minLength={3} />
        </div>
        <div>
          <label className="text-sm text-text-dim block mb-1">Password</label>
          <input className="input" type="password" value={form.password} onChange={set("password")}
            placeholder="Min 8 characters" required minLength={8} />
        </div>
        {error && <p className="text-danger text-sm bg-danger/10 px-3 py-2 rounded-lg">{error}</p>}
        <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>
      <p className="text-center text-sm text-text-dim mt-4">
        Already have an account?{" "}
        <Link to="/login" className="text-accent hover:underline">Sign in</Link>
      </p>
    </AuthCard>
  );
}
