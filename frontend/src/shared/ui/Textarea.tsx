import { useId, type TextareaHTMLAttributes } from 'react';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export function Textarea({ label, error, id, className = '', ...props }: TextareaProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  return (
    <div className={`field ${className}`.trim()}>
      {label && <label htmlFor={inputId}>{label}</label>}
      <textarea id={inputId} className={error ? 'field__control field__control--error' : 'field__control'} {...props} />
      {error && <span className="field__error" role="alert">{error}</span>}
    </div>
  );
}
