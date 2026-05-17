import { translations, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE } from '../locales/translations';

export function getStoredLanguage() {
  try {
    const stored = localStorage.getItem('flowboard_language');
    if (stored && SUPPORTED_LANGUAGES.includes(stored)) {
      return stored;
    }
  } catch {
    // localStorage not available
  }
  return DEFAULT_LANGUAGE;
}

export function setStoredLanguage(lang) {
  if (SUPPORTED_LANGUAGES.includes(lang)) {
    try {
      localStorage.setItem('flowboard_language', lang);
    } catch {
      // localStorage not available
    }
  }
}

export function t(key, locale = DEFAULT_LANGUAGE) {
  const lang = SUPPORTED_LANGUAGES.includes(locale) ? locale : DEFAULT_LANGUAGE;
  return translations[lang]?.[key] ?? translations[DEFAULT_LANGUAGE]?.[key] ?? key;
}

export function formatDate(date, locale = DEFAULT_LANGUAGE) {
  if (!date) return '';
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    
    if (locale === 'ru') {
      return new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      }).format(dateObj);
    }
    
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(dateObj);
  } catch {
    return '';
  }
}

export function formatDateTime(date, locale = DEFAULT_LANGUAGE) {
  if (!date) return '';
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    
    if (locale === 'ru') {
      return new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      }).format(dateObj);
    }
    
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(dateObj);
  } catch {
    return '';
  }
}

export function formatRelativeDate(dateStr, locale = DEFAULT_LANGUAGE) {
  if (!dateStr) return t('neverActivity', locale);
  
  const tKey = (key) => t(key, locale);
  const date = new Date(dateStr);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  
  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  
  if (dateOnly.getTime() === today.getTime()) {
    return tKey('today');
  }
  if (dateOnly.getTime() === yesterday.getTime()) {
    return tKey('yesterday');
  }
  if (dateOnly.getTime() === tomorrow.getTime()) {
    return tKey('tomorrow');
  }
  
  return formatDate(date, locale);
}

export function formatDuration(ms, locale = DEFAULT_LANGUAGE) {
  const tKey = (key) => t(key, locale);
  
  if (!Number.isFinite(ms) || ms <= 0) {
    return tKey('expiresIn') + ' 0 ' + tKey('minutesLeft');
  }
  
  const DAY_IN_MS = 24 * 60 * 60 * 1000;
  const HOUR_IN_MS = 60 * 60 * 1000;
  const MINUTE_IN_MS = 60 * 1000;
  
  const days = Math.floor(ms / DAY_IN_MS);
  const hours = Math.floor((ms % DAY_IN_MS) / HOUR_IN_MS);
  const minutes = Math.max(1, Math.floor((ms % HOUR_IN_MS) / MINUTE_IN_MS));
  
  if (days > 0) {
    return `${days} ${tKey('daysLeft')} ${hours}h`;
  }
  
  if (hours > 0) {
    return `${hours} ${tKey('hoursLeft')} ${minutes}m`;
  }
  
  return `${minutes} ${tKey('minutesLeft')}`;
}
