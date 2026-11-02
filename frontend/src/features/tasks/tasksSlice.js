import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import {
  ApiError,
  completeTask as completeTaskRequest,
  createTask as createTaskRequest,
  deleteTask as deleteTaskRequest,
  listTasks,
  renameTask as renameTaskRequest,
} from '../../api/client.js';

const initialState = {
  items: [],
  isLoading: false,
  isCreating: false,
  busyTaskId: null,
  error: '',
};

function errorMessage(error) {
  if (error instanceof ApiError && error.status === 401) {
    return 'Your session is invalid or expired. Log in again.';
  }

  return error.message || 'Something went wrong.';
}

function createApiThunk(type, request) {
  return createAsyncThunk(type, async (argument, { getState, rejectWithValue }) => {
    try {
      const token = getState().auth.session.id_token;
      return await request(argument, token);
    } catch (error) {
      return rejectWithValue(errorMessage(error));
    }
  });
}

export const loadTasks = createAsyncThunk(
  'tasks/loadTasks',
  async (_, { getState, rejectWithValue, signal }) => {
    try {
      const token = getState().auth.session.id_token;
      const data = await listTasks(token, signal);
      return data.tasks;
    } catch (error) {
      // Let createAsyncThunk recognize cancellations instead of treating them as API errors.
      if (error.name === 'AbortError') throw error;
      return rejectWithValue(errorMessage(error));
    }
  },
);

export const createTask = createApiThunk(
  'tasks/createTask',
  (title, token) => createTaskRequest(title, token),
);

export const completeTask = createApiThunk(
  'tasks/completeTask',
  (id, token) => completeTaskRequest(id, token),
);

export const renameTask = createApiThunk(
  'tasks/renameTask',
  ({ id, title }, token) => renameTaskRequest(id, title, token),
);

export const deleteTask = createApiThunk(
  'tasks/deleteTask',
  async (id, token) => {
    await deleteTaskRequest(id, token);
    return id;
  },
);

function replaceTask(state, updatedTask) {
  state.items = state.items.map(task => task.id === updatedTask.id ? updatedTask : task);
}

function taskUpdateRejected(state, action) {
  state.busyTaskId = null;
  state.error = action.payload || action.error.message;
}

// Redux Toolkit uses Immer so these reducer mutations still produce immutable state.
const tasksSlice = createSlice({
  name: 'tasks',
  initialState,
  reducers: {
    tasksCleared: () => initialState,
  },
  extraReducers: builder => {
    builder
      .addCase(loadTasks.pending, state => {
        state.isLoading = true;
        state.error = '';
      })
      .addCase(loadTasks.fulfilled, (state, action) => {
        state.isLoading = false;
        state.items = action.payload;
      })
      .addCase(loadTasks.rejected, (state, action) => {
        state.isLoading = false;
        // Intentional effect cleanup should stop loading without showing an error.
        if (!action.meta.aborted) {
          state.error = action.payload || action.error.message;
        }
      })
      .addCase(createTask.pending, state => {
        state.isCreating = true;
        state.error = '';
      })
      .addCase(createTask.fulfilled, (state, action) => {
        state.isCreating = false;
        state.items.push(action.payload);
      })
      .addCase(createTask.rejected, (state, action) => {
        state.isCreating = false;
        state.error = action.payload || action.error.message;
      })
      // meta.arg contains the original thunk input used to identify the busy task.
      .addCase(completeTask.pending, (state, action) => {
        state.busyTaskId = action.meta.arg;
        state.error = '';
      })
      .addCase(completeTask.fulfilled, (state, action) => {
        state.busyTaskId = null;
        replaceTask(state, action.payload);
      })
      .addCase(completeTask.rejected, taskUpdateRejected)
      .addCase(renameTask.pending, (state, action) => {
        state.busyTaskId = action.meta.arg.id;
        state.error = '';
      })
      .addCase(renameTask.fulfilled, (state, action) => {
        state.busyTaskId = null;
        replaceTask(state, action.payload);
      })
      .addCase(renameTask.rejected, taskUpdateRejected)
      .addCase(deleteTask.pending, (state, action) => {
        state.busyTaskId = action.meta.arg;
        state.error = '';
      })
      .addCase(deleteTask.fulfilled, (state, action) => {
        state.busyTaskId = null;
        state.items = state.items.filter(task => task.id !== action.payload);
      })
      .addCase(deleteTask.rejected, taskUpdateRejected);
  },
});

export const { tasksCleared } = tasksSlice.actions;

export const selectTasks = state => state.tasks.items;
export const selectIsLoadingTasks = state => state.tasks.isLoading;
export const selectIsCreating = state => state.tasks.isCreating;
export const selectBusyTaskId = state => state.tasks.busyTaskId;
export const selectTaskError = state => state.tasks.error;
export const selectPendingCount = state => (
  state.tasks.items.filter(task => !task.completed_at).length
);

export default tasksSlice.reducer;
