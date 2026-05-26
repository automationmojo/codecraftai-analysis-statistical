.PHONY: help test lint format coverage clean dist-clean dist-build dist-publish userguide

help:
	@echo "Targets:"
	@echo "  test         Run the singlehost testbase suite into .output/"
	@echo "  lint         Run ruff against source/packages and source/testroots"
	@echo "  format       Apply ruff's safe auto-fixes"
	@echo "  coverage     Run tests under coverage and emit a report"
	@echo "  userguide    Build the userguide with Sphinx into docs/_build/"
	@echo "  dist-build   poetry build (sdist + wheel)"
	@echo "  dist-publish poetry publish"
	@echo "  dist-clean   Remove dist/"
	@echo "  clean        Remove caches, dist, and test output"

test:
	. ./.venv/bin/activate && \
	testbase testing run --root ./source/testroots/automojo \
	    --includes=automojo.tests.singlehost --output=./.output

lint:
	. ./.venv/bin/activate && \
	ruff check source/packages source/testroots source/examples

format:
	. ./.venv/bin/activate && \
	ruff check --fix source/packages source/testroots source/examples

coverage:
	. ./.venv/bin/activate && \
	coverage run -m testbase testing run --root ./source/testroots/automojo \
	    --includes=automojo.tests.singlehost --output=./.output && \
	coverage report -m

userguide:
	. ./.venv/bin/activate && \
	sphinx-build -b html userguide docs/_build

dist-clean:
	rm -fr dist

dist-build:
	poetry build

dist-publish:
	poetry publish

clean: dist-clean
	rm -fr .output .output-* docs/_build
	find . -name __pycache__ -type d -exec rm -fr {} +
