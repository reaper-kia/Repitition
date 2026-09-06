import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  loading?: boolean;
  children: ReactNode;
}

export function Button({ variant = 'primary', loading = false, className = '', disabled, children, ...props }: ButtonProps) {
  return (
    <button
      className={`button button--${variant} ${className}`.trim()}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span className="button__spinner" aria-hidden="true" />}
      {children}
    </button>
  );
}
