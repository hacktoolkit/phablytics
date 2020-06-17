help:
	@cat Makefile | grep '^## ' | cut -c4- | sed -e 's/ - /\t- /;' | column -s "$$( echo -e '\t' )" -t

## isort - run isort recursively on all Python files
isort:
	isort -rc phablytics

## clean - part of build lifecycle
clean:
	rm -rf dist/*
	rm -rf build/*

## package - create package for dist
package:
	python3 setup.py sdist bdist_wheel

## repackage - runs clean and package
repackage: clean package

## install - installs locally built package
install: package
	sh -c "pip install -U dist/phablytics-`cat VERSION`.tar.gz"

## upload - uploads built package to PYPI
upload:
	sh -c "twine upload dist/phablytics-`cat VERSION`-py2.py3-none-any.whl"
