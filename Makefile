.PHONY: build install

build:
	python setup.py bdist_wheel sdist

install:
	pip install --force-reinstall dist/*.whl
