import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

type FieldVariant = "default" | "compact";

type CustomFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  variant?: FieldVariant;
};

type CustomTextAreaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  variant?: FieldVariant;
};

export function CustomField({ className = "", variant = "default", type = "text", ...props }: CustomFieldProps) {
  return (
    <input
      {...props}
      type={type}
      className={`custom-field ${variant === "compact" ? "compact" : ""} ${className}`.trim()}
    />
  );
}

export function CustomTextArea({ className = "", variant = "default", ...props }: CustomTextAreaProps) {
  return <textarea {...props} className={`custom-field custom-field-textarea ${variant === "compact" ? "compact" : ""} ${className}`.trim()} />;
}
