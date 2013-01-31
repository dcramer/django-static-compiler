from fnmatch import fnmatch
import os.path
from django.contrib.staticfiles import finders
from django.core.management.base import BaseCommand, CommandError
from django.utils import simplejson
from django.utils.datastructures import SortedDict


def find_static_files(ignore_patterns=()):
    found_files = SortedDict()
    for finder in finders.get_finders():
        for path, storage in finder.list(ignore_patterns):
            # Prefix the relative path if the source storage contains it
            if getattr(storage, 'prefix', None):
                prefixed_path = os.path.join(storage.prefix, path)
            else:
                prefixed_path = path

            if prefixed_path not in found_files:
                found_files[prefixed_path] = (storage, path)
    return found_files


def read_package_config(path):
    with open(path) as fp:
        data = simplejson.load(fp)
    return data


class Command(BaseCommand):
    def handle(self, *args, **options):
        # TODO: wtf is a prefixed path

        # First we need to build a mapping of all files using django.contrib.staticfiles
        bunch_mapping = {}

        found_files = find_static_files()
        for prefixed_path, (storage, path) in found_files.iteritems():
            if not path.endswith('packages.json'):
                continue

            source_path = storage.path(path)
            config = read_package_config(source_path)
            for bunch, options in config.get('packages', {}).iteritems():
                options['path'] = os.path.dirname(source_path)
                options['ext'] = os.path.splitext(bunch)[1]
                options.setdefault('preprocessors', config.get('preprocessors'))
                options.setdefault('postcompilers', config.get('postcompilers'))
                bunch_mapping[bunch] = options

        # Now do shit
        for bunch_name, options in bunch_mapping.iteritems():
            for src in options['src']:
                for pattern, cmd_list in (options.get('preprocessors') or {}).iteritems():
                    if fnmatch(src, pattern):
                        for cmd in cmd_list:
                            name = os.path.splitext(src)[0]
                            print cmd % dict(
                                input=src,
                                output=os.path.join(options['path'], name + options['ext']),
                            )

            for pattern, cmd_list in (options.get('postcompilers') or {}).iteritems():
                if fnmatch(bunch_name, pattern):
                    for cmd in cmd_list:
                        # TODO: pipe source files (after preprocessed) into stdin
                        print cmd % dict(
                            input='/dev/stdin',
                            output=os.path.join(options['path'], bunch_name),
                        )
