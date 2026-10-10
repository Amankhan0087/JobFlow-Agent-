"use client";
import { signIn } from "next-auth/react";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    const result = await signIn("credentials", {
      email, password, redirect: false,
    });
    setLoading(false);
    if (result?.ok) {
      router.push("/dashboard");
    } else {
      setError("Invalid email or password");
    }
  };

  const S = {
    page: { minHeight: "100vh", background: "#0A0F1E", display: "flex", alignItems: "center", justifyContent: "center" } as React.CSSProperties,
    card: { width: 400, background: "#111827", border: "1px solid #1F2937", borderRadius: 16, padding: 40 } as React.CSSProperties,
    logo: { fontSize: 22, fontWeight: 700, color: "#2DD4BF", textAlign: "center" as const, marginBottom: 8 },
    sub: { fontSize: 13, color: "#6B7280", textAlign: "center" as const, marginBottom: 32 },
    label: { fontSize: 12, fontWeight: 500, color: "#9CA3AF", display: "block", marginBottom: 6 },
    input: { width: "100%", padding: "10px 14px", background: "#1A2234", border: "1px solid #1F2937", borderRadius: 8, color: "#F9FAFB", fontSize: 13, outline: "none", marginBottom: 16, boxSizing: "border-box" as const },
    btn: { width: "100%", padding: "12px", background: "#2DD4BF", color: "#0A0F1E", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: "pointer" },
    err: { fontSize: 12, color: "#EF4444", textAlign: "center" as const, marginBottom: 16 },
    divider: { textAlign: "center" as const, color: "#4B5563", fontSize: 12, margin: "20px 0", position: "relative" as const },
    googleBtn: { width: "100%", padding: "10px", background: "transparent", color: "#9CA3AF", border: "1px solid #1F2937", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer", marginTop: 4 },
  };

  return (
    <div style={S.page}>
      <div style={S.card}>
        <div style={S.logo}>⚡ JobFlow Agent</div>
        <div style={S.sub}>AI-powered job applications across 5 markets</div>

        <form onSubmit={handleLogin}>
          <label style={S.label}>Email</label>
          <input style={S.input} type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required />
          <label style={S.label}>Password</label>
          <input style={S.input} type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required />
          {error && <div style={S.err}>{error}</div>}
          <button style={S.btn} type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div style={S.divider}>or</div>

        <button style={S.googleBtn} onClick={() => signIn("google", { callbackUrl: "/dashboard" })}>
          🔗 Continue with Google
        </button>

        <div style={{ marginTop: 24, padding: 14, background: "#0D1526", borderRadius: 8, fontSize: 11, color: "#4B5563" }}>
          Default: <code style={{ color: "#6366F1" }}>admin@jobflow.ai</code> / <code style={{ color: "#6366F1" }}>jobflow2024</code>
        </div>
      </div>
    </div>
  );
}
