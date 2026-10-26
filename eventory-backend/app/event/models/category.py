from django.db import models
from django.utils.translation import gettext_lazy as _

from app.common.models import BaseModel


class Category(BaseModel):
    """
    Represent a category used to organize events.

    Each category has a unique name and can be associated
    with multiple events.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("name"),
        help_text=_("The unique name of the event category."),
    )

    class Meta:
        """Define category model metadata."""

        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["name"]

    def __str__(self) -> str:
        """Return the category name."""
        return self.name