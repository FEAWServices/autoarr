import { useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Download, Tv, Film, Server } from "lucide-react";
import { SplashScreen } from "./components/SplashScreen";
import { MainLayout } from "./layouts/MainLayout";
import { Search } from "./pages/Search";
import { Settings } from "./pages/Settings";
import { Placeholder } from "./pages/Placeholder";
import { Dashboard } from "./components/Dashboard";
import ConfigAuditPage from "./pages/ConfigAudit";
import { Activity } from "./pages/Activity";
import { ToastContainer } from "./components/Toast";
import { ErrorBoundary } from "./components/ErrorBoundary";

function App() {
  const [showSplash, setShowSplash] = useState(true);

  const handleSplashComplete = () => {
    setShowSplash(false);
  };

  if (showSplash) {
    return (
      <SplashScreen onComplete={handleSplashComplete} minDisplayTime={2000} />
    );
  }

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ToastContainer />
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="search" element={<Search />} />
            <Route path="settings" element={<Settings />} />
            <Route path="activity" element={<Activity />} />
            <Route path="config-audit" element={<ConfigAuditPage />} />
            <Route
              path="downloads"
              element={
                <Placeholder
                  icon={Download}
                  title="Downloads"
                  description="Monitor and manage your active downloads from SABnzbd"
                />
              }
            />
            <Route
              path="shows"
              element={
                <Placeholder
                  icon={Tv}
                  title="TV Shows"
                  description="Browse and manage your TV show collection with Sonarr"
                />
              }
            />
            <Route
              path="movies"
              element={
                <Placeholder
                  icon={Film}
                  title="Movies"
                  description="Browse and manage your movie collection with Radarr"
                />
              }
            />
            <Route
              path="media"
              element={
                <Placeholder
                  icon={Server}
                  title="Media Server"
                  description="View and manage your Plex media server"
                />
              }
            />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
