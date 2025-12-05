import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Download, Tv, Film, Server, Activity } from 'lucide-react';
import { SplashScreen } from './components/SplashScreen';
import { MainLayout } from './layouts/MainLayout';
import { Search } from './pages/Search';
import { Settings } from './pages/Settings';
import { Appearance } from './pages/Appearance';
import { Placeholder } from './pages/Placeholder';
import { Home } from './pages/Home';
import ConfigAuditPage from './pages/ConfigAudit';
import { Chat } from './pages/Chat';
import { useThemeStore } from './stores/themeStore';

function App() {
  const [showSplash, setShowSplash] = useState(true);
  const { _initializeTheme } = useThemeStore();

  // Initialize theme system on mount
  useEffect(() => {
    _initializeTheme();
  }, [_initializeTheme]);

  const handleSplashComplete = () => {
    setShowSplash(false);
  };

  if (showSplash) {
    return <SplashScreen onComplete={handleSplashComplete} minDisplayTime={2000} />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Home />} />
          <Route path="chat" element={<Chat />} />
          <Route path="search" element={<Search />} />
          <Route path="settings" element={<Settings />} />
          <Route path="settings/appearance" element={<Appearance />} />
          <Route path="settings/config-audit" element={<ConfigAuditPage />} />
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
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
