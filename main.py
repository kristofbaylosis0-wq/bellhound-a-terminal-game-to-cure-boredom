"""Backward-compatible entry point for Bellbound.

The authoritative CLI lives in :mod:`game.__main__`. This shim keeps
``python main.py`` working without maintaining a second game launcher.
"""

from game.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())
