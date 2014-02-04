from __future__ import absolute_import

import os.path

from django.contrib.staticfiles import finders, utils
from static_compiler.storage import StaticCompilerFileStorage


class StaticCompilerFinder(finders.BaseStorageFinder):
    """
    A staticfiles finder that looks in the compiler's cache directory
    for intermediate files.
    """
    storage = StaticCompilerFileStorage

    def list(self, ignore_patterns):
        return []


class StaticCompilerWithCacheFinder(StaticCompilerFinder):
    storage = StaticCompilerFileStorage

    def list(self, ignore_patterns):
        if os.path.exists(self.storage.location):
            for path in utils.get_files(self.storage, ignore_patterns):
                yield path, self.storage
