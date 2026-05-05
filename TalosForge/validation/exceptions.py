"""Validation-specific exceptions."""

from typing import Any, Dict, List, Optional

from ..core.exceptions import TalosForgeException


class DataValidationError(TalosForgeException):
    """Raised when data validation against schema fails (strict mode)."""

    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.errors = errors or []
