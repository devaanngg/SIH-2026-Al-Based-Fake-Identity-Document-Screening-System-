"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, LayoutDashboard, Search, History, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/screening", label: "New Screening", icon: Search },
  { href: "/history", label: "Screening History", icon: History },
];

export function Sidebar() {
  const pathname = usePathname();
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch("/api/dashboard/stats");
        setApiOnline(res.ok);
      } catch {
        setApiOnline(false);
      }
    };
    check();
  }, []);

  return (
    <aside className="flex h-screen w-56 flex-col border-r bg-slate-900 text-slate-400">
      <div className="flex items-center gap-3 px-5 py-6">
        <ShieldCheck className="h-8 w-8 text-primary" />
        <div>
          <div className="text-lg font-semibold text-white">DocGuard AI</div>
          <div className="text-xs text-slate-500">Document Screening</div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3">
        {navItems.map((item) => {
          const active = item.href === "/"
            ? pathname === "/"
            : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-primary text-white"
                  : "hover:bg-slate-800 hover:text-white"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-800 px-5 py-4">
        <div className="flex items-center gap-2 text-xs">
          {apiOnline === null ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                apiOnline ? "bg-emerald-500" : "bg-red-500"
              )}
            />
          )}
          API: {apiOnline === null ? "checking..." : apiOnline ? "online" : "offline"}
        </div>
      </div>
    </aside>
  );
}
