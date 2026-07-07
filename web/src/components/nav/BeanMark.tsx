export function BeanMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 48 48"
      className={className}
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
    >
      <ellipse cx="24" cy="24" rx="14" ry="20" fill="currentColor" opacity="0.9" />
      <path
        d="M24 6 C29 13 29 21 24 28 C19 35 19 40 24 42"
        stroke="var(--background)"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
    </svg>
  );
}
