help:
	@cat Makefile | grep '^## ' | cut -c4- | sed -e 's/ - /\t- /;' | column -s "$$( echo -e '\t' )" -t

## isort - Runs isort recursively on all Python files
isort:
	isort -rc phablytics

## clean - Cleans dist and build, part of build lifecycle
clean:
	rm -rf dist/*
	rm -rf build/*

## package - Create package for dist
package:
	python setup.py sdist bdist_wheel

## repackage - Runs clean and package
repackage: clean package

## install - Installs locally built package
install: package
	sh -c "pip install -U dist/phablytics-`cat VERSION`.tar.gz"

## upload - Uploads built package to PYPI
upload:
	sh -c "twine upload dist/phablytics-`cat VERSION`-py2.py3-none-any.whl"

## publish - Clean, build and publish package to PyPI
publish: repackage upload
