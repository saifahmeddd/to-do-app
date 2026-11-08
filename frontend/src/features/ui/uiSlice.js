import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { getRuntime } from '../../api/client.js';

export const loadActiveDatabase = createAsyncThunk(
  'ui/loadActiveDatabase',
  async () => {
    const runtime = await getRuntime();
    return runtime.database;
  },
);

const uiSlice = createSlice({
  name: 'ui',
  initialState: {
    theme: 'light',
    activeDatabase: 'loading',
  },
  reducers: {
    // This synchronous update needs no thunk because it performs no async work.
    themeToggled(state) {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
    },
  },
  extraReducers: builder => {
    builder
      .addCase(loadActiveDatabase.fulfilled, (state, action) => {
        state.activeDatabase = action.payload;
      })
      .addCase(loadActiveDatabase.rejected, state => {
        state.activeDatabase = 'unavailable';
      });
  },
});

export const { themeToggled } = uiSlice.actions;
export const selectTheme = state => state.ui.theme;
export const selectActiveDatabase = state => state.ui.activeDatabase;

export default uiSlice.reducer;
