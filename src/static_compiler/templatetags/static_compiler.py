import os
from django import template
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command

register = template.Library()


BUNDLE_CACHE = {}


@register.simple_tag
def staticbundle(bundle):
    if settings.DEBUG and bundle in settings.STATIC_BUNDLES['packages']:
        outdated = False
        src_list = settings.STATIC_BUNDLES['packages'][bundle]['src']
        for src in src_list:
            cached_mtime = BUNDLE_CACHE.get(src, 0)
            current_mtime = os.stat(staticfiles_storage.path(src)).st_mtime
            if current_mtime > cached_mtime:
                outdated = True
                BUNDLE_CACHE[src] = current_mtime

        if outdated:
            call_command('compilestatic', bundle, compile=False)

        if isinstance(src_list, dict):
            src_list = src_list.values()

    else:
        src_list = [bundle]

    output = []
    for src in src_list:
        url = staticfiles_storage.url(src)

        # TODO: make this less stupid and configurable
        if url.endswith('.css'):
            output.append('<link href="%s" rel="stylesheet" type="text/css"/>' % (url,))
        elif url.endswith('.js'):
            output.append('<script type="text/javascript" src="%s"></script>' % (url,))

    return '\n'.join(output)
