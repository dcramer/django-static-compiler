import os.path
import shlex
import subprocess
from fnmatch import fnmatch
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management.base import BaseCommand
from django.utils import simplejson
from django.utils.datastructures import SortedDict


def find_static_files(ignore_patterns=()):
    found_files = SortedDict()
    for finder in finders.get_finders():
        for path, storage in finder.list(ignore_patterns):
            found_files[path] = storage.path(path)
    return found_files


def read_package_config(path):
    with open(path) as fp:
        data = simplejson.load(fp)
    return data


class Command(BaseCommand):
    def get_format_params(self, dst):
        dst_filename = os.path.basename(dst)
        dst_path = os.path.dirname(dst)
        dst_basename, dst_ext = os.path.splitext(dst_filename)

        return dict(
            name=dst_basename,
            ext=dst_ext,
            filename=dst_filename,
            path=dst_path,
            static_root=os.path.abspath(settings.STATIC_ROOT),
        )

    def parse_command(self, cmd, **params):
        parsed_cmd = shlex.split(str(cmd).format(**params))
        # force absolute path to binary
        parsed_cmd[0] = os.path.abspath(parsed_cmd[0])

        # TODO: why is uglify hanging when we pass the command as a list?
        return ' '.join(parsed_cmd)

    def run_command(self, cmd, root, dst, **params):
        parsed_cmd = self.parse_command(cmd, **params)

        print " ->", parsed_cmd
        proc = subprocess.Popen(
            args=parsed_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=root,
        )
        (stdout, stderr) = proc.communicate()

        assert not proc.returncode, stderr

        # TODO: this should probably change dest to be a temp file
        with open(os.path.join(root, dst), 'w') as fp:
            fp.write(stdout)

    def apply_preprocessors(self, root, src, dst, processors):
        """
        Preprocessors operate based on the source filename, and apply to each
        file individually.
        """
        matches = [(pattern, cmds) for pattern, cmds in processors.iteritems() if fnmatch(src, pattern)]
        if src == dst and not matches:
            return

        params = self.get_format_params(dst)

        src_path = src
        for pattern, cmd_list in matches:
            for cmd in cmd_list:
                self.run_command(cmd, root=root, dst=dst, input=src_path, **params)
                src_path = dst

    def apply_postcompilers(self, root, src_list, dst, processors):
        """
        Postcompilers operate based on the destination filename. They operate on a collection
        of files, and are expected to take a list of 1+ inputs and generate a single output.
        """
        dst_file = os.path.join(root, dst)

        matches = [(pattern, cmds) for pattern, cmds in processors.iteritems() if fnmatch(dst, pattern)]
        if not matches:
            # We should just concatenate the files
            with open(dst_file, 'w') as dst_fp:
                for src in src_list:
                    with open(os.path.join(root, src)) as src_fp:
                        for chunk in src_fp:
                            dst_fp.write(chunk)
            return

        params = self.get_format_params(dst)

        # TODO: probably doesnt play nice everywhere
        src_names = src_list
        for pattern, cmd_list in processors.iteritems():
            for cmd in cmd_list:
                self.run_command(cmd, root=root, dst=dst, input=' '.join(src_names), **params)
                src_names = [dst]

    def handle(self, *args, **options):
        # TODO: wtf is a prefixed path

        # First we need to build a mapping of all files using django.contrib.staticfiles
        bundle_mapping = {}

        found_files = find_static_files()
        for rel_path, abs_path in found_files.iteritems():
            if not rel_path.endswith('packages.json'):
                continue

            config = read_package_config(abs_path)
            for bundle_name, options in config.get('packages', {}).iteritems():
                options['path'] = os.path.dirname(abs_path)
                options['ext'] = os.path.splitext(bundle_name)[1]
                options.setdefault('preprocessors', config.get('preprocessors'))
                options.setdefault('postcompilers', config.get('postcompilers'))
                bundle_mapping[bundle_name] = options

        for bundle_name, options in bundle_mapping.iteritems():
            src_outputs = []
            for src in options['src']:
                # TODO: we need to deal w/ relative files
                # (e.g. / means absolute to static home, otherwise its relative to bunch path)
                if src.startswith('/'):
                    src_path = found_files[src[1:]]
                else:
                    src_path = src
                name = os.path.splitext(src)[0]
                dst_path = name + options['ext']

                self.apply_preprocessors(
                    options['path'],
                    src_path,
                    dst_path,
                    options.get('preprocessors'),
                )

                src_outputs.append(dst_path)

            self.apply_postcompilers(
                options['path'],
                src_outputs,
                os.path.join(options['path'], bundle_name),
                options.get('postcompilers'),
            )
