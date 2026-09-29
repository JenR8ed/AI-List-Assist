"""Local draft review rules; no marketplace calls or publishing side effects."""

import math
from typing import Any

from shared.models import ItemCondition


def validate_draft(draft: dict[str, Any]) -> list[str]:
    """Report missing or invalid review fields without changing the draft."""
    errors = []
    for field in ('title', 'description', 'category_id'):
        value = draft.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f'{field} is required')
    if isinstance(draft.get('title'), str) and len(draft['title']) > 80:
        errors.append('title must be at most 80 characters')
    if draft.get('condition') not in {condition.value for condition in ItemCondition}:
        errors.append('condition is invalid')
    price = draft.get('price')
    if isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(price) or price <= 0:
        errors.append('price must be a positive number')
    if draft.get('missing_required_specifics'):
        errors.append('required item specifics are missing')
    return errors
