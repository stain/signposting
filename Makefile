all: test

build: setup.py src tests
	tox

test: build

install:
	pip install .
