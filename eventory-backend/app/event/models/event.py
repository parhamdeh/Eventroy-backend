from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.common.models import BaseModel


class Event(BaseModel):
    """
    Represent an event that users can discover and register for.

    Events contain descriptive information, pricing, capacity,
    media, location, category, registration deadline, and points.

    Prices are stored as integer values in Iranian tomans.
    A limit of zero means that the event has no capacity limit.
    """

    title = models.CharField(
        max_length=255,
        verbose_name=_("title"),
        help_text=_("The title of the event."),
    )

    content = models.TextField(
        verbose_name=_("content"),
        help_text=_("The detailed description of the event."),
    )

    price = models.PositiveBigIntegerField(
        default=0,
        verbose_name=_("price"),
        help_text=_("The event price in Iranian tomans. Zero means free."),
    )

    limit = models.PositiveIntegerField(
        default=0,
        verbose_name=_("capacity limit"),
        help_text=_(
            "The maximum number of participants. "
            "Zero means unlimited capacity."
        ),
    )

    image = models.ImageField(
        upload_to="events/images/",
        blank=True,
        null=True,
        verbose_name=_("image"),
        help_text=_("An optional image for the event."),
    )

    video = models.FileField(
        upload_to="events/videos/",
        blank=True,
        null=True,
        verbose_name=_("video"),
        help_text=_("An optional video file for the event."),
    )

    location = models.CharField(
        max_length=255,
        verbose_name=_("location"),
        help_text=_("The location or venue of the event."),
    )

    latitude = models.DecimalField(
    max_digits=9,
    decimal_places=6,
    blank=True,
    null=True,
    verbose_name=_("latitude"),
    help_text=_("The geographic latitude of the event."),
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name=_("longitude"),
        help_text=_("The geographic longitude of the event."),
    )

    category = models.ForeignKey(
        "event.Category",
        on_delete=models.PROTECT,
        related_name="events",
        verbose_name=_("category"),
        help_text=_("The category to which this event belongs."),
    )

    active = models.BooleanField(
        default=True,
        verbose_name=_("active"),
        help_text=_("Whether this event is currently active."),
    )

    limit_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("registration deadline"),
        help_text=_(
            "The deadline for event registration. "
            "Leave empty if there is no deadline."
        ),
    )

    point = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5),
        ],
        verbose_name=_("point"),
        help_text=_("The event point, from zero to five."),
    )

    class Meta:
        """Define event model metadata."""

        verbose_name = _("event")
        verbose_name_plural = _("events")
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["active", "category"],
                name="event_active_category_idx",
            ),
            models.Index(
                fields=["limit_time"],
                name="event_limit_time_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(point__gte=0, point__lte=5),
                name="event_point_between_0_and_5",
            ),
        ]

    def __str__(self) -> str:
        """Return a readable representation of the event."""
        return f"Event(title={self.title!r}, id={self.pk})"
    