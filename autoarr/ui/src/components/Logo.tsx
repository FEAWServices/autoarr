import logoImage from '../assets/autoarr-logo.png';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export const Logo = ({ size = 'md', className = '' }: LogoProps) => {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-20 h-20',
    xl: 'w-32 h-32',
  };

  return (
    <div className={`${sizeClasses[size]} ${className}`}>
      <img src={logoImage} alt="AutoArr Logo" className="w-full h-full object-contain" />
    </div>
  );
};
