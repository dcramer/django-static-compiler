from __future__ import absolute_import

from django.contrib.staticfiles import finders
from static_compiler.storage import StaticCompilerFileStorage


class StaticCompilerFinder(finders.BaseStorageFinder):
    """
    A staticfiles finder that looks in the compiler's cache directory
    for intermediate files.
    """
    storage = StaticCompilerFileStorage

    def list(self, ignore_patterns):
        return []
