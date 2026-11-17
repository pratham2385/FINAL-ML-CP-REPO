import React from 'react';

/**
 * DecryptedText
 * High-integrity display component: renders text directly and stably without gimmick text-scrambling.
 */
export function DecryptedText({ text = '', className = '' }) {
  return <span className={className}>{text}</span>;
}
