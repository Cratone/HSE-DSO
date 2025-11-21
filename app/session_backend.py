"""Session storage backends for authentication tokens."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:  # pragma: no cover - typing only
    from redis import Redis


class SessionBackend(Protocol):
    """Simple interface for storing and resolving session tokens."""

    def store_token(self, token: str, user_id: int) -> None: ...

    def resolve_token(self, token: str) -> int | None: ...

    def reset(self) -> None: ...


@dataclass
class InMemorySessionBackend(SessionBackend):
    """Naive in-memory session backend used by tests and local runs."""

    _sessions: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if self._sessions is None:
            self._sessions = {}

    def store_token(self, token: str, user_id: int) -> None:
        assert self._sessions is not None
        self._sessions[token] = user_id

    def resolve_token(self, token: str) -> int | None:
        assert self._sessions is not None
        return self._sessions.get(token)

    def reset(self) -> None:
        assert self._sessions is not None
        self._sessions.clear()


class RedisSessionBackend(SessionBackend):
    """Redis-backed session store with TTL and prefix isolation."""

    def __init__(
        self,
        url: str,
        prefix: str = "recipe-session",
        ttl_seconds: int = 3600,
        client: "Redis" | None = None,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._prefix = prefix.rstrip(":")
        self._ttl = ttl_seconds
        if client is not None:
            self._client = client
        else:
            try:
                from redis import Redis as RedisClient  # type: ignore
            except ImportError as exc:  # pragma: no cover - env misconfig
                raise RuntimeError(
                    "redis package is not installed; "
                    "install redis extra or set SESSION_BACKEND=memory"
                ) from exc
            self._client = RedisClient.from_url(url, decode_responses=True)
        # Fail fast if the connection cannot be established
        self._client.ping()

    def store_token(self, token: str, user_id: int) -> None:
        self._client.set(self._key(token), str(user_id), ex=self._ttl)

    def resolve_token(self, token: str) -> int | None:
        value = self._client.get(self._key(token))
        return int(value) if value is not None else None

    def reset(self) -> None:
        pattern = f"{self._prefix}:*"
        keys = list(self._client.scan_iter(match=pattern, count=200))
        if keys:
            self._client.delete(*keys)

    def _key(self, token: str) -> str:
        return f"{self._prefix}:{token}"


def create_session_backend_from_env() -> SessionBackend:
    """Factory that selects session backend based on environment variables."""

    backend_name = os.getenv("SESSION_BACKEND", "memory").strip().lower()
    if backend_name == "redis":
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        prefix = os.getenv("SESSION_KEY_PREFIX", "recipe-session")
        ttl_raw = os.getenv("SESSION_TTL_SECONDS", "3600")
        try:
            ttl_seconds = int(ttl_raw)
        except ValueError as exc:  # pragma: no cover - validated by env parsing tests
            raise ValueError("SESSION_TTL_SECONDS must be an integer") from exc
        return RedisSessionBackend(
            url=redis_url, prefix=prefix, ttl_seconds=ttl_seconds
        )

    return InMemorySessionBackend()
