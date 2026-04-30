"""Shared HTTP fetch with exponential backoff + jitter retry."""

import random
import time

import requests

# Status codes that warrant a retry
_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})

_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0  # seconds; delays: 1s, 2s, 4s
_BACKOFF_MAX = 8.0
_JITTER = 0.3  # ± uniform jitter added to each delay


def fetch(url: str, headers: dict, timeout: int = 10) -> requests.Response:
    """GET *url* with retry on transient network and server errors.

    Retry schedule (before jitter): 1 s, 2 s, 4 s.
    Raises the last exception if all attempts fail.
    """
    last_exc: Exception | None = None

    for attempt in range(_MAX_RETRIES + 1):
        if attempt:
            delay = min(_BACKOFF_BASE * 2 ** (attempt - 1), _BACKOFF_MAX)
            delay += random.uniform(-_JITTER, _JITTER)
            time.sleep(max(delay, 0.1))

        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as exc:
            last_exc = exc
            continue

        if resp.status_code not in _RETRY_STATUS or attempt == _MAX_RETRIES:
            resp.raise_for_status()
            return resp

        last_exc = requests.exceptions.HTTPError(response=resp)

    assert last_exc is not None
    raise last_exc
