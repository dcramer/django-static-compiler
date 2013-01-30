django-static-compiler
======================

A static files compiler (JavaScript, CSS, et all) which aims to solve two things:

1. Distributed compressed and uncompresed files with third party applications.
2. Simple compression of project-wide static files.

Many projects solve the second item, but they're unfortunately not compatible (and/or very hard to make so) with
sourcemap generation.

Compiled Distributions
----------------------

Static files are stored relative to their root:

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

    [site-packages]/static/static.json

The configration would describe bunches:

::

    {
        'packages': {
            'bunchname.js': {
                'src': ['foo.js']
            }
        },
        postcompilers: {
            '*.js': ['uglifyjs %(input)s %(output)s']
        }
        precompilers: {
            '*.less': ['lessc %(input)s %(output)s']
        }
    }

We'd make several variables available:

input:
  absolute path to input file
output:
  absolute path to output file
version:
  the generated version identifier (this is a checksum of the input file(s))
ext:
  output extension (e.g. .js)
name:
  extensionless filename from output (e.g. bunchname)
filename:
  full output filename (e.g. bunchname.VERSION.js)

Staticfiles Collection and Compiliation
---------------------------------------

First, the compilation phase happens. This would happen either within the 3rd party app or the project (or potentially
both).

- Run manage.py compilestatic
- It iterates your staticfiles finders, finds configurations, and compiles the static files into the relative
  locations.

It's important to note, that the configuration file would be relative to the directory, and potentially we should support
inclusion of files from apps (e.g. at the project level). For example, my app might want to do this:

::

    # sentry/static/static.json
    {
        'packages': {
            'global.js': {
                'src': ['/sentry/js/foo.js', '/jquery/jquery.js']
            }
        },
    }

(Imagine there was a django-jquery which just had this static file available.)

We'd generate a manifest (similar to compressor) which described the results of this action, so we'd know which
compiled files are available, and which aren't. This would handle cases where an application didn't distribute
compiled files and your system isnt configured with the nescesary tools to compile them.

Once we've dealt w/ compilation, the staticfiles finder would work as expected.

PreProcessors
~~~~~~~~~~~~~

A pre-processor will **always** be run. This is nearly always a requirement as things like LESS files have to be processed
befor they can be served in a browser.

In debug mode, or more specifically when the Python code is serving the staticfiles, we would store each file in a bunches
modified time, and we'd recompile whenever that value is changed.

When preprocessing happens each input file is transformed to an output file (using the standard versioning scheme). For
example, if I had a bunch that included foo.less and bar.less, each would be compiled separately, and I'd end up with
two output files: foo.VERSION.css, and bar.VERSION.css.

PostProcessors
~~~~~~~~~~~~~~

A post-process runs on pre-processed inputs and is expected to concatenate the results together into a unified file.

For example, if it runs against foo.js and bar.js, it will output bunchname.VERSION.js.


Template Usage
--------------

Similar to django-pipeline:

::

    {% staticfile 'bunchname.js' %}
