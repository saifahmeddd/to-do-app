import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { login, loginWithGoogle, register } from '../../api/client.js';

const initialState = {
  mode: 'login',
  session: null,
  isSubmitting: false,
  error: '',
};

function errorMessage(error) {
  return error.message || 'Something went wrong.';
}

// createAsyncThunk runs the request and generates pending, fulfilled, and rejected actions.
export const authenticate = createAsyncThunk(
  'auth/authenticate',
  async (credentials, { getState, rejectWithValue }) => {
    try {
      // getState reads the latest mode without passing it through React props.
      const mode = getState().auth.mode;
      const request = mode === 'register' ? register : login;
      const session = await request(credentials);

      return {
        user_id: session.user_id,
        email: session.email,
        database: session.database,
        access_token: session.access_token,
      };
    } catch (error) {
      // rejectWithValue places a readable API error in the rejected action payload.
      return rejectWithValue(errorMessage(error));
    }
  },
);

export const authenticateWithGoogle = createAsyncThunk(
  'auth/authenticateWithGoogle',
  async (idToken, { rejectWithValue }) => {
    try {
      return await loginWithGoogle(idToken);
    } catch (error) {
      return rejectWithValue(errorMessage(error));
    }
  },
);

// createSlice groups auth state and reducers while generating matching action creators.
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    modeChanged(state, action) {
      state.mode = action.payload;
      state.error = '';
    },
    loggedOut(state) {
      state.session = null;
      state.error = '';
    },
  },
  // extraReducers handles lifecycle actions created outside the slice's normal reducers.
  extraReducers: builder => {
    builder
      .addCase(authenticate.pending, state => {
        state.isSubmitting = true;
        state.error = '';
      })
      .addCase(authenticate.fulfilled, (state, action) => {
        state.isSubmitting = false;
        state.session = action.payload;
      })
      .addCase(authenticate.rejected, (state, action) => {
        state.isSubmitting = false;
        state.error = action.payload || action.error.message;
      })
      .addCase(authenticateWithGoogle.pending, state => {
        state.isSubmitting = true;
        state.error = '';
      })
      .addCase(authenticateWithGoogle.fulfilled, (state, action) => {
        state.isSubmitting = false;
        state.session = {
          user_id: action.payload.user_id,
          email: action.payload.email,
          database: action.payload.database,
          access_token: action.payload.access_token,
        };
      })
      .addCase(authenticateWithGoogle.rejected, (state, action) => {
        state.isSubmitting = false;
        state.error = action.payload || action.error.message;
      });
  },
});

export const { modeChanged, loggedOut } = authSlice.actions;

// Selectors provide focused reads from the combined Redux state.
export const selectAuthMode = state => state.auth.mode;
export const selectSession = state => state.auth.session;
export const selectIsAuthenticating = state => state.auth.isSubmitting;
export const selectAuthError = state => state.auth.error;

export default authSlice.reducer;
