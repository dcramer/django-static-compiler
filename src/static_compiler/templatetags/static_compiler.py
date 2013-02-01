import os
from django import template
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command
from django.utils.html import escape

register = template.Library()


BUNDLE_CACHE = {}
TEMPLATES = {
    'text/css': '<link href="%(url)s" rel="stylesheet" type="%(mimetype)s %(attrs)s/>',
    'text/javascript': '<script src="%(url)s" type="%(mimetype)s" %(attrs)s></script>',
}


@register.simple_tag
def staticbundle(bundle, mimetype=None, **attrs):
    """
    >>> {% staticbundle 'bundlename.css' %}
    >>> {% staticbundle 'bundlename.css' media='screen' %}
    >>> {% staticbundle 'bundlename' mimetype='text/css' %}
    """
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

        if url.endswith('.css'):
            mimetype = 'text/css'
        elif url.endswith('.js'):
            mimetype = 'text/javascript'

        output.append(TEMPLATES[mimetype] % dict(
            url=url,
            mimetype=mimetype,
            attrs=' '.join('%s="%s"' % (k, escape(v)) for k, v in attrs.iteritems()),
        ))

    return '\n'.join(output)
