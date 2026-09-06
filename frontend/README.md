# Frontend

React 19 + TypeScript + Vite. Структура по FSD.

```bash
npm install
npm run dev      # http://localhost:5173, проксирует API на localhost:8000
npm run build
npm run test     # vitest
npm run lint     # oxlint
```

```
src/
  app/        App, router, providers (тема, язык, тосты), global.css
  pages/      страницы-заглушки: home, login, admin, not-found
  widgets/    layout
  features/   auth (api + ProtectedRoute)
  shared/     api-клиент, ui-кит, утилиты, конфиг
```

Дизайн-токены (цвета, радиусы, тени, тёмная тема) — в `app/styles/global.css`
в блоках `:root` и `:root[data-theme="dark"]`. Меняй палитру там, компоненты
подхватят автоматически.

Новый URL-префикс бэкенда надо добавить в двух местах: `vite.config.ts` (dev)
и `nginx.local.conf` (docker), иначе запрос уйдёт в SPA вместо API.
Проксирование WebSocket на `/ws` уже настроено в обоих.
