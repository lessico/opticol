.PHONY: format lint test

format:
	black opticol tests benchmarks

lint:
	black --check opticol tests benchmarks
	mypy opticol tests benchmarks
	pylint opticol

test:
	pytest
