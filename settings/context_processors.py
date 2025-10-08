# shoestore/context_processors.py
from settings.models import SiteSettings  # assuming your SiteSettings model is in the 'settings' app

def site_settings(request):
    """Add site settings (like social links) to all templates."""
    settings = SiteSettings.objects.first()
    return {'site_settings': settings}
