/**
 * Service Selection Step
 *
 * Allows users to select which services they want to integrate with AutoArr.
 * Uses the service plugin architecture for extensibility.
 * Shows already-connected services in a separate green section at the bottom.
 */

import { useEffect, useState } from 'react';
import { ArrowRight, ArrowLeft, Check, CheckCircle2 } from 'lucide-react';
import { useOnboardingStore } from '../../../stores/onboardingStore';
import {
  servicePlugins,
  getColorClasses,
  type ServicePlugin,
} from '../../../plugins/services';

interface ServiceCardProps {
  plugin: ServicePlugin;
  selected: boolean;
  onToggle: (selected: boolean) => void;
  connected?: boolean;
}

const ServiceCard = ({ plugin, selected, onToggle, connected = false }: ServiceCardProps) => {
  const colors = getColorClasses(plugin);

  // For connected services, use green styling
  const borderClass = connected
    ? 'border-green-500/50 bg-green-500/5'
    : selected
      ? `${colors.border} ${colors.bg}`
      : 'border-border hover:border-primary/30';

  return (
    <button
      onClick={() => !connected && onToggle(!selected)}
      disabled={connected}
      className={`
        relative w-full p-5 rounded-xl border-2 text-left transition-all
        ${borderClass}
        ${connected ? 'cursor-default' : 'cursor-pointer'}
      `}
      data-testid={`service-card-${plugin.id}`}
    >
      {/* Selected/Connected indicator */}
      {(selected || connected) && (
        <div className={`absolute top-3 right-3 w-6 h-6 rounded-full ${connected ? 'bg-green-500/20' : colors.bg} flex items-center justify-center`}>
          {connected ? (
            <CheckCircle2 className="w-4 h-4 text-green-500" />
          ) : (
            <Check className={`w-4 h-4 ${colors.text}`} />
          )}
        </div>
      )}

      <div className="flex items-start gap-4">
        {/* Logo image - fixed size for consistency */}
        <div className="w-12 h-12 rounded-xl bg-card flex items-center justify-center flex-shrink-0 overflow-hidden">
          <img
            src={plugin.logo}
            alt={`${plugin.name} logo`}
            className="w-10 h-10 object-contain"
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-foreground">{plugin.name}</h3>
            {connected && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-green-500/20 text-green-500">
                Connected
              </span>
            )}
            {!connected && plugin.optional && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                Optional
              </span>
            )}
          </div>
          <p className="text-sm text-muted-foreground line-clamp-2">
            {plugin.description}
          </p>
          <div className="mt-2 text-xs text-muted-foreground">
            Default port: {plugin.defaultPort}
          </div>
        </div>
      </div>
    </button>
  );
};

export const ServiceSelectionStep = () => {
  const {
    previousStep,
    nextStep,
    selectedServices,
    selectService,
    isLoading,
  } = useOnboardingStore();

  // Track which services are already connected
  const [connectedServices, setConnectedServices] = useState<string[]>([]);
  const [checkingConnections, setCheckingConnections] = useState(true);

  // Check which services are already connected on mount
  useEffect(() => {
    const checkConnections = async () => {
      setCheckingConnections(true);
      const connected: string[] = [];

      for (const plugin of servicePlugins) {
        try {
          const response = await fetch(`/health/${plugin.id}`);
          if (response.ok) {
            const data = await response.json();
            if (data.healthy === true) {
              connected.push(plugin.id);
            }
          }
        } catch {
          // Service not connected
        }
      }

      setConnectedServices(connected);
      setCheckingConnections(false);
    };

    checkConnections();
  }, []);

  const handleContinue = async () => {
    if (selectedServices.length > 0) {
      await nextStep();
    } else {
      // Skip service config if nothing selected
      await nextStep();
    }
  };

  // Separate connected and unconnected services
  const unconnectedPlugins = servicePlugins.filter(p => !connectedServices.includes(p.id));
  const connectedPlugins = servicePlugins.filter(p => connectedServices.includes(p.id));

  // Group unconnected services by category
  const downloadServices = unconnectedPlugins.filter((p) => p.category === 'download');
  const mediaServices = unconnectedPlugins.filter((p) => p.category === 'media');
  const streamingServices = unconnectedPlugins.filter((p) => p.category === 'streaming');

  return (
    <div className="max-w-2xl mx-auto" data-testid="service-selection-step">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Select Your Services
        </h2>
        <p className="text-muted-foreground">
          Choose which services you want to integrate with AutoArr.
          You can add more later from Settings.
        </p>
      </div>

      {checkingConnections ? (
        <div className="text-center py-8 text-muted-foreground">
          Checking service connections...
        </div>
      ) : (
        <>
          {/* Download Services */}
          {downloadServices.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
                Download Client
              </h3>
              <div className="grid gap-4">
                {downloadServices.map((plugin) => (
                  <ServiceCard
                    key={plugin.id}
                    plugin={plugin}
                    selected={selectedServices.includes(plugin.id)}
                    onToggle={(selected) => selectService(plugin.id, selected)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Media Management */}
          {mediaServices.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
                Media Management
              </h3>
              <div className="grid gap-4 sm:grid-cols-2">
                {mediaServices.map((plugin) => (
                  <ServiceCard
                    key={plugin.id}
                    plugin={plugin}
                    selected={selectedServices.includes(plugin.id)}
                    onToggle={(selected) => selectService(plugin.id, selected)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Streaming */}
          {streamingServices.length > 0 && (
            <div className="mb-8">
              <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
                Media Server
              </h3>
              <div className="grid gap-4">
                {streamingServices.map((plugin) => (
                  <ServiceCard
                    key={plugin.id}
                    plugin={plugin}
                    selected={selectedServices.includes(plugin.id)}
                    onToggle={(selected) => selectService(plugin.id, selected)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Already Connected Services - Green Section at Bottom */}
          {connectedPlugins.length > 0 && (
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <h3 className="text-sm font-medium text-green-500 uppercase tracking-wide">
                  Already Connected
                </h3>
              </div>
              <div className="p-4 rounded-xl border-2 border-green-500/30 bg-green-500/5">
                <div className="grid gap-4 sm:grid-cols-2">
                  {connectedPlugins.map((plugin) => (
                    <ServiceCard
                      key={plugin.id}
                      plugin={plugin}
                      selected={false}
                      onToggle={() => {}}
                      connected={true}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Selection summary - only show if there are unconnected services to select */}
          {unconnectedPlugins.length > 0 && (
            <div className="bg-card rounded-xl border border-border p-4 mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Selected services</p>
                  <p className="text-lg font-semibold text-foreground">
                    {selectedServices.length} of {unconnectedPlugins.length}
                  </p>
                </div>
                {selectedServices.length > 0 && (
                  <div className="flex gap-2">
                    {selectedServices.map((id) => {
                      const plugin = servicePlugins.find((p) => p.id === id);
                      if (!plugin) return null;
                      return (
                        <div
                          key={id}
                          className="w-8 h-8 rounded-lg bg-card border border-border flex items-center justify-center overflow-hidden"
                          title={plugin.name}
                        >
                          <img
                            src={plugin.logo}
                            alt={plugin.name}
                            className="w-6 h-6 object-contain"
                          />
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={previousStep}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl border border-border text-muted-foreground hover:text-foreground hover:border-foreground/30 transition-colors disabled:opacity-50"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        <button
          onClick={handleContinue}
          disabled={isLoading || checkingConnections}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          data-testid="continue-button"
        >
          {selectedServices.length > 0 ? (
            <>
              Configure {selectedServices.length} Service{selectedServices.length > 1 ? 's' : ''}
              <ArrowRight className="w-4 h-4" />
            </>
          ) : connectedPlugins.length > 0 && unconnectedPlugins.length === 0 ? (
            <>
              All Services Connected
              <ArrowRight className="w-4 h-4" />
            </>
          ) : (
            <>
              Skip Services
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
};
