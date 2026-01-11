// components/ui/Toaster.tsx - Toast provider with glassmorphism styling
import { Toaster as SonnerToaster } from 'sonner';

export function Toaster() {
  return (
    <SonnerToaster
      position="bottom-right"
      offset={16}
      gap={8}
      toastOptions={{
        unstyled: true,
        classNames: {
          toast:
            'flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-xl shadow-lg bg-[rgba(255,255,255,0.03)] border-[rgba(255,255,255,0.06)]',
          title: 'text-sm font-medium text-zinc-100',
          description: 'text-xs text-zinc-400',
          actionButton:
            'px-2 py-1 rounded-md text-xs font-medium bg-indigo-500 text-white hover:bg-indigo-400',
          cancelButton:
            'px-2 py-1 rounded-md text-xs font-medium bg-zinc-800 text-zinc-300 hover:bg-zinc-700',
          closeButton:
            'p-1 rounded-md text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800',
          error: 'border-l-2 border-l-red-500',
          success: 'border-l-2 border-l-green-500',
          warning: 'border-l-2 border-l-yellow-500',
          info: 'border-l-2 border-l-blue-500',
        },
      }}
    />
  );
}
