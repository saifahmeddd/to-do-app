# TODO App Frontend

This React application is the user interface for the Python TODO API in `DDD/`.
It uses Redux Toolkit for shared application state. The browser does not connect
directly to MongoDB, PostgreSQL, or Firestore; it sends HTTP requests to the
backend.

## What the app can do

- Register and log in with an email and password.
- Sign in with Google.
- Create, list, rename, complete, and delete the signed-in user's tasks.
- Show which database the backend is currently using.
- Switch between light and dark themes.

## Run locally

Start the backend first, then configure and start the frontend:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open the URL printed by Vite (normally `http://127.0.0.1:5173`). Vite forwards
`/auth`, `/tasks`, and `/runtime` to the Python API. Set
`BACKEND_PROXY_TARGET` in `frontend/.env` if the API is listening somewhere
else. The default is `http://127.0.0.1:8000`.

### Google sign-in configuration

Create a Google OAuth client of type **Web application**. For local development,
add the frontend origin you use in the browser as an authorized JavaScript
origin, for example `http://127.0.0.1:5173`. Put the same client ID in both
`frontend/.env` and `DDD/.env`:

```env
# frontend/.env
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com

# DDD/.env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

The client ID is public configuration, not a client secret. The backend uses it
to verify that a Google ID token was issued for this application. For local
work, Google Audience can remain External/Testing; publishing in production
requires a public homepage and privacy policy on a domain you control.

## Redux state and local component state

The store is created in `src/store/store.js` and registers three reducers:

```js
{
  auth: { mode, session, isSubmitting, error },
  tasks: { items, isLoading, isCreating, busyTaskId, error },
  ui: { theme, activeDatabase }
}
```

Shared application data, such as the session and saved tasks, lives in Redux.
Short-lived form values, such as the email, password, and draft task title, stay
in their React components with `useState`. The Redux store is memory-only, so
refreshing the page clears the session and task state.

## Google authentication flow

```text
GoogleSignInButton.jsx gets a Google ID token
        |
        v
AuthForm.jsx -> App.jsx dispatches authenticateWithGoogle(token)
        |
        v
authSlice.js -> api/client.js -> POST /auth/google
        |
        v
Python verifies Google's token, finds/creates the database user,
and returns the app's own JWT session
        |
        v
Redux stores the app session; later task calls use the app JWT
```

These are two different tokens with different jobs:

- **Google ID token:** proves the Google identity to the backend during sign-in.
- **App JWT:** issued by the backend after verification and sent with protected
  task requests as `Authorization: Bearer <token>`.

The frontend does not use Firebase Authentication. Firebase Admin is used by
the backend only when Firestore is the selected database.

## Redux request flow

```text
User action -> React component -> App dispatches thunk
            -> thunk calls api/client.js -> backend response
            -> slice handles pending/fulfilled/rejected
            -> useSelector reads updated state -> React re-renders
```

`createAsyncThunk` makes `pending`, `fulfilled`, and `rejected` actions.
`extraReducers` handles those actions and updates loading, data, and error
state. The task thunks use `getState()` to read the current app JWT rather than
passing it through component props. `loadTasks` also accepts an abort signal so
the `App.jsx` effect can cancel an outdated request.

`unwrap()` in `App.jsx` turns a dispatched task thunk into a normal Promise,
letting a form clear or close only after a successful request. Synchronous
theme changes use a normal slice action and do not call the API.

## API calls made by this frontend

| Request | Purpose |
| --- | --- |
| `POST /auth/register` | Register with email and password |
| `POST /auth/login` | Log in with email and password |
| `POST /auth/google` | Exchange a Google ID token for an app session |
| `GET /runtime` | Read the backend's active database for the indicator |
| `GET /tasks` | Load the signed-in user's tasks |
| `POST /tasks` | Create a task |
| `PATCH /tasks/{id}` | Rename an owned task |
| `POST /tasks/{id}/complete` | Complete an owned task |
| `DELETE /tasks/{id}` | Delete an owned task |

The backend supplies the owner identity from the verified JWT. The frontend
does not submit an `owner_id` for task operations.

## Important files

```text
src/
├── main.jsx                       Mounts React and provides the Redux store
├── App.jsx                        Connects Redux state and callbacks to the UI
├── api/client.js                  Sends HTTP requests to the Python API
├── store/store.js                 Configures Redux and DevTools action sanitizing
├── features/
│   ├── auth/authSlice.js           Auth thunks, session state, and selectors
│   ├── tasks/tasksSlice.js         Task thunks, task state, and selectors
│   └── ui/uiSlice.js               Theme and active-database state
└── components/
    ├── AuthForm.jsx                Email/password form and Google button placement
    ├── GoogleSignInButton.jsx      Loads Google Identity Services and gets ID token
    ├── DatabaseIndicator.jsx       Shows the backend-selected database
    ├── AppHeader.jsx               Shows account, theme, and logout controls
    ├── TaskForm.jsx                Creates a task
    ├── TaskList.jsx                Renders the task collection
    └── TaskItem.jsx                Renders one task and its actions
```

## Commands

```bash
npm run dev      # Start the Vite development server
npm run lint     # Check frontend code with ESLint
npm run build    # Create a production build in dist/
npm run preview  # Preview the production build locally
```
