import { Link } from 'react-router-dom';

/**
 * Заглушка главной страницы. Замени содержимое под кейс.
 * Классы hero/container/button уже описаны в global.css.
 */
export function HomePage() {
  return (
    <section className="container hero">
      <div className="hero__content">
        <p className="eyebrow">Hackathon template</p>
        <h1>Каркас готов к работе</h1>
        <p>
          Авторизация, кэш, событийная шина, миграции и деплой уже настроены.
          Замени эту страницу на главный экран своего продукта.
        </p>
        <div className="hero__actions">
          <Link className="button button--primary" to="/login">Войти</Link>
        </div>
      </div>
    </section>
  );
}
