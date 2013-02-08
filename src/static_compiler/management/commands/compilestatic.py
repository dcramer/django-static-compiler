from __future__ import absolute_import

import os.path
import shlex
import shutil
import subprocess
from fnmatch import fnmatch
from optparse import make_option
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management.base import BaseCommand
from django.utils.datastructures import SortedDict

from static_compiler.constants import DEFAULT_CACHE_DIR


def ensure_dirs(dst):
    dirname = os.path.dirname(dst)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def copy_file(src, dst):
    ensure_dirs(dst)
    shutil.copy2(src, dst)


def find_static_files(ignore_patterns=()):
    found_files = SortedDict()
    for finder in finders.get_finders():
        for path, storage in finder.list(ignore_patterns):
            found_files[path] = storage.path(path)
    return found_files


def collect_static_files(src_map, dst):
    """
    Collect all static files and move them into a temporary location.

    This is very similar to the ``collectstatic`` command.
    """
    for rel_src, abs_src in src_map.iteritems():
        abs_dst = os.path.join(dst, rel_src)
        copy_file(abs_src, abs_dst)


def get_format_params(dst):
    filename = os.path.basename(dst)
    path = os.path.dirname(dst)
    basename, ext = os.path.splitext(filename)
    if path.startswith(settings.STATIC_ROOT):
        relpath = path[len(settings.STATIC_ROOT) + 1:]
    else:
        relpath = path

    return dict(
        name=basename,
        ext=ext,
        filename=filename,
        relpath=relpath,
        abspath=path,
        # TODO: is there a better way to do the relroot?
        relroot=os.sep.join([os.pardir] * (relpath.count(os.sep) + 1),),
        root=os.path.abspath(settings.STATIC_ROOT),
    )


def parse_command(cmd, input, params):
    parsed_cmd = shlex.split(str(cmd).format(input=input, **params))
    # force absolute path to binary
    parsed_cmd[0] = os.path.abspath(parsed_cmd[0])

    # TODO: why is uglify hanging when we pass the command as a list?
    return ' '.join(parsed_cmd)


def run_command(cmd, root, dst, input, params):
    """
    Execute a command, and if successful write it's stdout to ``root``/``dst``.
    """
    use_stdout = '{output}' not in cmd
    if not use_stdout:
        params['output'] = dst
    parsed_cmd = parse_command(cmd, input=input, params=params)

    ensure_dirs(dst)

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

    if use_stdout:
        # TODO: this should probably change dest to be a temp file
        with open(os.path.join(root, dst), 'w') as fp:
            fp.write(stdout)


def apply_preprocessors(root, src, dst, processors):
    """
    Preprocessors operate based on the source filename, and apply to each
    file individually.
    """
    matches = [(pattern, cmds) for pattern, cmds in processors.iteritems() if fnmatch(src, pattern)]
    if src == dst and not matches:
        return False

    params = get_format_params(dst)

    src_path = src
    for pattern, cmd_list in matches:
        for cmd in cmd_list:
            run_command(cmd, root=root, dst=dst, input=src_path, params=params)
            src_path = dst

    return True


def apply_postcompilers(root, src_list, dst, processors):
    """
    Postcompilers operate based on the destination filename. They operate on a collection
    of files, and are expected to take a list of 1+ inputs and generate a single output.
    """
    dst_file = os.path.join(root, dst)

    matches = [(pattern, cmds) for pattern, cmds in processors.iteritems() if fnmatch(dst, pattern)]
    if not matches:
        ensure_dirs(dst_file)
        # We should just concatenate the files
        with open(dst_file, 'w') as dst_fp:
            for src in src_list:
                with open(os.path.join(root, src)) as src_fp:
                    for chunk in src_fp:
                        dst_fp.write(chunk)
        return True

    params = get_format_params(dst)

    # TODO: probably doesnt play nice everywhere
    src_names = src_list
    for pattern, cmd_list in processors.iteritems():
        for cmd in cmd_list:
            run_command(cmd, root=root, dst=dst, input=' '.join(src_names), params=params)
            src_names = [dst]

    return True


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--no-compile', action='store_false', default=True, dest='compile'),
    )

    def handle(self, *bundles, **options):
        config = settings.STATIC_BUNDLES
        if not config:
            return

        cache_root = os.path.join(settings.STATIC_ROOT,
            config.get('cache') or DEFAULT_CACHE_DIR)

        static_files = find_static_files()

        # remove all files in cache root
        for key, value in static_files.items():
            if value.startswith(cache_root):
                del static_files[key]

        # First we need to build a mapping of all files using django.contrib.staticfiles
        bundle_mapping = {}
        for bundle_name, bundle_opts in config.get('packages', {}).iteritems():
            if bundles and bundle_name not in bundles:
                continue

            bundle_opts['ext'] = os.path.splitext(bundle_name)[1]
            bundle_opts.setdefault('preprocessors', config.get('preprocessors'))
            bundle_opts.setdefault('postcompilers', config.get('postcompilers'))
            bundle_mapping[bundle_name] = bundle_opts

        collect_static_files(static_files, cache_root)

        for bundle_name, bundle_opts in bundle_mapping.iteritems():
            src_outputs = []
            is_mapping = isinstance(bundle_opts['src'], dict)

            for src_path in bundle_opts['src']:
                # TODO: we should guarantee that you cant preprocess an input into the
                # same output file
                if not bundle_opts.get('preprocessors'):
                    continue

                if is_mapping:
                    dst_path = bundle_opts['src'][src_path]
                else:
                    dst_path = src_path

                dst_abspath = os.path.join(cache_root, dst_path)

                was_run = apply_preprocessors(
                    root=cache_root,
                    src=src_path,
                    dst=dst_abspath,
                    processors=bundle_opts.get('preprocessors'),
                )
                if was_run:
                    copy_file(
                        src=dst_abspath,
                        dst=os.path.join(settings.STATIC_ROOT, dst_path)
                    )

                src_outputs.append(dst_path)

            if options['compile']:
                if not bundle_opts.get('postcompilers'):
                    continue

                apply_postcompilers(
                    root=cache_root,
                    src_list=src_outputs,
                    dst=os.path.join(settings.STATIC_ROOT, bundle_name),
                    processors=bundle_opts.get('postcompilers'),
                )
