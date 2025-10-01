"""Server-only runner for the Flet app (used in headless tests)."""

from __future__ import annotations

import argparse

import flet as ft

from .main import main


def get_asgi_app():
    """Return an ASGI app for serving the Flet UI without opening a window."""
    return ft.app(target=main, export_asgi_app=True)


def run_server(port: int, host: str = "127.0.0.1") -> None:
    """Convenience launcher using uvicorn."""
    import uvicorn

    uvicorn.run(
        "app.web_runner:get_asgi_app",
        host=host,
        port=port,
        factory=True,
        log_level="warning",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Coordinate Converter UI server")
    parser.add_argument("--port", type=int, default=0, help="Port to bind the server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface")
    return parser.parse_args()


def cli() -> None:  # pragma: no cover - simple CLI glue
    args = parse_args()
    run_server(port=args.port, host=args.host)


if __name__ == "__main__":  # pragma: no cover
    cli()
