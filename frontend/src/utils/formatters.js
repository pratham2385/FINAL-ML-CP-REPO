/**
 * Utilities for formatting dates, percentages, and threat visual classes.
 * Follows clean SOC console tokens with quiet neutral backgrounds and restrained semantic indicators.
 */

export function formatDate(isoString) {
  if (!isoString) return '—';
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return isoString;
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(date);
  } catch {
    return isoString;
  }
}

export function formatPercent(val) {
  if (val === undefined || val === null) return '0.0%';
  const num = typeof val === 'number' ? val : parseFloat(val);
  return `${num.toFixed(1)}%`;
}

export function getThreatTierConfig(threatLevel) {
  const level = (threatLevel || '').toUpperCase();
  switch (level) {
    case 'MALICIOUS':
    case 'CRITICAL':
      return {
        bg: 'bg-[#1a1416] border-[#cf222e]/40 text-[#ff8182]',
        badge: 'bg-[#cf222e]/15 text-[#ff8182] border border-[#cf222e]/40',
        color: '#cf222e',
        label: level === 'MALICIOUS' ? 'Malicious' : 'Critical'
      };
    case 'HIGH':
      return {
        bg: 'bg-[#1a1417] border-[#da3633]/35 text-[#ff7b72]',
        badge: 'bg-[#da3633]/15 text-[#ff7b72] border border-[#da3633]/35',
        color: '#da3633',
        label: 'High Risk'
      };
    case 'SUSPICIOUS':
    case 'MEDIUM':
      return {
        bg: 'bg-[#181612] border-[#d29922]/35 text-[#e3b341]',
        badge: 'bg-[#d29922]/15 text-[#e3b341] border border-[#d29922]/35',
        color: '#d29922',
        label: level === 'SUSPICIOUS' ? 'Suspicious' : 'Medium Risk'
      };
    case 'LOW_SUSPICIOUS':
      return {
        bg: 'bg-[#161511] border-[#bb8009]/30 text-[#d29922]',
        badge: 'bg-[#bb8009]/15 text-[#d29922] border border-[#bb8009]/30',
        color: '#bb8009',
        label: 'Low Suspicious'
      };
    case 'SAFE':
    default:
      return {
        bg: 'bg-[#101713] border-[#2da44e]/35 text-[#56d364]',
        badge: 'bg-[#2da44e]/15 text-[#56d364] border border-[#2da44e]/35',
        color: '#2da44e',
        label: 'Safe'
      };
  }
}
