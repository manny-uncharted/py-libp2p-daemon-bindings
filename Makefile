p2pd_pb_path = p2pclient/pb
p2pd_pbs = $(shell find $(p2pd_pb_path) -name *.proto)
pys = $(p2pd_pbs:.proto=_pb2.py)
pyis = $(p2pd_pbs:.proto=_pb2.pyi)

# Set default to `protobufs`, otherwise `format` is called when typing only `make`
all: protobufs

dev:
	@echo "🔌  Installing development dependencies…"
	pip install -e '.[dev]'

format:
	@echo "➡️  Running code formatters…"
	black p2pclient tests setup.py
	isort p2pclient tests setup.py

lint:
	@echo "🔍  Checking code style & quality…"
	black --check p2pclient tests setup.py
	isort --check-only p2pclient tests setup.py
	flake8 p2pclient tests setup.py
	mypy -p p2pclient --config-file mypy.ini


precommit:
	@echo "🔌  Running pre‑commit hooks…"
	pre-commit run --all-files

protobufs: $(pys)

%_pb2.py: %.proto
	protoc --python_out=. --mypy_out=. $<


package:
	# create a source distribution
	python setup.py sdist
	# create a wheel
	python setup.py bdist_wheel

.PHONY: all format lint precommit protobufs package clean

clean:
	rm $(pys) $(pyis)

