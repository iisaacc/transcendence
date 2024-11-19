from django import template
from django.core.files.storage import default_storage
from django.conf import settings
import os
import logging
logger = logging.getLogger(__name__)

register = template.Library()
    
@register.filter(name='avatar_file_exists')
def file_exists(filepath):
    # If the filepath starts with /media, strip it
    if filepath.startswith('/media/'):
        filepath = filepath[len('/media/'):]
    
    # Now join with MEDIA_ROOT
    full_filepath = os.path.join(settings.MEDIA_ROOT, filepath)
    
    if default_storage.exists(full_filepath):
        # Return the relative path (this will be joined with MEDIA_URL in the template)
        return ('media/' + filepath)
    else:
        # Fallback to a default image (relative to MEDIA_URL)
        default_image = 'media/avatars/default.png'
        return default_image