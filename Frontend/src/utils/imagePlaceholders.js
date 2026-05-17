function encodeSvg(svg) {
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
}

function buildLayeredBackground(imageUrl, fallbackLayers) {
  if (!imageUrl) {
    return fallbackLayers.join(', ');
  }

  const safeUrl = imageUrl.replace(/"/g, '\\"');
  return [`url("${safeUrl}")`, ...fallbackLayers].join(', ');
}

const avatarPlaceholder = encodeSvg(`
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
    <circle cx="32" cy="24" r="12" fill="rgba(255,255,255,0.92)"/>
    <path d="M14 54c2.8-10.4 10.8-15.6 18-15.6S47.2 43.6 50 54" fill="rgba(255,255,255,0.92)"/>
  </svg>
`);

const boardPlaceholder = encodeSvg(`
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 72" fill="none">
    <rect x="11" y="14" width="50" height="44" rx="10" stroke="rgba(255,255,255,0.88)" stroke-width="4"/>
    <circle cx="26" cy="28" r="5" fill="rgba(255,255,255,0.88)"/>
    <path d="M20 48l10-10 8 8 8-11 10 13" stroke="rgba(255,255,255,0.88)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
`);

const boardGradient = 'linear-gradient(145deg, #6cc8d7 0%, #2f2f2a 100%)';

export function getAvatarSurfaceStyle(imageUrl, color) {
  return {
    backgroundColor: color || 'var(--surface-muted)',
    backgroundImage: buildLayeredBackground(imageUrl, [avatarPlaceholder]),
    backgroundPosition: 'center, center',
    backgroundRepeat: 'no-repeat, no-repeat',
    backgroundSize: 'cover, 62%',
  };
}

export function getBoardCoverStyle(imageUrl) {
  return {
    backgroundImage: buildLayeredBackground(imageUrl, [boardPlaceholder, boardGradient]),
    backgroundPosition: 'center, center, center',
    backgroundRepeat: 'no-repeat, no-repeat, no-repeat',
    backgroundSize: 'cover, 58%, cover',
  };
}
