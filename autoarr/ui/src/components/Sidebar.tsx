import { useState } from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
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
  Home,
  ClipboardCheck,
  Palette,
} from 'lucide-react';
import { Logo } from './Logo';
import { useThemeStore } from '../stores/themeStore';

interface NavItem {
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  children?: Omit<NavItem, 'children'>[];
}

const navItems: NavItem[] = [
  { path: '/', icon: Home, label: 'Home' },
  { path: '/chat', icon: MessageCircle, label: 'Chat' },
  { path: '/search', icon: Search, label: 'Search' },
  { path: '/downloads', icon: Download, label: 'Downloads' },
  { path: '/shows', icon: Tv, label: 'TV Shows' },
  { path: '/movies', icon: Film, label: 'Movies' },
  { path: '/media', icon: Server, label: 'Media Server' },
  { path: '/activity', icon: Activity, label: 'Activity' },
  {
    path: '/settings',
    icon: Settings,
    label: 'Settings',
    children: [
      { path: '/settings/appearance', icon: Palette, label: 'Appearance' },
      { path: '/settings/config-audit', icon: ClipboardCheck, label: 'Config Audit' },
    ],
  },
];

// Sidebar Item Component - follows *arr pattern
const SidebarItem = ({
  item,
  isChild = false,
  onCloseMobileMenu,
}: {
  item: NavItem;
  isChild?: boolean;
  onCloseMobileMenu: () => void;
}) => {
  const location = useLocation();

  const isActive = location.pathname === item.path;
  const isParentActive =
    item.children?.some(
      (child) => location.pathname === child.path || location.pathname.startsWith(child.path + '/')
    ) || false;
  const showChildren = isActive || isParentActive;

  return (
    <div>
      <NavLink
        to={item.path}
        onClick={onCloseMobileMenu}
        className={`
          flex items-center
          border-l-[3px] transition-all duration-200 ease-in-out
          ${
            isActive
              ? 'border-l-[var(--accent-color)] text-[var(--accent-color)] bg-[var(--sidebar-accent)]'
              : isParentActive && !isChild
                ? 'border-l-transparent text-foreground bg-[var(--sidebar-accent)]'
                : 'border-l-transparent text-muted-foreground hover:text-[var(--accent-color)] hover:bg-[var(--sidebar-accent)]/50'
          }
        `}
        style={{
          paddingTop: 'var(--sidebar-item-py, 12px)',
          paddingBottom: 'var(--sidebar-item-py, 12px)',
          paddingLeft: isChild ? 'var(--sidebar-child-pl, 40px)' : 'var(--sidebar-item-px, 15px)',
          paddingRight: 'var(--sidebar-item-px, 15px)',
        }}
      >
        <span className="inline-block w-5 mr-2 text-center">
          <item.icon className="w-[18px] h-[18px] inline-block" />
        </span>
        <span className="font-medium">{item.label}</span>
      </NavLink>

      {/* Children - only show when parent is active */}
      {item.children && showChildren && (
        <div>
          {item.children.map((child) => (
            <SidebarItem
              key={child.path}
              item={child}
              isChild={true}
              onCloseMobileMenu={onCloseMobileMenu}
            />
          ))}
        </div>
      )}
    </div>
  );
};

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
        className="lg:hidden fixed top-4 left-4 z-50 p-2.5 rounded-lg bg-card/80 backdrop-blur-md border border-primary/20 hover:bg-muted hover:border-primary/40 transition-all duration-300 shadow-lg hover:shadow-glow-hover"
        aria-label="Toggle menu"
      >
        {isMobileMenuOpen ? (
          <X className="w-6 h-6 text-foreground" />
        ) : (
          <Menu className="w-6 h-6 text-foreground" />
        )}
      </button>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 backdrop-blur-sm z-40 animate-fade-in"
          onClick={closeMobileMenu}
        />
      )}

      {/* Sidebar - following *arr family structure */}
      <aside
        className={`
          fixed lg:sticky top-0 h-screen z-40
          bg-[var(--sidebar-background)]
          flex flex-col
          transition-transform duration-300 ease-in-out
          ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
        style={{
          width: 'var(--sidebar-width, 192px)',
          backgroundColor: 'var(--sidebar-background, hsl(222 47% 11%))',
        }}
      >
        {/* Logo/Brand Header - *arr style */}
        <Link
          to="/"
          onClick={closeMobileMenu}
          className="flex items-center gap-3 px-5 py-4 hover:bg-[var(--sidebar-accent)]/50 transition-colors duration-200"
        >
          <div className="transition-transform duration-200 hover:scale-105">
            <Logo size="md" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">AutoArr</h1>
            <p className="text-xs text-muted-foreground">v1.0.0</p>
          </div>
        </Link>

        {/* Navigation - *arr style */}
        <nav className="flex-1 overflow-y-auto py-2">
          {navItems.map((item) => (
            <SidebarItem key={item.path} item={item} onCloseMobileMenu={closeMobileMenu} />
          ))}
        </nav>

        {/* Footer - Dark Mode Toggle & Status */}
        <div className="border-t border-[var(--sidebar-border)] py-3 px-4 space-y-3">
          {/* Dark Mode Toggle */}
          <button
            onClick={toggleDarkMode}
            className="w-full flex items-center justify-between px-3 py-2.5 rounded-md bg-[var(--sidebar-accent)]/30 hover:bg-[var(--sidebar-accent)]/50 transition-colors duration-200"
            aria-label="Toggle dark mode"
          >
            <span className="text-sm text-muted-foreground">
              {isDarkMode ? 'Dark Mode' : 'Light Mode'}
            </span>
            <div className="relative w-10 h-5 bg-muted rounded-full transition-colors duration-200">
              <div
                className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-[var(--accent-color)] shadow-sm transition-transform duration-200 flex items-center justify-center ${
                  isDarkMode ? 'translate-x-5' : 'translate-x-0'
                }`}
              >
                {isDarkMode ? (
                  <Moon className="w-2.5 h-2.5 text-white" />
                ) : (
                  <Sun className="w-2.5 h-2.5 text-white" />
                )}
              </div>
            </div>
          </button>

          {/* Status */}
          <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
            <span>Status</span>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span className="text-green-500 font-medium">Online</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
