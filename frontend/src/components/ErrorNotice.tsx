export function ErrorNotice({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-xl border border-rose-400/30 bg-rose-500/10 p-4 text-sm text-rose-200">
      {message}
      {onRetry && (
        <button onClick={onRetry} className="ml-3 underline underline-offset-2 hover:text-white">
          Try again
        </button>
      )}
    </div>
  );
}
