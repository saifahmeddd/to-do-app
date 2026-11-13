import { configureStore } from '@reduxjs/toolkit';
import authReducer from '../features/auth/authSlice.js';
import tasksReducer from '../features/tasks/tasksSlice.js';
import uiReducer from '../features/ui/uiSlice.js';

// Hide the submitted password from Redux DevTools without storing a modified action.
function sanitizeAction(action) {
  if (action.type.startsWith('auth/authenticateWithGoogle/') && action.meta?.arg) {
    return { ...action, meta: { ...action.meta, arg: '[REDACTED]' } };
  }
  if (action.type.startsWith('auth/authenticateWithGitHub/') && action.meta?.arg) {
    return { ...action, meta: { ...action.meta, arg: '[REDACTED]' } };
  }
  if (!action.type.startsWith('auth/authenticate/') || !action.meta?.arg) {
    return action;
  }

  return {
    ...action,
    meta: {
      ...action.meta,
      arg: {
        ...action.meta.arg,
        password: '[REDACTED]',
      },
    },
  };
}

// configureStore combines the slices and includes thunk middleware.
export const store = configureStore({
  reducer: {
    auth: authReducer,
    tasks: tasksReducer,
    ui: uiReducer,
  },
  devTools: {
    actionSanitizer: sanitizeAction,
  },
});
