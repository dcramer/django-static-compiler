django-static-compiler
======================

A static files compiler (JavaScript, CSS, et all) which aims to solve two things:

1. Distributed compressed and uncompresed files with third party applications.
2. Simple compression of project-wide static files

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
            '*.js': ['uglifyjs %(in) %(out)']
        }
        precompilers: {
            '*.less': ['lessc %(in) %(out)']
        }
    }

Template Usage
--------------

Similar to django-pipeline:

::

    {% staticfile 'bunchname.js' %}


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

TODO / Questions
----------------

Some questions which need answered:

- Is there a better way to do a library's static compilation configuration?
  - e.g. we could do sentry.staticfiles (a python module), but that's kind of gross
- Are there any problems with the staticfiles finders that might conflict here?
- Is it fine to infer content type from destination file?
- What's the ideal way to handle pre/post compilers?
- What about situations where you don't want to write the output to disk?
- How can we handle project-wide staticfiles? e.g. I want to compile together sentry's XYZ and otherapp's XYZ for my project.