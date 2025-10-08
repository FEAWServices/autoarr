import { useState } from "react";
import { ContentSearchResult } from "../../types/chat";
import { Film, Tv, Star, Calendar, Plus } from "lucide-react";

interface ContentCardProps {
  content: ContentSearchResult;
  onAdd?: (tmdbId: number) => void;
}

const TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500";

export const ContentCard = ({ content, onAdd }: ContentCardProps) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleAdd = async () => {
    if (!onAdd) return;

    setIsLoading(true);
    try {
      await onAdd(content.tmdbId);
    } finally {
      setIsLoading(false);
    }
  };

  const posterUrl = content.posterPath
    ? `${TMDB_IMAGE_BASE_URL}${content.posterPath}`
    : null;

  const truncatedOverview =
    content.overview.length > 150 && !isExpanded
      ? `${content.overview.slice(0, 150)}...`
      : content.overview;

  const releaseYear =
    content.year ||
    (content.releaseDate
      ? new Date(content.releaseDate).getFullYear()
      : content.firstAirDate
        ? new Date(content.firstAirDate).getFullYear()
        : null);

  return (
    <div
      data-testid="content-card"
      className="flex gap-4 p-4 bg-background-secondary rounded-lg border border-background-tertiary hover:border-primary-default transition-all"
    >
      {/* Poster */}
      <div className="flex-shrink-0 w-24 sm:w-32">
        {posterUrl ? (
          <img
            src={posterUrl}
            alt={`${content.title} poster`}
            className="w-full h-auto rounded-md"
            loading="lazy"
          />
        ) : (
          <div className="w-full aspect-[2/3] bg-background-tertiary rounded-md flex items-center justify-center">
            {content.mediaType === "movie" ? (
              <Film className="w-8 h-8 text-text-muted" />
            ) : (
              <Tv className="w-8 h-8 text-text-muted" />
            )}
          </div>
        )}
      </div>

      {/* Content Details */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-text-primary truncate">
              {content.title}
            </h3>
            <div className="flex items-center gap-3 text-sm text-text-secondary mt-1">
              {releaseYear && (
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>{releaseYear}</span>
                </div>
              )}
              {content.voteAverage && content.voteAverage > 0 && (
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-yellow-500" />
                  <span>{content.voteAverage.toFixed(1)}</span>
                </div>
              )}
              <div className="flex items-center gap-1">
                {content.mediaType === "movie" ? (
                  <Film className="w-4 h-4" />
                ) : (
                  <Tv className="w-4 h-4" />
                )}
                <span className="capitalize">{content.mediaType}</span>
              </div>
            </div>
          </div>

          {/* Add Button */}
          <button
            onClick={handleAdd}
            disabled={isLoading}
            className="px-4 py-2 bg-gradient-primary text-white rounded-lg hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 flex-shrink-0"
            aria-label={`Add ${content.title} to library`}
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            <span className="hidden sm:inline">Add</span>
          </button>
        </div>

        {/* Overview */}
        <div
          data-testid="content-overview"
          className="text-sm text-text-secondary leading-relaxed"
        >
          <p>{truncatedOverview}</p>
          {content.overview.length > 150 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-primary-default hover:text-primary-dark mt-1 font-medium"
              aria-label={isExpanded ? "Show less" : "Show more"}
            >
              {isExpanded ? "Show less" : "Show more"}
            </button>
          )}
        </div>

        {/* Original Title if different */}
        {content.originalTitle && content.originalTitle !== content.title && (
          <p className="text-xs text-text-muted mt-2">
            Original: {content.originalTitle}
          </p>
        )}
      </div>
    </div>
  );
};
