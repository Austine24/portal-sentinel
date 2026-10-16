import { Activity, Brain, LayoutDashboard, ShieldAlert } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { DemoBadge } from "./DemoBadge";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/incidents", label: "Incidents", icon: ShieldAlert },
  { to: "/ai", label: "AI Intelligence", icon: Brain },
];

export function Layout() {
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-60 shrink-0 border-r border-white/10 bg-black/20 p-4 backdrop-blur-md md:block">
        <NavLink to="/" className="mb-8 flex items-center gap-2 px-2">
          <Activity className="text-cyan-300" size={22} />
          <span className="text-lg font-semibold tracking-wide text-white">Portal Sentinel</span>
        </NavLink>
        <nav className="space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
                  isActive
                    ? "bg-cyan-400/10 text-cyan-200"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-6 py-3">
          <div className="flex items-center gap-3 text-sm text-slate-300">
            <span className="inline-block h-2 w-2 rounded-full bg-slate-500" />
            Portaldot connection: <span className="text-slate-400">not connected (prototype)</span>
          </div>
          <DemoBadge label="DATA IS DEMO / SIMULATED UNTIL PORTALDOT IS CONNECTED" />
        </header>
        <main className="mx-auto max-w-6xl p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
