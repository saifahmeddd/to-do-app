# TODO API: DDD and Onion Architecture

This folder contains the Python backend for the TODO application. It uses
Domain-Driven Design (DDD) to keep task rules in a domain model and Onion
Architecture to keep HTTP and database details outside the application core.

The backend supports email/password authentication, Google and GitHub sign-in,
and task CRUD. It issues its own JWT after successful authentication. Firebase
Authentication is not used; Firebase Admin is used to connect to Firestore
when Firestore is selected.

## Architecture

```mermaid
flowchart LR
    P[Presentation: HTTP, routes, validation] --> A[Application: use cases and ports]
    A --> D[Domain: task rules and values]
    I[Infrastructure: databases, JWT, Google, system adapters] -. implements ports .-> A
    C[main.py and bootstrap.py: wiring] --> P
    C --> A
    C --> I
```

- **Presentation** accepts HTTP requests, validates their shape, routes them,
  and returns JSON.
- **Application** coordinates actions such as login and create-task. It defines
  interfaces (ports) for the capabilities it needs.
- **Domain** contains task entities, validated values, and business behavior.
- **Infrastructure** implements ports using databases, Google token
  verification, JWT, the system clock, UUIDs, and logging.
- **`main.py` and `bootstrap.py`** load configuration and connect the concrete
  infrastructure adapters to application services.
- **Task reminders** use the same task and user repositories. A daily external
  cron invokes `scripts/send_task_reminders.py`; the script sends due-tomorrow
  mail through the Resend adapter and records successful sends.

## Authentication

### Email and password

`POST /auth/register` stores a user in the selected database. Passwords are
hashed with Argon2id by `Argon2PasswordHasher`; the plain password is not stored.
`POST /auth/login` checks the submitted password against that hash.

### Google sign-in

```text
Google Identity Services in frontend
    -> sends Google ID token to POST /auth/google
    -> backend verifies signature, issuer, audience, expiry, verified email
    -> AuthService finds or creates the user in the selected database
    -> backend issues this app's JWT session
```

The Google ID token proves identity to the backend during sign-in. The backend
then issues a separate app JWT. The frontend sends the app JWT with protected
task requests; it does not send the Google token for task access.

### GitHub sign-in

GitHub uses the OAuth authorization-code flow. The frontend generates and
checks a one-time `state` value, then sends the short-lived authorization code
to the backend. The backend exchanges it using the GitHub client secret,
retrieves the GitHub account and its primary verified email, and issues this
app's JWT. GitHub access tokens are not stored. Only the `read:user` and
`user:email` scopes are requested. GitHub identity subjects are persisted
separately from Google subjects; matching email addresses are not linked
automatically.

The Google identity is looked up by Google's stable `sub` value. If an email
already belongs to a password account, the app does not automatically link the
accounts. GitHub identities are stored separately by their immutable numeric
GitHub user ID, and matching email addresses are also not linked automatically.
Account linking is not implemented.

### Protected requests

Task requests include:

```http
Authorization: Bearer <app JWT>
```

`presentation/middleware/authentication.py` extracts the bearer token.
`JwtTokenService` checks its signature, expiration, issuer, required claims, and
database audience. The verified user ID is passed to task use cases and used as
the task owner. A missing or invalid token returns `401`; a task belonging to
another user is treated as not found (`404`).

The app JWT has a database-specific audience (`tasks:<database>`). Restart the
backend after changing `TASK_DATABASE`; users and tasks are not copied between
databases.

## Database selection

Set one `TASK_DATABASE` value in `DDD/.env`:

```env
TASK_DATABASE=firestore
# or mongodb
# or postgres
```

At startup, `bootstrap.py` builds both the user repository and task repository
for that same database:

| `TASK_DATABASE` | User storage | Task storage |
| --- | --- | --- |
| `firestore` | Firestore `users` collection | Firestore `tasks` collection |
| `mongodb` | `users` collection in `MONGODB_DATABASE` | `tasks` collection in `MONGODB_DATABASE` |
| `postgres` | `public.users` table | `tasks` table |

Only one database is active per backend process. User and task databases cannot
currently be selected independently, and the adapters do not sync data.

The selected database contains both the user identity record and that user's
tasks. Task rows/documents include `owner_id`; list, get, update, complete, and
delete operations are scoped to the user ID taken from the verified app JWT.

The `/runtime` route reports the selected database for the frontend indicator.
It is public and does not authenticate a user.

### Adapter notes

- **Firestore:** `FirestoreUserRepository` and `FirestoreTaskRepository` use
  Firebase Admin. Credentials can come from Application Default Credentials,
  `GOOGLE_APPLICATION_CREDENTIALS`, or the local ignored service-account file
  `DDD/.secrets/firebase-service-account.json`.
- **MongoDB:** uses `MONGODB_URI` and `MONGODB_DATABASE` (default `todo`). The
  user adapter creates unique indexes for Google and GitHub subjects.
- **PostgreSQL:** uses `POSTGRES_DSN`. The user adapter creates/updates the
  `users` table for password and Google accounts; Google-only users have no
  password hash. If it finds the old Firebase-shaped `users` table, startup
  renames it to `users_firebase_legacy` before creating the current table.

## Configuration

Copy `DDD/.env.example` to `DDD/.env` and set the values for the selected
database. Do not commit `.env`, database credentials, JWT secrets, or service
account JSON files.

| Variable | Purpose |
| --- | --- |
| `JWT_SECRET` | App JWT signing key; must be at least 32 bytes |
| `JWT_EXPIRES_MINUTES` | App JWT lifetime; defaults to 60 |
| `GOOGLE_CLIENT_ID` | Google Web client ID used to verify Google ID tokens |
| `GITHUB_CLIENT_ID` | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App secret; backend only |
| `GITHUB_REDIRECT_URI` | Exact frontend callback URL registered in the GitHub OAuth App |
| `TASK_DATABASE` | `firestore`, `mongodb`, or `postgres`; defaults to Firestore |
| `MONGODB_URI` | MongoDB connection string when MongoDB is selected |
| `MONGODB_DATABASE` | MongoDB database name; defaults to `todo` |
| `POSTGRES_DSN` | PostgreSQL connection string when PostgreSQL is selected |
| `FIREBASE_PROJECT_ID` | Optional Firestore project override |
| `GOOGLE_APPLICATION_CREDENTIALS` | Optional path to Firestore service-account JSON |
| `FIREBASE_USER_COLLECTION` | Firestore users collection; defaults to `users` |
| `FIREBASE_TASK_COLLECTION` | Firestore tasks collection; defaults to `tasks` |
| `TODO_HOST`, `TODO_PORT` | API bind address; defaults to `127.0.0.1:8000` |
| `RESEND_API_KEY` | Server-side Resend API key used by the reminder runner |
| `REMINDER_FROM_EMAIL` | Verified sender address configured in Resend |
| `WELCOME_FROM_EMAIL` | Sender for first-account welcome email; defaults to `onboarding@resend.dev` |

For Google sign-in, `GOOGLE_CLIENT_ID` must match `VITE_GOOGLE_CLIENT_ID` in
`frontend/.env`. The ID is public configuration; never place a Google client
secret in the frontend.

For GitHub sign-in, create an OAuth App and configure its callback URL to match
`GITHUB_REDIRECT_URI` and `VITE_GITHUB_REDIRECT_URI` exactly. Put the client ID
in `DDD/.env` and `frontend/.env`; put the client secret only in `DDD/.env`.
For local development the callback can be `http://127.0.0.1:5173/`. Set the
GitHub authorization callback URL to that exact URL. Restart the backend and
Vite after changing environment variables. Production needs its own callback
URL and matching frontend/backend settings.

Set the connection variables for the chosen adapter. For example:

```env
# MongoDB
TASK_DATABASE=mongodb
MONGODB_URI=mongodb://127.0.0.1:27017
MONGODB_DATABASE=todo
```

```env
# PostgreSQL
TASK_DATABASE=postgres
POSTGRES_DSN=postgresql://username:password@host:5432/database
```

For Firestore, set `TASK_DATABASE=firestore` and provide project credentials.
The service account JSON belongs in the ignored `.secrets/` directory, not Git.

For local Google sign-in, configure an OAuth Web client and add the exact
frontend origin you use, such as `http://127.0.0.1:5173`, to authorized
JavaScript origins. A production Google app needs a public homepage and privacy
policy on a domain you control.

`Settings.from_environment()` reads `DDD/.env` without overriding variables
already exported in the shell. Changing environment settings requires a backend
restart.

## Run locally

```bash
cd DDD
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set JWT_SECRET and the settings for your chosen database.
python main.py
```

Generate a suitable local JWT secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The API listens at `http://127.0.0.1:8000` by default. Start the frontend in a
second terminal. `frontend/.env` can set `BACKEND_PROXY_TARGET` if the API uses
a different address.

## HTTP endpoints

| Method and path | Authentication | Purpose | Success |
| --- | --- | --- | --- |
| `POST /auth/register` | Public | Register with email and password | `201` session |
| `POST /auth/login` | Public | Log in with email and password | `200` session |
| `POST /auth/google` | Public | Verify Google ID token and start app session | `200` session |
| `POST /auth/github` | Public | Exchange GitHub OAuth code and start app session | `200` session |
| `GET /runtime` | Public | Return active database name | `200` |
| `GET /tasks` | App JWT | List the caller's tasks | `200` |
| `POST /tasks` | App JWT | Create a task owned by the caller | `201` |
| `GET /tasks/{id}` | App JWT | Read one owned task | `200` |
| `PATCH /tasks/{id}` | App JWT | Rename one owned task | `200` |
| `POST /tasks/{id}/complete` | App JWT | Complete one owned task | `200` |
| `DELETE /tasks/{id}` | App JWT | Delete one owned task | `200` |

Create and rename accept a JSON body containing only a title:

```json
{ "title": "Learn DDD" }
```

The public task response contains `id`, `title`, `created_at`, `completed_at`,
and its optional due date fields. It does not expose `owner_id`.

The domain trims task titles and requires 1–120 characters. Task creation also
accepts a due date and time for an exact-time email reminder. Legacy clients may
also provide `submission_date` in `YYYY-MM-DD` format; those date-only tasks use
the separate one-day-prior reminder runner.

These timed reminders are scheduled directly through Resend for the chosen
instant; the browser converts its local time to UTC. Resend currently accepts
individual scheduled emails up to 30 days ahead. Editing or completing a task
replaces or cancels its scheduled reminder. Timed reminders require
`RESEND_API_KEY` and `REMINDER_FROM_EMAIL` (or the configured welcome sender
fallback).

### Resend reminders

Set `RESEND_API_KEY` and `REMINDER_FROM_EMAIL` in `DDD/.env`. Verify the sender
domain/address in Resend first. Install backend dependencies, then schedule this
command once each morning on a machine that can reach the configured database:

```cron
0 9 * * * cd /path/to/PRAC/DDD && .venv/bin/python scripts/send_task_reminders.py >> reminders.log 2>&1
```

The runner uses UTC dates; schedule it for 09:00 UTC (14:00 Pakistan time).
It sends only for incomplete tasks with a submission date tomorrow. A sent
marker is saved after Resend accepts each email, so subsequent runs skip it.
If a send succeeds but the process stops before saving the marker, the next run
may send that email again; Resend delivery and the database cannot share an
atomic transaction.

New password registrations and first-time Google account creation also send a
welcome email using `RESEND_API_KEY` and `WELCOME_FROM_EMAIL`. Existing users
who sign in do not receive another welcome email. Welcome-email delivery
failure is logged and does not prevent sign-in or registration. Resend's
`onboarding@resend.dev` sender is intended for testing; use a verified domain
sender for general recipient delivery.

## One create-task request from start to finish

```text
POST /tasks + app JWT
  -> http_server.py checks token and reads JSON
  -> api_routes.py -> task_routes.py
  -> TaskController validates and creates CreateTaskDTO
  -> TaskService builds the Task for the verified owner
  -> selected TaskRepository saves it
  -> TaskDTO -> task_view.py -> HTTP 201 JSON
```

The controller does not choose a database. `TaskService` depends on the
application-owned `TaskRepository` interface. `bootstrap.py` supplies one
concrete adapter at startup.

`TaskOrdering` puts unfinished tasks first, then orders by creation time and
task ID. Completing a task changes the domain entity once and publishes a
`TaskCompleted` event through the logging adapter.

## Code map

```text
DDD/
├── main.py                         Loads settings and starts the HTTP server
├── bootstrap.py                    Selects adapters and wires services/routes
├── domain/
│   ├── entities/task.py            Task state and completion behavior
│   ├── value_objects/              Validated task ID, title, and user ID
│   ├── domain_services/            Task ordering rule
│   ├── domain_events/              TaskCompleted fact
│   └── exceptions/                 Domain validation failures
├── application/
│   ├── services/                   AuthService and TaskService use cases
│   ├── dtos/                       Input/output data contracts
│   ├── interfaces/                 Repository, token, Google, and runtime ports
│   └── exceptions/                 Use-case failures
├── presentation/
│   ├── http_server.py              Reads/writes HTTP and maps errors to statuses
│   ├── routes/                     Maps method/path to controller actions
│   ├── controllers/                Adapts requests into use-case calls
│   ├── validators/                 Checks incoming request shapes
│   ├── middleware/                 Bearer authentication and request logging
│   └── views/                      Converts DTOs to JSON-ready dictionaries
└── infrastructure/
    ├── authentication/             Argon2, Google token verification, app JWT
    ├── repositories/               Firestore, MongoDB, and PostgreSQL adapters
    ├── firebase/                   Firebase Admin/Firestore client
    ├── config/                     Environment-backed Settings
    ├── providers/                  System clock and UUID generator
    └── messaging/                  Logs domain events
```

## Error responses

The HTTP adapter converts expected failures to JSON:

- `400`: malformed request or invalid task value.
- `401`: missing/invalid app JWT, bad login, or invalid Google ID token.
- `404`: task does not exist for the authenticated owner.
- `405`: known route with an unsupported HTTP method.
- `409`: duplicate registration or Google/password email collision.
- `500`: unexpected server or infrastructure failure; details are logged
  server-side and a generic message is sent to the client.
