import { writable } from 'svelte/store';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  duration?: number;
}

export const notifications = writable<Notification[]>([]);

export function addNotification(type: NotificationType, message: string, duration = 5000) {
  const id = crypto.randomUUID();
  notifications.update((n) => [...n, { id, type, message, duration }]);
  if (duration > 0) {
    setTimeout(() => {
      notifications.update((n) => n.filter((x) => x.id !== id));
    }, duration);
  }
  return id;
}

export function removeNotification(id: string) {
  notifications.update((n) => n.filter((x) => x.id !== id));
}

export function success(message: string) { return addNotification('success', message); }
export function error(message: string) { return addNotification('error', message); }
export function warning(message: string) { return addNotification('warning', message); }
export function info(message: string) { return addNotification('info', message); }
