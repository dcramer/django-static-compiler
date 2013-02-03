from __future__ import absolute_import

import logging
import os
from django import template
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command
from django.utils.html import escape

from static_compiler.constants import DEFAULT_CACHE_DIR


register = template.Library()
logger = logging.getLogger('static_compiler')

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
    config = getattr(settings, 'STATIC_BUNDLES', {})

    if settings.DEBUG and bundle in config['packages']:
        cache_root = os.path.join(settings.STATIC_ROOT, config.get('cache') or DEFAULT_CACHE_DIR)

        changed = set()
        src_list = config['packages'][bundle]['src']
        for src in src_list:
            cached_mtime = BUNDLE_CACHE.get(src)
            if cached_mtime is None:
                BUNDLE_CACHE[src] = cached_mtime = os.stat(
                    os.path.join(cache_root, src)).st_mtime

            current_mtime = os.stat(staticfiles_storage.path(src)).st_mtime
            if current_mtime != cached_mtime:
                changed.add(src)
                BUNDLE_CACHE[src] = current_mtime

        if changed:
            logger.info('Regenerating %s due to changes: %s', bundle, ' '.join(changed))
            call_command('compilestatic', bundle)

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
