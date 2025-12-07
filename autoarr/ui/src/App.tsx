import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Activity } from 'lucide-react';
import { SplashScreen } from './components/SplashScreen';
import { MainLayout } from './layouts/MainLayout';
import { Search } from './pages/Search';
import { Settings } from './pages/Settings';
import { Appearance } from './pages/Appearance';
import { Logs } from './pages/Logs';
import { ConnectionStatus } from './components/ConnectionStatus';
import { Placeholder } from './pages/Placeholder';
import { Downloads } from './pages/Downloads';
import { Shows } from './pages/Shows';
import { Movies } from './pages/Movies';
import { Media } from './pages/Media';
import { Home } from './pages/Home';
import { Onboarding } from './pages/Onboarding';
import ConfigAuditPage from './pages/ConfigAudit';
import { useThemeStore } from './stores/themeStore';
import { useOnboardingStore } from './stores/onboardingStore';

/**
 * Component that checks onboarding status and redirects if needed
 */
function OnboardingRedirect({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { completed, needsOnboarding, fetchStatus, isInitializing } = useOnboardingStore();
  const [hasChecked, setHasChecked] = useState(false);

  useEffect(() => {
    // Fetch onboarding status on mount
    fetchStatus().finally(() => setHasChecked(true));
  }, [fetchStatus]);

  // Don't redirect while loading or if we haven't checked yet
  if (!hasChecked || isInitializing) {
    return <>{children}</>;
  }

  // If on onboarding page, allow it
  if (location.pathname === '/onboarding') {
    return <>{children}</>;
  }

  // Redirect to onboarding if not completed and needs onboarding
  if (!completed && needsOnboarding) {
    return <Navigate to="/onboarding" replace />;
  }

  return <>{children}</>;
}

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
      <ConnectionStatus />
      <OnboardingRedirect>
        <Routes>
          {/* Onboarding wizard - standalone, no sidebar */}
          <Route path="/onboarding" element={<Onboarding />} />

          {/* Main app with sidebar layout */}
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Home />} />
            <Route path="search" element={<Search />} />
            <Route path="settings" element={<Settings />} />
            <Route path="settings/appearance" element={<Appearance />} />
            <Route path="settings/config-audit" element={<ConfigAuditPage />} />
            <Route path="settings/logs" element={<Logs />} />
            <Route path="downloads" element={<Downloads />} />
            <Route path="shows" element={<Shows />} />
            <Route path="movies" element={<Movies />} />
            <Route path="media" element={<Media />} />
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
      </OnboardingRedirect>
    </BrowserRouter>
  );
}

export default App;
