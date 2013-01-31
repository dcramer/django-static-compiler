django-static-compiler
======================

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

Configuration is handled via the ``STATIC_BUNDLES`` setting, in ``settings.py``.

An example configuration might look like this:

::

    STATIC_BUNDLES = {
        "packages": {
            "sentry/scripts/global.js": {
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
            "sentry/styles/global.css": {
                "src": {
                    "sentry/less/sentry.less": "sentry/styles/sentry.css",
                },
            },
        },
        "postcompilers": {
            "*.js": ["node_modules/uglify-js/bin/uglifyjs {input} --source-map-url={name}.map{ext} --source-map={relpath}/{name}.map{ext}"],
        },
        "preprocessors": {
            "*.less": ["node_modules/less/bin/lessc {input}"],
        },
    }


There are three top level attributes:

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
ext
  output extension (e.g. .js)
name
  extensionless filename from output (e.g. bundle)
filename
  full output filename (e.g. bundle.js)
path
  full output dir path (e.g. foo/bar)


Staticfiles Collection and Compiliation
---------------------------------------

First, the compilation phase happens. This would happen either within the 3rd party app or the project (or potentially
both).

- Run manage.py compilestatic
- It iterates your staticfiles finders, finds configurations, and compiles the static files into the relative
  locations.

Once we've dealt w/ compilation, the staticfiles finder would work as expected.

PreProcessors
~~~~~~~~~~~~~

A pre-processor will **always** be run. This is nearly always a requirement as things like LESS files have to be processed
befor they can be served in a browser.

When preprocessing happens each input file is transformed to an output file (using the standard versioning scheme). For
example, if I had a bunch that included foo.less and bar.less, each would be compiled separately, and I'd end up with
two output files: foo.css, and bar.css.

PostProcessors
~~~~~~~~~~~~~~

A post-process runs on pre-processed inputs and is expected to concatenate the results together into a unified file.

For example, if it runs against foo.js and bar.js, it will output bundle.js.

If no post-processors happen, the result would be similar to the following: cat [input, input, input] > output


Template Usage
--------------

Specify the relative path to the bunch name (relative to the static root):

::

    {% staticbundle 'bundle.js' %}

If we're in DEBUG / development mode and 'bundle.js' is defined in STATIC_BUNDLES:

1. Determines if it needs to recompile any files (based on its last modified time)
2. Serves the preprocessed but not compiled files (turning this into many html tags).

Otherwise:

1. Serve bundle.js (assumed to exist)

In general it simply acts as a proxy to the Django {% static %} templatetag with the inclusion of script/link/etc
HTML tags.

TODO
----

Currently processors apply relative to their location, which works most of the time, but if you're combining files
across projects the paths will be incorrect.

To solve this we need to actually build a temporarily static directory (e.g. collectstatic), and then apply bundle
commands on top of that location.

This would change things so that every command executed with the cwd at the STATIC_ROOT, and src/dst files would be
prefixed with their relative path from the root.
