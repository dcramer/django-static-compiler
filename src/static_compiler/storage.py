from __future__ import absolute_import

import errno
import os.path
from datetime import datetime
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from static_compiler.constants import DEFAULT_CACHE_DIR


class StaticCompilerFileStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None, *args, **kwargs):
        if location is None:
            location = os.path.join(settings.STATIC_ROOT, DEFAULT_CACHE_DIR)
        if base_url is None:
            base_url = settings.STATIC_URL
        super(StaticCompilerFileStorage, self).__init__(location, base_url,
                                                    *args, **kwargs)

    def accessed_time(self, name):
        return datetime.fromtimestamp(os.path.getatime(self.path(name)))

    def created_time(self, name):
        return datetime.fromtimestamp(os.path.getctime(self.path(name)))

    def modified_time(self, name):
        return datetime.fromtimestamp(os.path.getmtime(self.path(name)))

    def get_available_name(self, name):
        """
        Deletes the given file if it exists.
        """
        if self.exists(name):
            self.delete(name)
        return name

    def delete(self, name):
        """
        Handle deletion race condition present in Django prior to 1.4
        https://code.djangoproject.com/ticket/16108
        """
        try:
            super(StaticCompilerFileStorage, self).delete(name)
        except OSError, e:
            if e.errno != errno.ENOENT:
                raise
