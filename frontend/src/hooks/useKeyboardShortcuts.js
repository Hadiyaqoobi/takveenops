import { useEffect } from 'react';

export default function useKeyboardShortcuts(handlers) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      const tag = e.target.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || e.target.isContentEditable) {
        if (e.key === 'Escape') {
          e.target.blur();
          handlers.onEscape?.();
        }
        return;
      }

      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        handlers.onOpenPalette?.();
        return;
      }

      switch (e.key) {
        case 'c':
          e.preventDefault();
          handlers.onCreateTask?.();
          break;
        case '/':
          e.preventDefault();
          handlers.onOpenPalette?.();
          break;
        case '?':
          e.preventDefault();
          handlers.onShowHelp?.();
          break;
        case 'Escape':
          handlers.onEscape?.();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handlers]);
}
