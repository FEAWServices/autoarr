import { useEffect, useState } from 'react';

interface SplashScreenProps {
  onComplete: () => void;
  minDisplayTime?: number;
}

export const SplashScreen = ({ onComplete, minDisplayTime = 2000 }: SplashScreenProps) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Simulate loading progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, minDisplayTime / 10);

    // Complete splash screen after min display time
    const timer = setTimeout(() => {
      onComplete();
    }, minDisplayTime);

    return () => {
      clearInterval(interval);
      clearTimeout(timer);
    };
  }, [onComplete, minDisplayTime]);

  return (
    <div className="fixed inset-0 bg-gradient-hero flex items-center justify-center z-50">
      <div className="flex flex-col items-center text-center">
        {/* Logo with text */}
        <div className="mb-6 animate-pulse">
          <div className="bg-white rounded-full p-8 shadow-lg">
            <img
              src="/logo.png"
              alt="AutoArr"
              className="w-48 h-auto"
            />
          </div>
        </div>

        {/* Tagline */}
        <p className="text-xl text-text-secondary mb-8">Intelligent Media, Automated.</p>

        {/* Loading Bar */}
        <div className="w-64">
          <div className="h-1.5 bg-background-tertiary rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-primary transition-all duration-300 ease-out progress-bar"
              data-progress={progress}
              data-testid="loading-bar"
            />
          </div>
          <p className="text-text-muted text-sm mt-3">Loading...</p>
        </div>
      </div>
    </div>
  );
};
