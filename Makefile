LIBNAME:=openoligo
EXECNAME:=main.py

help:
	@echo "Usage: make [target]"
	@echo
	@echo "Targets:"
	@echo "  all 		Run linting, type checking and tests 	<== If in doubt, use this target"
	@echo "  run 		run the application"
	@echo "  lint 		run linter"
	@echo "  type 		run type checker"
	@echo "  test 		run tests"
	@echo "  help 		print this help"

all: lint test

run:
	@poetry run python $(EXECNAME)

lint:
	poetry run pylint $(LIBNAME)
	poetry run flake8 $(LIBNAME)
	poetry run black $(LIBNAME)
	poetry run isort $(LIBNAME)

type:
	poetry run mypy $(LIBNAME)

test: type
	poetry run pytest 

publish:
	poetry publish --build

.PHONY: ghtest lint type help run test publish
