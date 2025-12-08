import { useState, useEffect } from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
import {
  Download,
  Tv,
  Film,
  Server,
  Settings,
  Activity,
  Search,
  Home,
  ClipboardCheck,
  Palette,
  Menu,
  X,
  Gauge,
} from 'lucide-react';

interface ServiceStatus {
  key: string;
  name: string;
  connected: boolean;
}

interface NavItem {
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  children?: Omit<NavItem, 'children'>[];
}

// Base nav items that are always visible
const baseNavItems: NavItem[] = [
  { path: '/', icon: Home, label: 'Home' },
  { path: '/search', icon: Search, label: 'Search' },
];

// Service-specific nav items - only shown when the service is connected
const serviceNavItems: Record<string, NavItem> = {
  sabnzbd: { path: '/downloads', icon: Download, label: 'Downloads' },
  sonarr: { path: '/shows', icon: Tv, label: 'TV Shows' },
  radarr: { path: '/movies', icon: Film, label: 'Movies' },
  plex: { path: '/media', icon: Server, label: 'Media Server' },
};

// Always visible nav items at the end
const footerNavItems: NavItem[] = [
  { path: '/optimize', icon: Gauge, label: 'Optimize' },
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
  onNavigate,
}: {
  item: NavItem;
  isChild?: boolean;
  onNavigate?: () => void;
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
        onClick={onNavigate}
        className={`
          flex items-center
          border-l-[3px] transition-colors duration-200
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
            <SidebarItem key={child.path} item={child} isChild={true} onNavigate={onNavigate} />
          ))}
        </div>
      )}
    </div>
  );
};

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  isMobile?: boolean;
}

export const Sidebar = ({ isOpen = true, onClose, isMobile = false }: SidebarProps) => {
  const [services, setServices] = useState<ServiceStatus[]>([
    { key: 'sabnzbd', name: 'SABnzbd', connected: false },
    { key: 'sonarr', name: 'Sonarr', connected: false },
    { key: 'radarr', name: 'Radarr', connected: false },
    { key: 'plex', name: 'Plex', connected: false },
    { key: 'llm', name: 'AI', connected: false },
  ]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkServices = async () => {
      const serviceKeys = ['sabnzbd', 'sonarr', 'radarr', 'plex', 'llm'];
      const results = await Promise.all(
        serviceKeys.map(async (key) => {
          try {
            const response = await fetch(`/health/${key}`);
            if (!response.ok) {
              return { key, connected: false };
            }
            const data = await response.json();
            // Check the actual healthy field, not just HTTP status
            return { key, connected: data.healthy === true };
          } catch {
            return { key, connected: false };
          }
        })
      );

      setServices((prev) =>
        prev.map((service) => {
          const result = results.find((r) => r.key === service.key);
          return result ? { ...service, connected: result.connected } : service;
        })
      );
      setLoading(false);
    };

    checkServices();
    // Re-check every 30 seconds
    const interval = setInterval(checkServices, 30000);
    return () => clearInterval(interval);
  }, []);

  const connectedCount = services.filter((s) => s.connected).length;

  const handleNavigate = () => {
    if (isMobile && onClose) {
      onClose();
    }
  };

  // Mobile overlay
  if (isMobile) {
    return (
      <>
        {/* Backdrop */}
        {isOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={onClose}
            aria-hidden="true"
          />
        )}

        {/* Sidebar */}
        <aside
          className={`
            fixed top-0 left-0 z-50 flex flex-col lg:hidden
            transform transition-transform duration-300 ease-in-out
            ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          `}
          style={{
            width: 'var(--sidebar-width, 240px)',
            minWidth: 'var(--sidebar-width, 240px)',
            height: '100dvh', /* Use dvh for better mobile support */
            backgroundColor: 'hsl(222 47% 11%)',
          }}
        >
          {/* Close button for mobile - top right */}
          <div className="flex-shrink-0 flex items-center justify-end px-4 py-3 border-b border-[var(--sidebar-border)]">
            <button
              onClick={onClose}
              className="p-2 text-muted-foreground hover:text-white"
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto py-2">
            {baseNavItems.map((item) => (
              <SidebarItem key={item.path} item={item} onNavigate={handleNavigate} />
            ))}
            {services
              .filter((service) => service.connected)
              .map((service) => {
                const item = serviceNavItems[service.key];
                return item ? (
                  <SidebarItem key={item.path} item={item} onNavigate={handleNavigate} />
                ) : null;
              })}
            {footerNavItems.map((item) => (
              <SidebarItem key={item.path} item={item} onNavigate={handleNavigate} />
            ))}
          </nav>

          {/* Footer - Service Status - flex-shrink-0 ensures it stays visible at bottom */}
          <div
            data-component="SidebarServiceStatus"
            className="flex-shrink-0 border-t border-[var(--sidebar-border)] py-3 px-4"
          >
            <div className="text-xs text-muted-foreground mb-2 px-1">
              Services ({connectedCount}/{services.length})
            </div>
            <div className="grid grid-cols-2 gap-1">
              {services.map((service) => (
                <div
                  key={service.key}
                  data-testid={`sidebar-status-${service.key}`}
                  className="flex items-center gap-1.5 px-1 py-0.5"
                  title={service.connected ? `${service.name} connected` : `${service.name} offline`}
                >
                  <div
                    className={`w-1.5 h-1.5 rounded-full ${
                      loading
                        ? 'bg-muted-foreground animate-pulse'
                        : service.connected
                          ? 'bg-green-500'
                          : 'bg-red-500'
                    }`}
                  />
                  <span
                    className={`text-xs truncate ${
                      loading
                        ? 'text-muted-foreground'
                        : service.connected
                          ? 'text-green-500'
                          : 'text-red-500'
                    }`}
                  >
                    {service.name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </>
    );
  }

  // Desktop sidebar (original behavior)
  return (
    <aside
      className="sticky top-0 h-screen flex-col hidden lg:flex"
      style={{
        width: 'var(--sidebar-width, 192px)',
        minWidth: 'var(--sidebar-width, 192px)',
        backgroundColor: 'var(--sidebar-background, hsl(222 47% 11%))',
      }}
    >
      {/* Brand Header - *arr style with logo */}
      <Link
        to="/"
        className="flex items-center gap-3 px-4 py-3 hover:bg-[var(--sidebar-accent)]/50 transition-colors duration-200"
      >
        <img src="/logo-192.png" alt="AutoArr Logo" className="w-10 h-10 object-contain" />
        <div>
          <h1 className="text-lg font-bold text-white leading-tight">AutoArr</h1>
          <p className="text-xs text-muted-foreground">v1.0.0</p>
        </div>
      </Link>

      {/* Navigation - *arr style */}
      <nav className="flex-1 overflow-y-auto py-2">
        {/* Base navigation items */}
        {baseNavItems.map((item) => (
          <SidebarItem key={item.path} item={item} />
        ))}

        {/* Service-specific items - only shown when connected */}
        {services
          .filter((service) => service.connected)
          .map((service) => {
            const item = serviceNavItems[service.key];
            return item ? <SidebarItem key={item.path} item={item} /> : null;
          })}

        {/* Footer navigation items */}
        {footerNavItems.map((item) => (
          <SidebarItem key={item.path} item={item} />
        ))}
      </nav>

      {/* Footer - Service Status */}
      <div
        data-component="SidebarServiceStatus"
        className="border-t border-[var(--sidebar-border)] py-3 px-4"
      >
        <div className="text-xs text-muted-foreground mb-2 px-1">
          Services ({connectedCount}/{services.length})
        </div>
        <div className="grid grid-cols-2 gap-1">
          {services.map((service) => (
            <div
              key={service.key}
              data-testid={`sidebar-status-${service.key}`}
              className="flex items-center gap-1.5 px-1 py-0.5"
              title={service.connected ? `${service.name} connected` : `${service.name} offline`}
            >
              <div
                className={`w-1.5 h-1.5 rounded-full ${
                  loading
                    ? 'bg-muted-foreground animate-pulse'
                    : service.connected
                      ? 'bg-green-500'
                      : 'bg-red-500'
                }`}
              />
              <span
                className={`text-xs truncate ${
                  loading
                    ? 'text-muted-foreground'
                    : service.connected
                      ? 'text-green-500'
                      : 'text-red-500'
                }`}
              >
                {service.name}
              </span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
};

// Mobile menu button component for use in headers
export const MobileMenuButton = ({ onClick }: { onClick: () => void }) => (
  <button
    onClick={onClick}
    className="p-2 text-muted-foreground hover:text-white lg:hidden"
    aria-label="Open menu"
  >
    <Menu className="w-6 h-6" />
  </button>
);
