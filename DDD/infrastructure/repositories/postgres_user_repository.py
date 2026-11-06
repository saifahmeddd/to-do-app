"""PostgreSQL adapter for local password accounts."""

from datetime import datetime
from uuid import uuid4

from application.dtos.auth_dto import UserCredentialDTO
from application.exceptions.user_already_exists import UserAlreadyExists


class PostgresUserRepository:
    """Store accounts in the selected PostgreSQL database's public.users table."""

    def __init__(self, dsn: str):
        import psycopg

        self.dsn = dsn
        with psycopg.connect(self.dsn) as connection:
            columns = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'users'
                    """
                ).fetchall()
            }
            if "firebase_uid" in columns:
                legacy_table = connection.execute(
                    "SELECT to_regclass('public.users_firebase_legacy')"
                ).fetchone()[0]
                if legacy_table is not None:
                    raise RuntimeError(
                        "Both legacy and active users tables exist; inspect them "
                        "before continuing."
                    )
                # Preserve the old Firebase-only table; its passwords cannot be reused.
                connection.execute(
                    "ALTER TABLE public.users RENAME TO users_firebase_legacy"
                )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS public.users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    email_key TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    last_login_at TIMESTAMPTZ NOT NULL
                )
                """
            )

    def create_user(
        self,
        email: str,
        email_key: str,
        password_hash: str,
        created_at: datetime,
    ) -> UserCredentialDTO:
        import psycopg

        user = UserCredentialDTO(str(uuid4()), email, password_hash)
        try:
            with psycopg.connect(self.dsn) as connection:
                connection.execute(
                    """
                    INSERT INTO public.users
                        (id, email, email_key, password_hash, created_at, last_login_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user.user_id,
                        user.email,
                        email_key,
                        user.password_hash,
                        created_at,
                        created_at,
                    ),
                )
        except psycopg.errors.UniqueViolation as exc:
            raise UserAlreadyExists from exc
        return user

    def get_by_email_key(self, email_key: str) -> UserCredentialDTO | None:
        import psycopg

        with psycopg.connect(self.dsn) as connection:
            row = connection.execute(
                "SELECT id, email, password_hash FROM public.users WHERE email_key = %s",
                (email_key,),
            ).fetchone()
        if row is None:
            return None
        return UserCredentialDTO(
            user_id=row[0],
            email=row[1],
            password_hash=row[2],
        )

    def record_login(self, email_key: str, logged_in_at: datetime) -> None:
        import psycopg

        with psycopg.connect(self.dsn) as connection:
            connection.execute(
                "UPDATE public.users SET last_login_at = %s WHERE email_key = %s",
                (logged_in_at, email_key),
            )
