"""Built-in device profiles."""

from __future__ import annotations

from . import compressed, l11, unsupported

BUILTIN_PROFILES = (*l11.PROFILES, *compressed.PROFILES, *unsupported.PROFILES)

__all__ = ["BUILTIN_PROFILES"]
