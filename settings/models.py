from django.db import models

class SiteSettings(models.Model):
    delivery_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=3500,
        help_text="Delivery fee per order"
    )

    # Social media handles
    facebook_url = models.URLField(blank=True, null=True, help_text="Facebook page URL")
    instagram_url = models.URLField(blank=True, null=True, help_text="Instagram profile URL")
    twitter_url = models.URLField(blank=True, null=True, help_text="Twitter profile URL")
    linkedin_url = models.URLField(blank=True, null=True, help_text="LinkedIn page URL")
    youtube_url = models.URLField(blank=True, null=True, help_text="YouTube channel URL")

    def __str__(self):
        return "Site Settings"

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"
