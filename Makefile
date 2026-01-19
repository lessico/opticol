.PHONY: format lint test

format:
	black opticol tests

lint:
	black --check opticol tests
	mypy opticol tests
	pylint opticol tests

test:
	pytest tests
