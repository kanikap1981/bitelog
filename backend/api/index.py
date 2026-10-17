"""Vercel entrypoint for the existing BiteLog FastAPI application."""

from app.main import app

__all__ = ["app"]
