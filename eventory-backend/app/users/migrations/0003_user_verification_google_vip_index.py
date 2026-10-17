from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_user_is_vip_wallet"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_phone_verified",
            field=models.BooleanField(
                default=False,
                help_text="Whether the phone number has been verified via OTP.",
                verbose_name="Phone verified",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="is_email_verified",
            field=models.BooleanField(
                default=False,
                help_text="Whether the email address has been verified via OTP or Google.",
                verbose_name="Email verified",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="google_sub",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Stable Google account identifier (sub). Empty when unused.",
                max_length=255,
                verbose_name="Google subject",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                models.F("google_sub"),
                condition=models.Q(("google_sub", ""), _negated=True),
                name="users_user_google_sub_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["is_vip"], name="users_user_is_vip_idx"),
        ),
    ]
