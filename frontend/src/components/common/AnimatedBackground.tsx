import React from 'react';

export interface AnimatedBackgroundProps {
  variant?: 'login' | 'dashboard';
  className?: string;
  isFixed?: boolean;
}

/**
 * AnimatedBackground: Renders the flowing Aurora multicolor animated background
 * on the Login page only. Other pages (such as Dashboard) use plain, static backgrounds.
 */
export const AnimatedBackground: React.FC<AnimatedBackgroundProps> = ({
  variant = 'login',
  className = '',
  isFixed = true,
}) => {
  // Only the login page has an animated background as strictly required
  if (variant !== 'login') {
    return null;
  }

  const positioning = isFixed ? 'fixed inset-0 z-0' : 'absolute inset-0 z-0';

  return (
    <div
      className={`${positioning} overflow-hidden pointer-events-none select-none ${className}`}
      aria-hidden="true"
    >
      {/* Ambient Canvas Base */}
      <div className="absolute inset-0 bg-slate-100/90 dark:bg-[#030712] transition-colors duration-500" />

      {/* Subtle mesh background gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(59,130,246,0.12),transparent)] dark:bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(37,99,235,0.22),transparent)]" />

      {/* Aurora Shape 1: Electric Blue & Cyan Flow */}
      <div className="absolute -top-[10%] -left-[10%] w-[68vw] h-[68vw] max-w-[850px] max-h-[850px] rounded-full animate-aurora-1 aurora-shape-1 blur-[90px] md:blur-[120px]" />

      {/* Aurora Shape 2: Violet & Purple Undulation */}
      <div className="absolute -top-[5%] -right-[10%] w-[62vw] h-[62vw] max-w-[800px] max-h-[800px] rounded-full animate-aurora-2 aurora-shape-2 blur-[95px] md:blur-[130px]" />

      {/* Aurora Shape 3: Subtle Magenta / Fuchsia Warm Accent */}
      <div className="absolute -bottom-[15%] left-[25%] w-[55vw] h-[55vw] max-w-[700px] max-h-[700px] rounded-full animate-aurora-3 aurora-shape-3 blur-[85px] md:blur-[115px]" />

      {/* Aurora Shape 4: Luminous Cyan Ribbon */}
      <div className="absolute bottom-[5%] -left-[15%] w-[52vw] h-[52vw] max-w-[650px] max-h-[650px] rounded-full animate-aurora-4 aurora-shape-4 blur-[80px] md:blur-[110px]" />

      {/* Soft Vignette Overlay */}
      <div className="absolute inset-0 bg-radial from-transparent via-slate-100/20 to-slate-100/50 dark:via-[#030712]/20 dark:to-[#030712]/60 pointer-events-none" />
    </div>
  );
};
