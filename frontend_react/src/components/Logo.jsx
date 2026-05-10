// RelayMed SVG Logo Icon Component
export function RelayMedIcon({ size = 32, className = '' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="20" cy="20" r="18" stroke="url(#logoGrad)" strokeWidth="1.5" fill="rgba(0,212,255,0.06)" />
      <path d="M6 20 L11 20 L13 14 L16 26 L19 18 L21 22 L23 20 L34 20" 
        stroke="#00D4FF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
        style={{ filter: 'drop-shadow(0 0 4px #00D4FF)' }} />
      <circle cx="34" cy="20" r="2.5" fill="#00D4FF" style={{ filter: 'drop-shadow(0 0 6px #00D4FF)' }} />
      <circle cx="6" cy="20" r="2.5" fill="#7C3AED" style={{ filter: 'drop-shadow(0 0 6px #7C3AED)' }} />
      <defs>
        <linearGradient id="logoGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop stopColor="#00D4FF" />
          <stop offset="1" stopColor="#7C3AED" />
        </linearGradient>
      </defs>
    </svg>
  );
}

// Full logo with text
export function RelayMedLogo({ size = 'md', className = '' }) {
  const iconSize = size === 'sm' ? 24 : size === 'lg' ? 44 : 32;
  const textClass = size === 'sm' ? 'text-lg' : size === 'lg' ? 'text-3xl' : 'text-xl';
  return (
    <div className={`flex items-center gap-2 ${className}`} style={{ userSelect: 'none' }}>
      <RelayMedIcon size={iconSize} />
      <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 800 }} className={`text-white ${textClass}`}>
        Relay<span style={{ color: '#00D4FF', textShadow: '0 0 20px rgba(0,212,255,0.5)' }}>Med</span>
      </span>
    </div>
  );
}
