export default function Button({ children, onClick, variant = "primary", className = "", ...rest }) {
  const base =
    "px-4 py-2 rounded-2xl text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-60";
  const styles =
    variant === "primary"
      ? "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-400"
      : "bg-neutral-200 text-neutral-900 hover:bg-neutral-300 dark:bg-neutral-800 dark:text-neutral-100 dark:hover:bg-neutral-700 focus:ring-neutral-400";
  return (
    <button className={`${base} ${styles} ${className}`} onClick={onClick} {...rest}>
      {children}
    </button>
  );
}
