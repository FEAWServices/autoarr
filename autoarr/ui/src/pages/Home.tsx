import { Plus, Search, Bell } from "lucide-react";

interface ServiceStatus {
  name: string;
  status: "Online" | "Offline";
  detail: string;
  isError?: boolean;
}

interface MediaItem {
  title: string;
  subtitle: string;
  image: string;
  type: "movie" | "show";
}

interface DownloadItem {
  title: string;
  progress: number;
}

export const Home = () => {
  // Mock data - will be replaced with real API calls
  const services: ServiceStatus[] = [
    { name: "Sonarr", status: "Online", detail: "256 GB Free" },
    { name: "Radarr", status: "Online", detail: "1.2 TB Free" },
    { name: "Plex", status: "Online", detail: "1,234 items" },
    { name: "SABnzbd", status: "Offline", detail: "0 MB/s", isError: true },
  ];

  const nextUp: MediaItem[] = [
    {
      title: "The Boys",
      subtitle: 'S04E01 - "Department of Dirty Tricks"',
      image: "https://via.placeholder.com/240x360/4a5568/ffffff?text=The+Boys",
      type: "show",
    },
    {
      title: "House of the Dragon",
      subtitle: 'S02E02 - "Rhaenyra the Cruel"',
      image:
        "https://via.placeholder.com/240x360/2d3748/ffffff?text=House+Dragon",
      type: "show",
    },
    {
      title: "Inside Out 2",
      subtitle: "Movie",
      image:
        "https://via.placeholder.com/240x360/4299e1/ffffff?text=Inside+Out+2",
      type: "movie",
    },
    {
      title: "The Acolyte",
      subtitle: 'S01E04 - "Day"',
      image:
        "https://via.placeholder.com/240x360/2d3748/ffffff?text=The+Acolyte",
      type: "show",
    },
  ];

  const downloads: DownloadItem[] = [
    { title: "Movie Title 1 (2023)", progress: 75 },
    { title: "TV Show S01E05", progress: 40 },
    { title: "Another Movie (2022)", progress: 20 },
  ];

  const libraryStats = [
    {
      label: "Movies",
      percentage: 70,
      color: "text-blue-500",
      bgColor: "text-blue-500/20",
    },
    {
      label: "4K",
      percentage: 60,
      color: "text-yellow-500",
      bgColor: "text-yellow-500/20",
    },
    {
      label: "Action",
      percentage: 85,
      color: "text-green-500",
      bgColor: "text-green-500/20",
    },
  ];

  return (
    <div className="flex flex-col h-full bg-background-primary">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-6 border-b border-background-tertiary">
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-background-tertiary rounded-lg transition-colors">
            <Plus className="w-6 h-6 text-white" />
          </button>
          <button className="p-2 hover:bg-background-tertiary rounded-lg transition-colors">
            <Search className="w-6 h-6 text-white" />
          </button>
          <button className="p-2 hover:bg-background-tertiary rounded-lg transition-colors">
            <Bell className="w-6 h-6 text-white" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* System Status */}
          <section>
            <h2 className="text-xl font-semibold text-white mb-4">
              System Status
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {services.map((service) => (
                <div
                  key={service.name}
                  className="bg-background-secondary border border-background-tertiary rounded-lg p-6"
                >
                  <h3 className="text-text-secondary text-sm mb-2">
                    {service.name}
                  </h3>
                  <p
                    className={`text-2xl font-bold mb-2 ${
                      service.isError ? "text-status-error" : "text-white"
                    }`}
                  >
                    {service.status}
                  </p>
                  <p
                    className={`text-sm ${
                      service.isError
                        ? "text-status-error"
                        : "text-status-success"
                    }`}
                  >
                    {service.detail}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* Next Up */}
          <section>
            <h2 className="text-xl font-semibold text-white mb-4">Next Up</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {nextUp.map((item, index) => (
                <div
                  key={index}
                  className="bg-background-secondary border border-background-tertiary rounded-lg overflow-hidden group cursor-pointer hover:border-primary transition-colors"
                >
                  <div className="aspect-[2/3] bg-background-tertiary">
                    <img
                      src={item.image}
                      alt={item.title}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="p-4">
                    <h3 className="text-white font-semibold mb-1">
                      {item.title}
                    </h3>
                    <p className="text-text-muted text-sm mb-3">
                      {item.subtitle}
                    </p>
                    <button className="w-full bg-primary hover:bg-primary-dark text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2">
                      ▶ Play on Plex
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Unified Download Queue */}
            <section>
              <h2 className="text-xl font-semibold text-white mb-4">
                Unified Download Queue
              </h2>
              <div className="bg-background-secondary border border-background-tertiary rounded-lg p-6">
                <div className="space-y-4">
                  {downloads.map((download, index) => (
                    <div key={index}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-white text-sm">
                          {download.title}
                        </span>
                        <span className="text-text-muted text-sm">
                          {download.progress}%
                        </span>
                      </div>
                      <div className="h-2 bg-background-tertiary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all"
                          style={{ width: `${download.progress}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-text-muted text-sm text-center mt-6">
                  Your download queue is looking good.
                </p>
              </div>
            </section>

            {/* Library Overview */}
            <section>
              <h2 className="text-xl font-semibold text-white mb-4">
                Library Overview
              </h2>
              <div className="bg-background-secondary border border-background-tertiary rounded-lg p-6">
                <div className="flex items-center justify-center gap-8 mb-6">
                  {libraryStats.map((stat) => (
                    <div
                      key={stat.label}
                      className="flex flex-col items-center"
                    >
                      <div className="relative w-24 h-24">
                        <svg className="w-24 h-24 transform -rotate-90">
                          <circle
                            cx="48"
                            cy="48"
                            r="40"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="none"
                            className={stat.bgColor}
                          />
                          <circle
                            cx="48"
                            cy="48"
                            r="40"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="none"
                            strokeDasharray={`${2 * Math.PI * 40}`}
                            strokeDashoffset={`${
                              2 * Math.PI * 40 * (1 - stat.percentage / 100)
                            }`}
                            className={stat.color}
                            strokeLinecap="round"
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className={`text-2xl font-bold ${stat.color}`}>
                            {stat.percentage}%
                          </span>
                        </div>
                      </div>
                      <span className="text-text-muted text-sm mt-2">
                        {stat.label}
                      </span>
                    </div>
                  ))}
                </div>
                <p className="text-text-muted text-sm text-center">
                  Library is primarily composed of action movies in 4K.
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>

      {/* Add Media Button (Bottom Left) */}
      <button className="fixed bottom-8 left-72 bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-lg shadow-glow transition-all flex items-center gap-2 font-semibold">
        <Plus className="w-5 h-5" />
        Add Media
      </button>
    </div>
  );
};
