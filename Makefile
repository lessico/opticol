.PHONY: format lint test bench

format:
	black opticol tests benchmarks

lint:
	black --check opticol tests benchmarks
	mypy opticol tests benchmarks
	pylint opticol

test:
	pytest

bench:
	@ESCAPED=$$(python3 -c "import re,sys;print(re.escape(sys.argv[1]))" "$(PATTERN)"); \
	pytest benchmarks/ --benchmark-only --regex ".*$$ESCAPED.*" $(if $(SAVE),--benchmark-save="$(SAVE)")
