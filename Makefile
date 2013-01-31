build:
	pip install -e .
	pip install "file://`pwd`#egg=django-static-compiler[tests]"

test: build
	py.test tests