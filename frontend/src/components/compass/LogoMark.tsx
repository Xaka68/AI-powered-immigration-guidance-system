interface LogoMarkProps {
  className?: string;
}

export function LogoMark({ className }: LogoMarkProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Thin outer ring */}
      <circle cx="12" cy="12" r="9.5" stroke="currentColor" strokeWidth="1.25" />
      {/* North needle — filled, solid */}
      <path d="M12 3.5L13.5 12H10.5L12 3.5Z" fill="currentColor" />
      {/* South needle — faded, secondary direction */}
      <path d="M12 20.5L13.5 12H10.5L12 20.5Z" fill="currentColor" fillOpacity="0.22" />
      {/* Pivot point */}
      <circle cx="12" cy="12" r="1.6" stroke="currentColor" strokeWidth="1.1" />
    </svg>
  );
}
