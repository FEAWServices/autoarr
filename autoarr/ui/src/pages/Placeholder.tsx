import { LucideIcon } from 'lucide-react';

interface PlaceholderProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

export const Placeholder = ({ icon: Icon, title, description }: PlaceholderProps) => {
  return (
    <div className="flex items-center justify-center h-full p-12">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <Icon className="w-10 h-10 text-gray-400" />
        </div>
        <h2 className="text-2xl font-semibold text-white mb-3">{title}</h2>
        <p className="text-gray-400">{description}</p>
        <div className="mt-8">
          <span className="inline-block px-4 py-2 bg-gray-800 text-gray-500 rounded-lg text-sm">
            Coming Soon
          </span>
        </div>
      </div>
    </div>
  );
};
