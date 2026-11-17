import React from 'react';
import { ShieldCheck, AlertTriangle, ShieldAlert, AlertOctagon } from 'lucide-react';
import { getThreatTierConfig } from '../../utils/formatters';
import { cn } from '../../utils/cn';

export function ThreatBadge({ threatLevel, showIcon = true, size = 'md', className }) {
  const config = getThreatTierConfig(threatLevel);
  const level = (threatLevel || '').toUpperCase();

  const getIcon = () => {
    const iconClass = size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5';
    switch (level) {
      case 'MALICIOUS':
      case 'CRITICAL':
        return <AlertOctagon className={iconClass} />;
      case 'HIGH':
        return <ShieldAlert className={iconClass} />;
      case 'SUSPICIOUS':
      case 'MEDIUM':
      case 'LOW_SUSPICIOUS':
        return <AlertTriangle className={iconClass} />;
      case 'SAFE':
      default:
        return <ShieldCheck className={iconClass} />;
    }
  };

  const sizeClasses = size === 'sm' 
    ? 'text-[11px] px-1.5 py-0.5 gap-1' 
    : size === 'lg' 
    ? 'text-xs px-2.5 py-1 gap-1.5 font-medium' 
    : 'text-xs px-2 py-0.5 gap-1.5 font-medium';

  return (
    <span
      className={cn(
        'inline-flex items-center rounded border font-medium',
        config.badge,
        sizeClasses,
        className
      )}
    >
      {showIcon && getIcon()}
      <span>{config.label}</span>
    </span>
  );
}
