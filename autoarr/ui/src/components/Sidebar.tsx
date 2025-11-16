import { NavLink, Link } from "react-router-dom";
import {
  Download,
  Tv,
  Film,
  Server,
  Settings,
  Activity,
  Search,
  MessageCircle,
} from "lucide-react";
import { Logo } from "./Logo";

const navItems = [
  { path: "/chat", icon: MessageCircle, label: "Chat" },
  { path: "/search", icon: Search, label: "Search" },
  { path: "/downloads", icon: Download, label: "Downloads" },
  { path: "/shows", icon: Tv, label: "TV Shows" },
  { path: "/movies", icon: Film, label: "Movies" },
  { path: "/media", icon: Server, label: "Media Server" },
  { path: "/activity", icon: Activity, label: "Activity" },
  { path: "/settings", icon: Settings, label: "Settings" },
];

export const Sidebar = () => {
  return (
    <aside className="w-64 bg-background-secondary border-r border-background-tertiary flex flex-col h-screen">
      {/* Logo - clickable home button */}
      <Link
        to="/"
        className="p-6 border-b border-background-tertiary hover:bg-background-tertiary transition-colors group"
      >
        <div className="flex items-center gap-3">
          <div className="transition-transform group-hover:scale-110">
            <Logo size="md" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">AutoArr</h1>
            <p className="text-xs text-text-muted">v1.0.0</p>
          </div>
        </div>
      </Link>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? "bg-gradient-primary text-white shadow-glow"
                  : "text-text-secondary hover:text-white hover:bg-background-tertiary"
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-background-tertiary">
        <div className="flex items-center justify-between text-xs text-text-muted">
          <span>Status</span>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-status-success rounded-full animate-pulse" />
            <span className="text-status-success">Online</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
