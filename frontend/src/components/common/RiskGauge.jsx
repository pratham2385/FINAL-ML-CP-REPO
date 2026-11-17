import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

export function RiskGauge({ score = 0, size = 100, strokeWidth = 8, className }) {
  const normalizedScore = Math.min(Math.max(Number(score) || 0, 0), 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  const getColor = (s) => {
    if (s >= 75) return '#cf222e'; // Red (Critical)
    if (s >= 50) return '#da3633'; // Rose/High
    if (s >= 35) return '#d29922'; // Amber (Medium)
    if (s >= 20) return '#bb8009'; // Low Suspicious
    return '#2da44e';              // Emerald (Safe)
  };

  const currentColor = getColor(normalizedScore);

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        {/* Background Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        {/* Progress Arc */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={currentColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          strokeLinecap="round"
          fill="transparent"
        />
      </svg>
      {/* Center Label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-xl font-semibold font-mono tabular-nums leading-none" style={{ color: currentColor }}>
          {normalizedScore.toFixed(0)}
        </span>
        <span className="text-[10px] text-slate-400 font-medium mt-1">Risk score</span>
      </div>
    </div>
  );
}
