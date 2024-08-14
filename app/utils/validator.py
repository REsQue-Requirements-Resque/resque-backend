from typing import Any


def validate_field(validators: list[callable], value: Any):
    errors = []
    for validator in validators:
        try:
            value = validator(value)
        except ValueError as e:
            errors.append(str(e))
    if errors:
        raise ValueError(errors)
    return value
