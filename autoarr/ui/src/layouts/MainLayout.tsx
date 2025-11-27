import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';

export const MainLayout = () => {
  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden relative">
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
      <div className="relative z-10 flex w-full h-full">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <div className="min-h-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
