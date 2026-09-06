import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

export type Language = 'ru' | 'en';

/**
 * Словарь переводов. Оставлены только универсальные ключи.
 * Добавляй свои под кейс — TypeScript сам подскажет, если забудешь
 * добавить ключ во второй язык.
 */
const dictionary = {
  ru: {
    home: 'Главная',
    admin: 'Админка',
    login: 'Войти',
    logout: 'Выйти',
    loading: 'Загрузка…',
    retry: 'Повторить',
    refresh: 'Обновить',
    save: 'Сохранить',
    cancel: 'Отмена',
    search: 'Поиск',
    details: 'Подробнее',
    status: 'Статус',
    all: 'Все',
    previous: 'Назад',
    next: 'Далее',
    name: 'Название',
    comment: 'Комментарий',
    optional: 'Необязательно',
    empty: 'Пока ничего нет',
  },
  en: {
    home: 'Home',
    admin: 'Admin',
    login: 'Sign in',
    logout: 'Log out',
    loading: 'Loading…',
    retry: 'Try again',
    refresh: 'Refresh',
    save: 'Save',
    cancel: 'Cancel',
    search: 'Search',
    details: 'Details',
    status: 'Status',
    all: 'All',
    previous: 'Previous',
    next: 'Next',
    name: 'Name',
    comment: 'Comment',
    optional: 'Optional',
    empty: 'Nothing here yet',
  },
} as const;

type TranslationKey = keyof typeof dictionary.ru;

interface LanguageContextValue {
  language: Language;
  setLanguage: (value: Language) => void;
  t: (key: TranslationKey) => string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() =>
    localStorage.getItem('app-language') === 'en' ? 'en' : 'ru',
  );

  const value = useMemo<LanguageContextValue>(() => ({
    language,
    setLanguage: (next) => {
      localStorage.setItem('app-language', next);
      setLanguageState(next);
    },
    t: (key) => dictionary[language][key],
  }), [language]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error('useLanguage must be used inside LanguageProvider');
  return context;
}
