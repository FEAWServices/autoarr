import { useState, useCallback } from 'react';
import { Outlet, Link } from 'react-router-dom';
import { Menu } from 'lucide-react';
import { Sidebar } from '../components/Sidebar';
import { SetupBanner } from '../components/Onboarding/SetupBanner';
import { PullToRefresh } from '../components/PullToRefresh';

export const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Handle pull-to-refresh - reload the page
  const handleRefresh = useCallback(async () => {
    window.location.reload();
  }, []);

  return (
    <div
      className="flex h-full w-full bg-background text-foreground overflow-hidden relative"
      style={{ maxWidth: '100%', maxHeight: '100%', overflow: 'hidden' }}
    >
      {/* Animated Gradient Mesh Background - More dramatic like visual-spark */}
      <div
        className="absolute inset-0 pointer-events-none opacity-60"
        style={{
          background: `
            radial-gradient(at 20% 10%, hsla(280, 85%, 60%, 0.35) 0px, transparent 50%),
            radial-gradient(at 80% 20%, hsla(290, 90%, 70%, 0.35) 0px, transparent 50%),
            radial-gradient(at 10% 60%, hsla(260, 70%, 50%, 0.25) 0px, transparent 50%),
            radial-gradient(at 90% 80%, hsla(300, 80%, 65%, 0.20) 0px, transparent 50%)
          `,
        }}
      />
      {/* Bottom gradient fade */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[hsl(280,50%,8%)] pointer-events-none" />

      {/* Content */}
      <div
        className="relative z-10 flex w-full h-full overflow-hidden"
        style={{ maxWidth: '100%', maxHeight: '100%', overflow: 'hidden' }}
      >
        {/* Desktop Sidebar */}
        <Sidebar />

        {/* Mobile Sidebar (drawer) */}
        <Sidebar isMobile isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <main className="flex-1 flex flex-col overflow-hidden min-w-0">
          {/* Mobile Header - shows hamburger menu on mobile */}
          <header className="flex items-center justify-between px-4 py-3 border-b border-border/30 lg:hidden bg-background/80 backdrop-blur-sm">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 -ml-2 text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Open menu"
            >
              <Menu className="w-6 h-6" />
            </button>

            {/* Mobile Logo */}
            <Link to="/" className="flex items-center gap-2">
              <img src="/logo-192.png" alt="AutoArr" className="w-8 h-8" />
              <span className="font-bold text-lg">AutoArr</span>
            </Link>

            {/* Spacer to center logo */}
            <div className="w-10" />
          </header>

          {/* Setup Banner - shows when onboarding incomplete */}
          <SetupBanner />

          <PullToRefresh onRefresh={handleRefresh} className="flex-1 overflow-x-hidden">
            <div className="min-h-full w-full max-w-full overflow-x-hidden">
              <Outlet />
            </div>
          </PullToRefresh>
        </main>
      </div>
    </div>
  );
};
