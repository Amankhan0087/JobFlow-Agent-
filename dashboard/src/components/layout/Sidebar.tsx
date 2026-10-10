"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";

const NAV = [
  { href: "/dashboard",   icon: "⚡", label: "Dashboard" },
  { href: "/pipeline",    icon: "🗂",  label: "Job Pipeline" },
  { href: "/interviews",  icon: "📅", label: "Interviews" },
  { href: "/resumes",     icon: "📄", label: "Resumes" },
  { href: "/followups",   icon: "📧", label: "Follow-Ups" },
  { href: "/settings",    icon: "⚙️",  label: "Settings" },
];

const FLAGS: Record<string, string> = {
  UAE: "🇦🇪", UK: "🇬🇧", SA: "🇸🇦", Germany: "🇩🇪", USA: "🇺🇸",
};

export default function Sidebar() {
  const path = usePathname();

  return (
    <aside style={{
      width: 220, minHeight: "100vh", background: "#0D1526",
      borderRight: "1px solid #1F2937", display: "flex", flexDirection: "column",
      position: "fixed", top: 0, left: 0, zIndex: 50,
    }}>
      {/* Logo */}
      <div style={{ padding: "20px 20px 16px", borderBottom: "1px solid #1F2937" }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: "#2DD4BF" }}>
          ⚡ JobFlow <span style={{ color: "#6366F1" }}>Agent</span>
        </div>
        <div style={{ fontSize: 11, color: "#4B5563", marginTop: 4 }}>
          {Object.values(FLAGS).join(" ")} 5 Markets
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "12px 0" }}>
        {NAV.map(({ href, icon, label }) => {
          const active = path === href || path.startsWith(href + "/");
          return (
            <Link key={href} href={href} style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "10px 20px", fontSize: 13, fontWeight: 500,
              color: active ? "#2DD4BF" : "#6B7280",
              background: active ? "rgba(45,212,191,0.08)" : "transparent",
              borderLeft: active ? "2px solid #2DD4BF" : "2px solid transparent",
              textDecoration: "none", transition: "all 0.15s",
            }}>
              <span style={{ fontSize: 16 }}>{icon}</span>
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{ padding: 16, borderTop: "1px solid #1F2937" }}>
        <button
          onClick={() => signOut({ callbackUrl: "/login" })}
          style={{
            width: "100%", padding: "8px 12px", borderRadius: 8,
            border: "1px solid #1F2937", background: "transparent",
            color: "#6B7280", fontSize: 12, cursor: "pointer",
          }}
        >
          Sign Out
        </button>
      </div>
    </aside>
  );
}
