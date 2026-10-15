from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class BaseModel(models.Model):
    created_at = models.DateTimeField(
        db_index=True,
        default=timezone.now,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True


class RandomModel(BaseModel):
    """
    Example model demonstrating database constraints.
    """

    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(start_date__lt=F("end_date")),
                name="start_date_before_end_date",
            ),
        ]