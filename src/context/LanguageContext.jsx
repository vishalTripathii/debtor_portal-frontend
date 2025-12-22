import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations } from '../translations';

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    // Try to get saved language from localStorage
    const savedLanguage = localStorage.getItem('appLanguage');
    return savedLanguage || 'th';
  });

  // Save language preference to localStorage
  useEffect(() => {
    localStorage.setItem('appLanguage', language);
  }, [language]);

  const t = (key) => {
    return translations[language]?.[key] || translations['en']?.[key] || key;
  };

  const toggleLanguage = () => {
    setLanguage(prev => prev === 'en' ? 'th' : 'en');
  };

  const changeLanguage = (lang) => {
    if (translations[lang]) {
      setLanguage(lang);
    }
  };

  return (
    <LanguageContext.Provider value={{
      language,
      setLanguage: changeLanguage,
      toggleLanguage,
      t,
      translations: translations[language] || translations['en']
    }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

export default LanguageContext;
