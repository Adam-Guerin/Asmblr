import { useToast } from '@/components/ui/use-toast';
import {
  ToastProvider as ToastRoot,
  ToastViewport,
  Toast,
  ToastTitle,
  ToastDescription,
  ToastClose,
} from '@/components/ui/toast';

function ToastList() {
  const { toasts, dismissToast } = useToast();
  return (
    <>
      {toasts.map((toast) => (
        <Toast key={toast.id}>
          <div className="flex-1">
            <ToastTitle>{toast.title}</ToastTitle>
            {toast.description ? <ToastDescription>{toast.description}</ToastDescription> : null}
          </div>
          <ToastClose onClick={() => dismissToast(toast.id)}>Close</ToastClose>
        </Toast>
      ))}
      <ToastViewport />
    </>
  );
}

export function Toaster() {
  return (
    <ToastRoot>
      <ToastList />
    </ToastRoot>
  );
}
