import { useState } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { RequestStatus } from '../../types/chat';
import { X, Film, Tv } from 'lucide-react';

interface ChatSearchProps {
  onClose: () => void;
}

export const ChatSearch = ({ onClose }: ChatSearchProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'movie' | 'tv' | undefined>();
  const [filterStatus, setFilterStatus] = useState<RequestStatus | undefined>();

  const { getFilteredMessages } = useChatStore();

  const filteredMessages = getFilteredMessages({
    searchTerm: searchTerm || undefined,
    type: filterType,
    status: filterStatus,
  });

  return (
    <div className="bg-background-tertiary rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary">Search Messages</h3>
        <button
          onClick={onClose}
          className="p-1 hover:bg-background-hover rounded transition-colors"
          aria-label="Close search"
        >
          <X className="w-5 h-5 text-text-secondary" />
        </button>
      </div>

      {/* Search Input */}
      <div className="mb-4">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search messages..."
          className="w-full bg-background-secondary text-text-primary placeholder-text-muted px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-default"
          aria-label="Search messages"
        />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        {/* Content Type Filter */}
        <div className="flex gap-2">
          <button
            onClick={() => setFilterType(undefined)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filterType === undefined
                ? 'bg-primary-default text-white'
                : 'bg-background-secondary text-text-secondary hover:text-text-primary'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilterType('movie')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
              filterType === 'movie'
                ? 'bg-primary-default text-white'
                : 'bg-background-secondary text-text-secondary hover:text-text-primary'
            }`}
          >
            <Film className="w-4 h-4" />
            Movies
          </button>
          <button
            onClick={() => setFilterType('tv')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
              filterType === 'tv'
                ? 'bg-primary-default text-white'
                : 'bg-background-secondary text-text-secondary hover:text-text-primary'
            }`}
          >
            <Tv className="w-4 h-4" />
            TV Shows
          </button>
        </div>

        {/* Status Filter */}
        <div className="flex gap-2">
          <select
            value={filterStatus || ''}
            onChange={(e) =>
              setFilterStatus(e.target.value ? (e.target.value as RequestStatus) : undefined)
            }
            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-background-secondary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-default"
            aria-label="Filter by status"
          >
            <option value="">All Status</option>
            <option value="completed">Completed</option>
            <option value="downloading">Downloading</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Results */}
      <div className="text-sm text-text-muted mb-2">
        {filteredMessages.length} message
        {filteredMessages.length !== 1 ? 's' : ''} found
      </div>

      {searchTerm && filteredMessages.length === 0 && (
        <div className="text-center py-8 text-text-muted">
          <p>No messages match your search criteria</p>
        </div>
      )}
    </div>
  );
};
