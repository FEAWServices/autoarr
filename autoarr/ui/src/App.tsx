import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Download, Tv, Film, Server, Activity } from "lucide-react";
import { SplashScreen } from "./components/SplashScreen";
import { MainLayout } from "./layouts/MainLayout";
import { Search } from "./pages/Search";
import { Settings } from "./pages/Settings";
import { Placeholder } from "./pages/Placeholder";
import { Dashboard } from "./components/Dashboard";
import ConfigAuditPage from "./pages/ConfigAudit";
import { Chat } from "./pages/Chat";
import { useThemeStore } from "./stores/themeStore";

function App() {
  const [showSplash, setShowSplash] = useState(true);
  const { isDarkMode } = useThemeStore();

  // Initialize dark mode on mount
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const handleSplashComplete = () => {
    setShowSplash(false);
  };

  if (showSplash) {
    return (
      <SplashScreen onComplete={handleSplashComplete} minDisplayTime={2000} />
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="chat" element={<Chat />} />
          <Route path="search" element={<Search />} />
          <Route path="settings" element={<Settings />} />
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
          <Route
            path="activity"
            element={
              <Placeholder
                icon={Activity}
                title="Activity"
                description="View recent activity and system logs"
              />
            }
          />
          <Route path="config-audit" element={<ConfigAuditPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
