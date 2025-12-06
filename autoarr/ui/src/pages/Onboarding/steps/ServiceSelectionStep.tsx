/**
 * Service Selection Step
 *
 * Allows users to select which services they want to integrate with AutoArr.
 * Uses the service plugin architecture for extensibility.
 */

import { ArrowRight, ArrowLeft, Check } from 'lucide-react';
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
}

const ServiceCard = ({ plugin, selected, onToggle }: ServiceCardProps) => {
  const colors = getColorClasses(plugin);
  const Icon = plugin.icon;

  return (
    <button
      onClick={() => onToggle(!selected)}
      className={`
        relative w-full p-5 rounded-xl border-2 text-left transition-all
        ${
          selected
            ? `${colors.border} ${colors.bg}`
            : 'border-border hover:border-primary/30'
        }
      `}
      data-testid={`service-card-${plugin.id}`}
    >
      {/* Selected indicator */}
      {selected && (
        <div className={`absolute top-3 right-3 w-6 h-6 rounded-full ${colors.bg} flex items-center justify-center`}>
          <Check className={`w-4 h-4 ${colors.text}`} />
        </div>
      )}

      <div className="flex items-start gap-4">
        <div className={`w-12 h-12 rounded-xl ${colors.bg} flex items-center justify-center flex-shrink-0`}>
          <Icon className={`w-6 h-6 ${colors.text}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-foreground">{plugin.name}</h3>
            {plugin.optional && (
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

  const handleContinue = async () => {
    if (selectedServices.length > 0) {
      await nextStep();
    } else {
      // Skip service config if nothing selected
      await nextStep();
    }
  };

  // Group services by category
  const downloadServices = servicePlugins.filter((p) => p.category === 'download');
  const mediaServices = servicePlugins.filter((p) => p.category === 'media');
  const streamingServices = servicePlugins.filter((p) => p.category === 'streaming');

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

      {/* Download Services */}
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

      {/* Media Management */}
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

      {/* Streaming */}
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

      {/* Selection summary */}
      <div className="bg-card rounded-xl border border-border p-4 mb-8">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Selected services</p>
            <p className="text-lg font-semibold text-foreground">
              {selectedServices.length} of {servicePlugins.length}
            </p>
          </div>
          {selectedServices.length > 0 && (
            <div className="flex gap-2">
              {selectedServices.map((id) => {
                const plugin = servicePlugins.find((p) => p.id === id);
                if (!plugin) return null;
                const colors = getColorClasses(plugin);
                return (
                  <div
                    key={id}
                    className={`w-8 h-8 rounded-lg ${colors.bg} flex items-center justify-center`}
                    title={plugin.name}
                  >
                    <plugin.icon className={`w-4 h-4 ${colors.text}`} />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

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
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          data-testid="continue-button"
        >
          {selectedServices.length > 0 ? (
            <>
              Configure {selectedServices.length} Service{selectedServices.length > 1 ? 's' : ''}
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
