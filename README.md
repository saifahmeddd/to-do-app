# To-Do App

A learning project that pairs a Python TODO API built with Domain-Driven Design
(DDD) and Onion Architecture with a React frontend managed by Redux Toolkit.
The API uses Firebase Authentication for identity and Cloud Firestore for
owner-scoped task storage.

## Features

- Register and log in with email and password.
- Create, list, rename, complete, and delete tasks.
- Keep each user's tasks isolated using the verified Firebase identity.
- Manage frontend auth, tasks, and theme state with Redux Toolkit.
- Demonstrate domain, application, presentation, and infrastructure boundaries.
- Include a separate `MVC/` implementation for architectural comparison.

## Project layout

```text
.
├── DDD/       Python API using DDD and Onion Architecture
├── frontend/  React, Vite, and Redux Toolkit application
├── MVC/       MVC reference implementation
└── .vscode/   Shared VS Code launch configurations
```

## Architecture

### Backend

The DDD API separates business rules from delivery and vendor details:

```text
Presentation → Application → Domain
Infrastructure → Application/Domain interfaces
Composition root → wires concrete implementations together
```

- **Presentation** handles HTTP routes, authentication middleware, validation,
  controllers, and JSON responses.
- **Application** coordinates use cases and defines the interfaces it needs.
- **Domain** contains task rules, entities, value objects, and domain events.
- **Infrastructure** implements Firebase Auth, Firestore, time, IDs, and logging.
- **Composition root** (`DDD/bootstrap.py`) assembles the application.

### Frontend

The frontend uses Redux Toolkit for shared state and React local state for
temporary form input.

```text
React component → dispatch/thunk → API client → Python API
       ↑                                      │
       └── useSelector ← Redux reducer ← response
```

Authentication, tasks, and theme are registered in `frontend/src/store/store.js`.
Async requests use `createAsyncThunk`; its `pending`, `fulfilled`, and
`rejected` actions update state in each feature slice. The HTTP boundary is
`frontend/src/api/client.js`.

See [frontend/README.md](frontend/README.md) for the Redux flow and frontend
setup details. The DDD backend's architecture and API notes are in
[`DDD/README.md`](DDD/README.md).

## Requirements

- Python 3.10 or newer
- Node.js and npm
- A Firebase project with Email/Password Authentication enabled
- A Firebase service account permitted to access Cloud Firestore
- Firebase Web API key for the backend's register and login use cases

## Configuration

The backend reads configuration from environment variables. Create a local
`DDD/.env` file (it is ignored by Git) with:

```dotenv
FIREBASE_WEB_API_KEY=your-firebase-web-api-key
FIREBASE_PROJECT_ID=your-firebase-project-id
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
```

Keep the service-account JSON and `.env` private. Never commit credentials,
ID tokens, or secret values. A local service-account file may instead be kept
at `DDD/.secrets/firebase-service-account.json`; `.secrets/` is ignored.

## Run locally

### 1. Start the API

```bash
cd DDD
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
set -a
source .env
set +a
python main.py
```

The API listens at `http://127.0.0.1:8000` by default.

### 2. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite forwards `/auth` and `/tasks` requests to the
local API on port `8000` during development.

## API overview

Registration and login are public. Task routes require a Firebase ID token in
the `Authorization: Bearer <ID_TOKEN>` header.

| Method | Path | Description | Auth required |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | Register an account | No |
| `POST` | `/auth/login` | Log in | No |
| `POST` | `/tasks` | Create a task | Yes |
| `GET` | `/tasks` | List the current user's tasks | Yes |
| `GET` | `/tasks/{id}` | Get one owned task | Yes |
| `PATCH` | `/tasks/{id}` | Rename an owned task | Yes |
| `POST` | `/tasks/{id}/complete` | Complete an owned task | Yes |
| `DELETE` | `/tasks/{id}` | Delete an owned task | Yes |

Create and rename requests use a JSON body such as:

```json
{"title": "Learn Redux"}
```

The backend derives ownership from the verified token; clients cannot assign a
task to another user by sending an owner ID.

## Tests and build

Run backend tests from the `DDD/` directory:

```bash
python -m unittest discover -s tests -v
```

Build the frontend from the `frontend/` directory:

```bash
npm run build
```

## Security notes

- Do not commit `.env`, `.secrets/`, service-account JSON files, or tokens.
- The frontend sends the Firebase ID token to the API; the backend verifies it.
- Authorization and task ownership are enforced by the backend, not trusted to
  frontend state.
- The frontend store is currently in-memory, so refreshing resets its session,
  task list, and theme state.
