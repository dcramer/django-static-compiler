import os
from django import template
from django.contrib.staticfiles.storage import staticfiles_storage
from django.conf import settings

register = template.Library()


BUNDLE_CACHE = {}


@register.simple_tag
def staticbundle(bundle):
    if settings.DEBUG:
        cached_mtime = BUNDLE_CACHE.get(bundle, 0)
        current_mtime = os.stat(staticfiles_storage.path(bundle)).st_mtime
        if current_mtime > cached_mtime:
            # run preprocessors on file
            pass
            BUNDLE_CACHE[bundle] = current_mtime

    url = staticfiles_storage.url(bundle)

    # TODO: make this less stupid and configurable
    if bundle.endswith('.css'):
        '<link href="%s" rel="stylesheet" type="text/css"/>' % (url,)
    elif bundle.endswith('.js'):
        '<script type="text/javascript" src="%s"></script>' % (url,)

    return url
