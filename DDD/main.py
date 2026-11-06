"""Executable entry point for the DDD TODO HTTP API."""

import logging

from bootstrap import build_routes
from infrastructure.authentication.firebase_token_verifier import FirebaseTokenVerifier
from infrastructure.config.settings import Settings
from infrastructure.firebase.client import initialize_firebase_app
from presentation.http_server import make_server


def main() -> None:
    """Load configuration, assemble dependencies, and serve requests."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = Settings.from_environment()
    # Token verification needs Firebase Admin even when tasks use another database.
    initialize_firebase_app(
        settings.firebase_project_id,
        settings.firebase_credentials_path,
    )
    routes = build_routes(settings)
    # dependency injection of the FirebaseTokenVerifier into the HTTP server
    with make_server(
        settings.host,
        settings.port,
        routes,
        FirebaseTokenVerifier(),
    ) as server:
        logging.info("TODO API listening on http://%s:%s", settings.host, settings.port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
