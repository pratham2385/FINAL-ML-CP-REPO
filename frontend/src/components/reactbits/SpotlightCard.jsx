import React from 'react';
import { cn } from '../../utils/cn';

/**
 * SpotlightCard
 * Professional SOC console card container with quiet graphite surfaces and hairline borders.
 */
export function SpotlightCard({
  children,
  className,
  spotlightColor, // retained for prop compatibility
  ...props
}) {
  return (
    <div
      className={cn(
        'relative rounded-xl border border-white/[0.08] bg-[#14171b] p-5 transition-colors duration-150 hover:border-white/[0.14]',
        className
      )}
      {...props}
    >
      <div className="relative z-10">{children}</div>
    </div>
  );
}
