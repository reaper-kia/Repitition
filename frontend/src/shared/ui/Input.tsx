import { useId, type InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export function Input({ label, error, hint, id, className = '', ...props }: InputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  return (
    <div className={`field ${className}`.trim()}>
      {label && <label htmlFor={inputId}>{label}{props.required && <span aria-hidden="true"> *</span>}</label>}
      <input id={inputId} className={error ? 'field__control field__control--error' : 'field__control'} {...props} />
      {error ? <span className="field__error" role="alert">{error}</span> : hint && <span className="field__hint">{hint}</span>}
    </div>
  );
}
