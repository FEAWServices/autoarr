import { Outlet } from "react-router-dom";
import { Sidebar } from "../components/Sidebar";

export const MainLayout = () => {
  return (
    <div className="flex h-screen bg-background-primary text-white overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-background-primary">
        <Outlet />
      </main>
    </div>
  );
};
