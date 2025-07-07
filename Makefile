# Makefile for building and managing the Python package

PACKAGE_NAME := minipam
PYTHON := python3
PIP := pip3

.PHONY: all build deps test clean

all: build

build: deps
	$(PYTHON) -m build

clean-build:
	rm -rf dist
	$(PYTHON) -m build

install-build: clean-build
	$(PIP) uninstall -y $(PACKAGE_NAME)
	$(PIP) install dist/$(PACKAGE_NAME)-*.whl

install-dev:
	$(PIP) install -e .

deps:
	$(PIP) install -r requirements.txt

test:
	$(PYTHON) -m unittest discover -s tests

clean:
	rm -rf build dist
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -f {} +