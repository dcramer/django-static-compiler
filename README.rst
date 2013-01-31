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

Configuration would be handled via a configuration file located in the application's static directory (via staticfiles):

::

    [site-packages]/static/packages.json

An example configuration might look like this:

::

    {
        "packages": {
            "scripts/global.js": {
                "src": [
                    "scripts/core.js",
                    "scripts/models.js",
                    "scripts/templates.js",
                    "scripts/utils.js",
                    "scripts/collections.js",
                    "scripts/charts.js",
                    "scripts/views.js",
                    "scripts/app.js"
                ]
            },
            "styles/global.css": {
                "src": [
                    "less/sentry.less"
                ]
            }
        },
        "postcompilers": {
            "*.js": ["node_modules/uglify-js/bin/uglifyjs {input} --source-map={name}.map{ext}"]
        },
        "preprocessors": {
            "*.less": ["node_modules/less/bin/lessc {input}"]
        }
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
  extensionless filename from output (e.g. bunchname)
filename
  full output filename (e.g. bunchname.js)
path
  full output dir path (e.g. foo/bar)

File Locations
~~~~~~~~~~~~~~

The configuration file can be placed within any directory, which makes the compiled bunchname and it's
files relative to the directory.

For example, if you have this in /assets/sentry/packages.json:

::

    {
        'packages': {
            'global.js': {
                'src': ['js/foo.js', '/jquery/jquery.js']
            }
        }
    }

We would end up with a single output file located in /static/sentry/global.js, which is a combination of
/static/sentry/js/foo.js and /static/jquery/jquery.js (which is likely provided by a dependency).

The resulting use of this in a template would specify global.js relative to the packages.json:

::

    {% staticfile 'sentry/global.js' %}

This file would actually have been generated and stored in /assets/sentry/global.js.

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

In debug mode, or more specifically when the Python code is serving the staticfiles, we would store each file in a bunches
modified time, and we'd recompile whenever that value is changed.

When preprocessing happens each input file is transformed to an output file (using the standard versioning scheme). For
example, if I had a bunch that included foo.less and bar.less, each would be compiled separately, and I'd end up with
two output files: foo.css, and bar.css.

PostProcessors
~~~~~~~~~~~~~~

A post-process runs on pre-processed inputs and is expected to concatenate the results together into a unified file.

For example, if it runs against foo.js and bar.js, it will output bunchname.js.


Template Usage
--------------

Specify the relative path to the bunch name (relative to the static root):

::

    {% staticfile 'bunchname.js' %}
