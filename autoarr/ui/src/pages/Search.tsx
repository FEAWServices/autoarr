import { useState } from "react";
import { Search as SearchIcon, Film } from "lucide-react";

interface SearchResult {
  id: string;
  title: string;
  type: "movie" | "show";
  description: string;
  poster: string;
  year?: number;
}

export const Search = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    // TODO: Implement actual API call to search endpoint
    setTimeout(() => {
      // Mock results
      setResults([
        {
          id: "1",
          title: "The Simpsons",
          type: "show",
          description:
            "This animated comedy focuses on the everyday life of the Simpson family in the misfit city of Springfield.",
          poster:
            "https://via.placeholder.com/200x300/4a5568/ffffff?text=The+Simpsons",
          year: 1989,
        },
        {
          id: "2",
          title: "Mission: Impossible - Dead Reckoning Part One",
          type: "movie",
          description:
            "Ethan Hunt and his IMF team embark on their most dangerous mission yet: To track down a terrifying new weapon that...",
          poster:
            "https://via.placeholder.com/200x300/2d3748/ffffff?text=Mission+Impossible",
          year: 2023,
        },
      ]);
      setIsSearching(false);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleAddToSonarr = (result: SearchResult) => {
    // TODO: Implement add to Sonarr
    console.log("Add to Sonarr:", result);
  };

  const handleAddToRadarr = (result: SearchResult) => {
    // TODO: Implement add to Radarr
    console.log("Add to Radarr:", result);
  };

  return (
    <div className="flex flex-col h-full bg-background-primary">
      {/* Header */}
      <div className="px-8 py-12">
        <h1 className="text-4xl font-bold text-white mb-3">
          Search and Add to Your Library
        </h1>
        <p className="text-text-secondary text-lg">
          Use natural language to find and add movies and TV shows to your
          collection.
        </p>
      </div>

      {/* Search Input */}
      <div className="px-8 mb-12">
        <div className="max-w-4xl">
          <div className="relative">
            <SearchIcon className="absolute left-6 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="e.g., 'add The Simpsons' or 'get me the latest Mission Impossible movie'"
              className="w-full pl-14 pr-6 py-4 bg-background-secondary border border-background-tertiary rounded-lg text-white placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-lg"
            />
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto px-8 pb-8">
        {results.length > 0 ? (
          <div className="max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-6">
            {results.map((result) => (
              <div
                key={result.id}
                className="bg-background-secondary border border-background-tertiary rounded-lg p-6 flex gap-4"
              >
                <div className="flex-shrink-0">
                  <img
                    src={result.poster}
                    alt={result.title}
                    className="w-32 h-48 object-cover rounded-lg"
                  />
                </div>
                <div className="flex-1 flex flex-col">
                  <div className="mb-2">
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                        result.type === "show"
                          ? "bg-primary/20 text-primary"
                          : "bg-yellow-500/20 text-yellow-500"
                      }`}
                    >
                      {result.type === "show" ? "TV Show" : "Movie"}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">
                    {result.title}
                  </h3>
                  <p className="text-text-secondary text-sm mb-4 line-clamp-3">
                    {result.description}
                  </p>
                  <div className="mt-auto">
                    {result.type === "show" ? (
                      <button
                        onClick={() => handleAddToSonarr(result)}
                        className="w-full bg-primary hover:bg-primary-dark text-white py-3 px-4 rounded-lg transition-colors font-semibold"
                      >
                        Add to Sonarr
                      </button>
                    ) : (
                      <button
                        onClick={() => handleAddToRadarr(result)}
                        className="w-full bg-primary hover:bg-primary-dark text-white py-3 px-4 rounded-lg transition-colors font-semibold"
                      >
                        Add to Radarr
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-24 h-24 bg-background-secondary rounded-full flex items-center justify-center mb-6">
              <Film className="w-12 h-12 text-text-muted" />
            </div>
            <h2 className="text-2xl font-semibold text-white mb-3">
              Start by searching for a movie or TV show.
            </h2>
            <p className="text-text-secondary max-w-md">
              Type in the search bar above to find media to add to your library.
            </p>
          </div>
        )}

        {isSearching && (
          <div className="flex items-center justify-center h-64">
            <div className="flex flex-col items-center gap-4">
              <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin" />
              <p className="text-text-muted">Searching...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
