django-static-compiler
======================

**This project is no longer maintained**

A static files compiler (JavaScript, CSS, et all) which aims to solve two things:

1. Distributed compressed and uncompresed files with third party applications.
2. Simple compression of project-wide static files.

Many projects solve the second item, but they're unfortunately not compatible (and/or very hard to make so) with
sourcemap generation.

Compiled Distributions
----------------------

Static files are stored relative to their configuration root:

::

    [site-packages]/sentry/static/sentry/js/foo.js
    [site-packages]/sentry/static/sentry/js/bar.js
    [site-packages]/otherapp/static/otherapp/css/bar.css

Each application would be compiled independently, based on its own configuration, and you'd end up with something
like the following:

::

    [site-packages]/sentry/static/sentry/dist/js/all.min.js
    [site-packages]/otherapp/static/otherapp/dist/css/bar.min.css

Eventually these would be collected (using standard staticfiles) in your project static directory.


Application Configuration
-------------------------

You'll need to add the library to both your ``INSTALLED_APPS`` and ``STATICFILES_FINDERS``:

::

  STATICFILES_FINDERS = (
      "django.contrib.staticfiles.finders.FileSystemFinder",
      "django.contrib.staticfiles.finders.AppDirectoriesFinder",
      "static_compiler.finders.StaticCompilerFinder",
  )

  INSTALLED_APPS = (
      # ...
      "static_compiler",
  )

Configuration is handled via the ``STATIC_BUNDLES`` setting, in ``settings.py``.

An example configuration might look like this:

::

    STATIC_BUNDLES = {
        "cache": "CACHE",
        "packages": {
            "sentry/scripts/global.min.js": {
                "src": [
                    "sentry/scripts/core.js",
                    "sentry/scripts/models.js",
                    "sentry/scripts/templates.js",
                    "sentry/scripts/utils.js",
                    "sentry/scripts/collections.js",
                    "sentry/scripts/charts.js",
                    "sentry/scripts/views.js",
                    "sentry/scripts/app.js",
                ],
            },
            "sentry/styles/global.min.css": {
                "src": {
                    "sentry/less/sentry.less": "sentry/styles/sentry.css",
                },
            },
        },
        "postcompilers": {
            "*.js": ["node_modules/uglify-js/bin/uglifyjs {input} --source-map-root={relroot}/ --source-map-url={name}.map{ext} --source-map={relpath}/{name}.map{ext} -o {output}"],
        },
        "preprocessors": {
            "*.less": ["node_modules/less/bin/lessc {input} {output}"],
        },
    }


There are the following top level attributes:

cache
  The directory name to store the compiler's cached files in. This is relative to ``STATIC_ROOT``, and is only used
  for compiling files.
packages
  A mapping of bunches to their options (options can include top level options as well)
precompilers
  A mapping of input grep patterns to a list of (ordered) commands to execute on files
  in all situations (including DEBUG use).
postcompilers
  A mapping of input grep patterns to a list of (ordered) commands to execute on files
  which are designated for distribution (e.g. not DEBUG use).

The packages attribute accepts the following:

src
  A list or mapping of source files to include in this bunch. If the value is a mapping
  the key is the input file, and the value is the output file.

We'd make several variables available to post- and precompilers:

input
  absolute path to input file
output
  absolute path to output file -- if not present will fetch from stdout
ext
  output extension (e.g. .js)
name
  extensionless filename from output (e.g. bundle)
filename
  full output filename (e.g. bundle.js)
path
  full output dir path (e.g. foo/bar)
relroot
  the relative path to the STATIC_ROOT. e.g. ../../..
root
  the value of STATIC_ROOT


Staticfiles Collection and Compiliation
---------------------------------------

The process currently looks like this:

- django-admin.py compilestatic
- django-admin.py collectstatic

Pre-Processors
~~~~~~~~~~~~~~

A pre-processor will **always** be run. This is nearly always a requirement as things like LESS files have to be processed
befor they can be served in a browser.

When pre-processing happens each input file is transformed to an output file (using the standard versioning scheme). For
example, if I had a bunch that included foo.less and bar.less, each would be compiled separately, and I'd end up with
two output files: foo.css, and bar.css.

The first pre-processor will change the input filename to be the expected output filename, and the following processors
will be passed that to work with.

Post-Compilers
~~~~~~~~~~~~~~

A post-compiler runs on pre-processed inputs and is expected to concatenate the results together into a unified file.

For example, if it runs against foo.js and bar.js, it will output bundle.js.

Each post-compiler must be able to accept 1+ inputs, and he first post-compilers will be responsible for combining files
and the resulting file will be passed to the additional compilers.

If no post-compilers happen, the result would be similar to the following: cat [input, input, input] > output


Template Usage
--------------

Specify the relative path to the bunch name (relative to the static root):

::

    {% load static_compiler %}

    {% staticbundle 'bundle.js' %}

You can also specify attributes, such as mimetype:

::

    {% staticbundle 'bundle.foo' mimetype='text/css' media='screen' %}

If we're in DEBUG / development mode and 'bundle.js' is defined in STATIC_BUNDLES:

1. Determines if it needs to recompile any files (based on its last modified time)
2. Serves the preprocessed but not compiled files (turning this into many html tags).

Otherwise:

1. Serve bundle.js (assumed to exist)

In general it simply acts as a proxy to the Django {% static %} templatetag with the inclusion of script/link/etc
HTML tags.

Distributing Staticfiles with your Library
------------------------------------------

The flow would be just like in your project. You'd start by defining STATIC_BUNDLES (in a build_settings.py, or
something along the lines), and then you'd simply do the following (pre-commit?):

::

  django-admin.py --settings=build_settings.py compilestatic

