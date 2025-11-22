import { useState } from "react";
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
  Menu,
  X,
  Moon,
  Sun,
} from "lucide-react";
import { Logo } from "./Logo";
import { useThemeStore } from "../stores/themeStore";

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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { isDarkMode, toggleDarkMode } = useThemeStore();

  const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);
  const closeMobileMenu = () => setIsMobileMenuOpen(false);

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={toggleMobileMenu}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-background-secondary/80 backdrop-blur-md border border-background-tertiary hover:bg-background-tertiary transition-all shadow-lg"
        aria-label="Toggle menu"
      >
        {isMobileMenuOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <Menu className="w-6 h-6 text-white" />
        )}
      </button>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 backdrop-blur-sm z-40 animate-fade-in"
          onClick={closeMobileMenu}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:sticky top-0 h-screen z-40
          w-64 lg:w-64
          bg-background-secondary/90 dark:bg-background-secondary/95
          backdrop-blur-xl
          border-r border-background-tertiary/50
          flex flex-col
          transition-transform duration-300 ease-in-out
          ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo - clickable home button */}
        <Link
          to="/"
          onClick={closeMobileMenu}
          className="p-6 border-b border-background-tertiary/50 hover:bg-background-tertiary/30 transition-all duration-300 group"
        >
          <div className="flex items-center gap-3">
            <div className="transition-transform duration-300 group-hover:scale-110 group-hover:rotate-6">
              <Logo size="md" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white bg-gradient-to-r from-white to-text-secondary bg-clip-text">
                AutoArr
              </h1>
              <p className="text-xs text-text-muted">v1.0.0</p>
            </div>
          </div>
        </Link>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto scrollbar-thin scrollbar-thumb-background-tertiary scrollbar-track-transparent">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={closeMobileMenu}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group relative overflow-hidden ${
                  isActive
                    ? "bg-gradient-primary text-white shadow-glow scale-105"
                    : "text-text-secondary hover:text-white hover:bg-background-tertiary/50 hover:scale-102"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <div className="absolute inset-0 bg-gradient-to-r from-primary-500/20 to-primary-600/20 animate-shimmer" />
                  )}
                  <item.icon className="w-5 h-5 relative z-10 transition-transform duration-300 group-hover:scale-110" />
                  <span className="font-medium relative z-10">{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Dark Mode Toggle & Status */}
        <div className="p-4 space-y-3 border-t border-background-tertiary/50">
          {/* Dark Mode Toggle */}
          <button
            onClick={toggleDarkMode}
            className="w-full flex items-center justify-between px-4 py-2 rounded-xl bg-background-tertiary/30 hover:bg-background-tertiary/50 transition-all duration-300 group"
            aria-label="Toggle dark mode"
          >
            <span className="text-sm text-text-secondary group-hover:text-white transition-colors">
              {isDarkMode ? 'Dark Mode' : 'Light Mode'}
            </span>
            <div className="relative w-12 h-6 bg-background-elevated rounded-full transition-colors duration-300">
              <div
                className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-gradient-primary shadow-lg transition-transform duration-300 flex items-center justify-center ${
                  isDarkMode ? 'translate-x-6' : 'translate-x-0'
                }`}
              >
                {isDarkMode ? (
                  <Moon className="w-3 h-3 text-white" />
                ) : (
                  <Sun className="w-3 h-3 text-white" />
                )}
              </div>
            </div>
          </button>

          {/* Status */}
          <div className="flex items-center justify-between text-xs text-text-muted px-2">
            <span>Status</span>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-status-success rounded-full animate-pulse shadow-glow" />
              <span className="text-status-success font-medium">Online</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
