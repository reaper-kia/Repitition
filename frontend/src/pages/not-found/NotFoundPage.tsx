import { Link } from 'react-router-dom';
import { useLanguage } from '../../app/providers/LanguageProvider';

export function NotFoundPage() {
  const { language, t } = useLanguage();
  return (
    <section className="not-found">
      <span>404</span>
      <h1>{language === 'ru' ? 'Страница не найдена' : 'Page not found'}</h1>
      <p>
        {language === 'ru'
          ? 'Возможно, ссылка устарела или адрес введён с ошибкой.'
          : 'The link may be outdated or the address mistyped.'}
      </p>
      <Link className="button button--primary" to="/">{t('home')}</Link>
    </section>
  );
}
