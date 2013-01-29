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
        'js': {
            'type': 'text/javascript',
            'src': ['foo.js'],
            'dst': ['foo.min.js'],
        }
    }

Template Usage
--------------

Similar to django-pipeline:

::

    {% staticfile 'bunchname' %}


Staticfiles Collection
----------------------

Assuming something like the application staticfiles finder, it would iterate all applications, and look for the
application's configuration.

- If DEBUG was enabled, we would return uncompiled resources
- Else if compiled resources available, return them
- Else if compilers available (e.g. lessc), compile resources
- Else return uncompiled resources

This would both influence what ends up in collectstatic as well as what the staticfile templatetags would return. It's
likely we'd generate a manifest (similar to compressor) which described the results of this action.

TODO / Questions
----------------

Some questions which need answered:

- Is there a better way to do a library's static compilation configuration?
  - e.g. we could do sentry.staticfiles (a python module), but that's kind of gross
- Are there any problems with the staticfiles finders that might conflict here?
- How should types be handled?
- What's the ideal way to handle pre/post compilers?