help:
	@cat Makefile | grep '^## ' | cut -c4- | sed -e 's/ - /\t- /;' | column -s "$$( echo -e '\t' )" -t

## isort - run isort recursively on all Python files
isort:
	isort -rc phablytics
