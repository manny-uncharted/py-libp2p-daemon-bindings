p2pd_pb_path = p2pclient/pb
p2pd_pbs = $(shell find $(p2pd_pb_path) -name *.proto)
pys = $(p2pd_pbs:.proto=_pb2.py)
pyis = $(p2pd_pbs:.proto=_pb2.pyi)

# Set default to `protobufs`, otherwise `format` is called when typing only `make`
all: protobufs

help:
	@echo "🚀 py-libp2p-daemon-bindings Development Commands"
	@echo ""
	@echo "📦 Development & Setup:"
	@echo "  make dev              Install development dependencies"
	@echo "  make all              Show this help (default)"
	@echo ""
	@echo "🎨 Code Quality:"
	@echo "  make format           Format code (black + isort)"
	@echo "  make lint             Check code quality (black + isort + flake8 + mypy)"
	@echo "  make precommit        Run pre-commit hooks"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test             Run optimized test suite (unit + integration)"
	@echo "  make test-unit        Run unit tests in parallel (~1.6s)"
	@echo "  make test-integration Run integration tests sequentially (~15min)"
	@echo "  make test-all-python  Test all Python versions (3.8-3.12)"
	@echo ""
	@echo "🔧 Build & Package:"
	@echo "  make protobufs       Generate protobuf files from .proto"
	@echo "  make package         Create source distribution and wheel"
	@echo "  make clean           Remove generated protobuf files"
	@echo ""
	@echo "💡 Quick Start:"
	@echo "  make dev && make format && make lint && make test-unit"

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
	flake8 p2pclient tests setup.py --exclude="*_pb2.py,*/pb/*_pb2.py"
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

test:
	@echo "🧪  Running optimized test suite…"
	python scripts/run_tests.py

test-unit:
	@echo "⚡  Running unit tests in parallel…"
	pytest -v -n auto --timeout=180 tests/libp2p_stubs/ tests/test_p2pclient.py tests/test_datastructures.py tests/test_serialization.py tests/test_utils.py

test-integration:
	@echo "🔗  Running integration tests sequentially…"
	pytest -v -n 0 --timeout=180 tests/test_p2pclient_integration.py

test-all-python:
	@echo "🐍  Testing all Python versions (3.8-3.12)…"
	python scripts/test_all_python_versions.py

.PHONY: all help dev format lint precommit protobufs package clean test test-unit test-integration test-all-python

clean:
	rm $(pys) $(pyis)

