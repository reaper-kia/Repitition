import { Component, type ErrorInfo, type ReactNode } from 'react';

interface State { hasError: boolean }

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Unhandled UI error', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="fatal-error">
          <h1>Что-то пошло не так</h1>
          <p>Обновите страницу. Если ошибка повторится, попробуйте ещё раз позже.</p>
          <button className="button button--primary" onClick={() => window.location.reload()}>
            Обновить страницу
          </button>
        </main>
      );
    }
    return this.props.children;
  }
}
