import { RequestInfo, RequestStatus as StatusType } from '../../types/chat';
import { CheckCircle, XCircle, Clock, Download, Search, AlertCircle, RotateCw } from 'lucide-react';

interface RequestStatusProps {
  request: RequestInfo;
  onRetry?: () => void;
  onCancel?: () => void;
}

const getStatusConfig = (status: StatusType) => {
  switch (status) {
    case 'submitted':
      return {
        icon: Clock,
        color: 'text-text-muted',
        bgColor: 'bg-background-tertiary',
        label: 'Submitted',
      };
    case 'classified':
      return {
        icon: CheckCircle,
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/10',
        label: 'Classified',
      };
    case 'searching':
      return {
        icon: Search,
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/10',
        label: 'Searching',
      };
    case 'pending_confirmation':
      return {
        icon: Clock,
        color: 'text-yellow-400',
        bgColor: 'bg-yellow-500/10',
        label: 'Awaiting Confirmation',
      };
    case 'downloading':
      return {
        icon: Download,
        color: 'text-green-400',
        bgColor: 'bg-green-500/10',
        label: 'Downloading',
      };
    case 'completed':
      return {
        icon: CheckCircle,
        color: 'text-status-success',
        bgColor: 'bg-green-500/10',
        label: 'Completed',
      };
    case 'failed':
      return {
        icon: XCircle,
        color: 'text-status-error',
        bgColor: 'bg-red-500/10',
        label: 'Failed',
      };
    case 'cancelled':
      return {
        icon: AlertCircle,
        color: 'text-text-muted',
        bgColor: 'bg-background-tertiary',
        label: 'Cancelled',
      };
    default:
      return {
        icon: Clock,
        color: 'text-text-muted',
        bgColor: 'bg-background-tertiary',
        label: status,
      };
  }
};

export const RequestStatus = ({ request, onRetry, onCancel }: RequestStatusProps) => {
  const config = getStatusConfig(request.status);
  const Icon = config.icon;

  const showProgressBar = request.status === 'downloading' && request.progress !== undefined;
  const showRetry = request.status === 'failed' && onRetry;
  const showCancel =
    (request.status === 'downloading' || request.status === 'searching') && onCancel;

  return (
    <div
      data-testid="request-status"
      className="flex flex-col gap-3 p-4 bg-background-secondary rounded-lg border border-background-tertiary"
    >
      {/* Status Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${config.bgColor}`}>
            <Icon className={`w-5 h-5 ${config.color}`} />
          </div>
          <div className="flex flex-col">
            <span
              data-testid="request-status-badge"
              className="text-sm font-medium text-text-primary"
            >
              {config.label}
            </span>
            <span className="text-xs text-text-muted">{request.title}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {showRetry && (
            <button
              onClick={onRetry}
              className="p-2 hover:bg-background-tertiary rounded-lg transition-colors"
              aria-label="Retry request"
            >
              <RotateCw className="w-4 h-4 text-text-secondary" />
            </button>
          )}
          {showCancel && (
            <button
              onClick={onCancel}
              className="px-3 py-1 text-sm text-text-secondary hover:text-text-primary bg-background-tertiary hover:bg-background-hover rounded transition-colors"
              aria-label="Cancel request"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {showProgressBar && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-text-muted">
            <span>{request.progress}%</span>
            {request.eta && <span>ETA: {request.eta}</span>}
          </div>
          <div
            data-testid="download-progress-bar"
            className="w-full h-2 bg-background-tertiary rounded-full overflow-hidden"
          >
            <div
              className="h-full bg-gradient-primary transition-all duration-300 ease-out progress-bar"
              data-progress={request.progress}
              role="progressbar"
              aria-valuenow={request.progress}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Download progress: ${request.progress}%`}
            />
          </div>
        </div>
      )}

      {/* Error Message */}
      {request.status === 'failed' && request.error && (
        <div className="text-sm text-status-error bg-red-500/10 px-3 py-2 rounded">
          {request.error}
        </div>
      )}

      {/* Timestamps */}
      <div className="flex justify-between text-xs text-text-muted">
        <span>Started: {new Date(request.createdAt).toLocaleTimeString()}</span>
        {request.status === 'completed' && (
          <span>Completed: {new Date(request.updatedAt).toLocaleTimeString()}</span>
        )}
      </div>
    </div>
  );
};
