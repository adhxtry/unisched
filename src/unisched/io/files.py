"""Validated file abstraction for the ``unisched.io`` layer.

The goal of this module is to pass around a strongly defined file object rather
than raw string paths. That keeps callers honest: if they receive a
``ValidatedFile`` instance, they are dealing with a normalized path that has
already been checked for basic file semantics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Self

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ValidatedFile:
    """Represent a normalized file path with read/write helpers.

    The instance is validated during construction so downstream code can rely on
    it being a concrete file target rather than an ambiguous path-like value.
    """

    path: Path

    def __post_init__(self) -> None:
        normalized_path = Path(self.path).expanduser().resolve(strict=False)
        self._validate_path(normalized_path)
        self._ensure_file_exists(normalized_path)
        object.__setattr__(self, "path", normalized_path)

    @classmethod
    def from_path(cls, path: str | Path) -> Self:
        """Build a validated file wrapper from a path-like value."""

        return cls(Path(path))

    @staticmethod
    def _validate_path(path: Path) -> None:
        if not path.name:
            raise ValueError("ValidatedFile requires a concrete file path.")

        if path.exists() and path.is_dir():
            raise IsADirectoryError(f"Expected a file path, got directory: {path}")

    @staticmethod
    def _ensure_file_exists(path: Path) -> None:
        if path.exists():
            return

        logger.info("Creating file at %s", path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        logger.debug("Created file at %s", path)

    def __fspath__(self) -> str:
        return str(self.path)

    def __str__(self) -> str:
        return str(self.path)

    def exists(self) -> bool:
        return self.path.exists()

    @property
    def extension(self) -> str:
        return self.path.suffix.lower()

    def read_text(self, encoding: str = "utf-8", errors: str = "strict") -> str:
        """Read the file contents as text."""

        logger.info("Reading text from %s", self.path)
        content = self.path.read_text(encoding=encoding, errors=errors)
        logger.debug("Read %s characters from %s", len(content), self.path)
        return content

    def write_text(
        self,
        content: str,
        encoding: str = "utf-8",
        errors: str = "strict",
        newline: str | None = None,
    ) -> int:
        """Write text content to the file.

        The parent directory is not created automatically. Callers should decide
        whether the target location should be provisioned up front.
        """

        logger.info("Writing text to %s", self.path)
        written = self.path.write_text(
            content,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )
        logger.debug("Wrote %s characters to %s", written, self.path)
        return written
