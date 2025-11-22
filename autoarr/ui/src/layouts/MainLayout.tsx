import { Outlet } from "react-router-dom";
import { Sidebar } from "../components/Sidebar";

export const MainLayout = () => {
  return (
    <div className="flex h-screen bg-gradient-hero dark:bg-background-primary text-white overflow-hidden relative">
      {/* Animated Gradient Mesh Background */}
      <div className="absolute inset-0 bg-gradient-mesh opacity-30 dark:opacity-50 pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary-900/20 via-transparent to-transparent pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 flex w-full h-full">
        <Sidebar />
        <main className="flex-1 overflow-y-auto backdrop-blur-[2px]">
          <div className="min-h-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
