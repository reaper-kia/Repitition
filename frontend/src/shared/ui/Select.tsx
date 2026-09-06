import { useId, type SelectHTMLAttributes } from 'react';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: Array<{ value: string; label: string }>;
}

export function Select({ label, options, id, className = '', ...props }: SelectProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  return (
    <div className={`field ${className}`.trim()}>
      {label && <label htmlFor={inputId}>{label}</label>}
      <select id={inputId} className="field__control" {...props}>
        {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
    </div>
  );
}
