import { createContext, useContext, useState, useEffect } from 'react';
import { getStoredLanguage, setStoredLanguage } from '../utils/i18n';

const LocaleContext = createContext(null);

export function LocaleProvider({ children }) {
  const [language, setLanguage] = useState(() => getStoredLanguage());

  useEffect(() => {
    setStoredLanguage(language);
  }, [language]);

  const value = {
    language,
    setLanguage,
  };

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useLocale() {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error('useLocale must be used within LocaleProvider');
  }
  return context;
}
