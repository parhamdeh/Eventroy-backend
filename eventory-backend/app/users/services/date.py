
from datetime import date

from django.utils import timezone


def calculate_age(birth_date: date | None) -> int | None:
    """
    Calculate a person's age based on their birth date.

    Args:
        birth_date: The person's date of birth.

    Returns:
        The person's completed age in years, or None if
        the birth date has not been provided.
    """

    if birth_date is None:
        return None

    today = timezone.localdate()

    age = today.year - birth_date.year

    if (today.month, today.day) < (
        birth_date.month,
        birth_date.day,
    ):
        age -= 1

    return age
