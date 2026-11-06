"""Executable entry point for the DDD TODO HTTP API."""

import logging

from bootstrap import build_routes
from infrastructure.authentication.jwt_token_service import JwtTokenService
from infrastructure.config.settings import Settings
from presentation.http_server import make_server


def main() -> None:
    """Load configuration, assemble dependencies, and serve requests."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = Settings.from_environment()
    jwt_service = JwtTokenService(
        settings.jwt_secret,
        settings.task_database,
        settings.jwt_expires_minutes,
    )
    routes = build_routes(settings, jwt_service=jwt_service)
    with make_server(
        settings.host,
        settings.port,
        routes,
        jwt_service,
    ) as server:
        logging.info("TODO API listening on http://%s:%s", settings.host, settings.port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
