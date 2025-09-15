from __future__ import annotations

from typing import Any, Dict, TypeVar, cast
from ._types import NotGiven, NOT_GIVEN

T = TypeVar("T")


def is_given(value: object) -> bool:
    """Check if a value is not NOT_GIVEN"""
    return not isinstance(value, NotGiven)


def is_dict(value: object) -> bool:
    """Check if a value is a dictionary"""
    return isinstance(value, dict)


def maybe_transform(
    data: Any,
    transform_type: type | None = None,
) -> Any:
    """
    Transform data to the specified type if needed.
    This is a simplified version - in production you'd use
    more sophisticated type transformation.
    """
    if data is None or data is NOT_GIVEN:
        return data
    
    if transform_type and not isinstance(data, transform_type):
        # Simple transformation - in production this would be more complex
        return data
    
    return data


async def async_maybe_transform(
    data: Any,
    transform_type: type | None = None,
) -> Any:
    """Async version of maybe_transform"""
    # For now, just call the sync version
    # In production, this might do async validation
    return maybe_transform(data, transform_type)


def remove_notgiven_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove NOT_GIVEN values from a dictionary"""
    return {k: v for k, v in data.items() if is_given(v)}


def merge_headers(
    *header_dicts: Dict[str, str] | None,
) -> Dict[str, str]:
    """Merge multiple header dictionaries"""
    result = {}
    for headers in header_dicts:
        if headers:
            result.update(headers)
    return result