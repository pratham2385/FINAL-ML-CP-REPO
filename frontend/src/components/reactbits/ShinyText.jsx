import React from 'react';
import { cn } from '../../utils/cn';

/**
 * ShinyText (ReactBits component)
 * Text with a subtle moving metallic/iridescent shine.
 */
export function ShinyText({ text, disabled = false, speed = 4, className = '' }) {
  const animationDuration = `${speed}s`;

  return (
    <span
      className={cn(
        'inline-block bg-gradient-to-r from-slate-300 via-white to-slate-400 bg-[length:200%_auto] bg-clip-text text-transparent',
        !disabled && 'animate-shimmer',
        className
      )}
      style={{
        animationDuration,
      }}
    >
      {text}
    </span>
  );
}
