import { forwardRef, type InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  // Explicit `| undefined` re-permits undefined props under exactOptionalPropertyTypes
  // (react-hook-form passes `errors.field?.message`, i.e. string | undefined).
  label?: string | undefined;
  error?: string | undefined;
  fieldClassName?: string | undefined;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, fieldClassName = "", className = "", id, ...rest }, ref) => {
    const fieldId = id ?? rest.name;
    return (
      <div className={`flex flex-col gap-1 ${fieldClassName}`}>
        {label && (
          <label htmlFor={fieldId} className="font-body text-label-sm uppercase tracking-[0.14em] text-stone">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={fieldId}
          aria-invalid={error ? true : undefined}
          className={`bg-transparent text-ink font-body text-body-md border-0 border-t border-b border-hairline px-0 py-3 outline-none focus:border-b-2 focus:border-b-signal transition-colors placeholder:text-stone ${className}`}
          {...rest}
        />
        {error && (
          <p className="font-mono text-mono-sm text-signal mt-1" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  },
);
Input.displayName = "Input";
