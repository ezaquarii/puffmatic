
test:
	pytest puffmatic

cov:
	pytest --cov=puffmatic --cov-report=lcov --cov-report=html puffmatic

tags:
	find . -type f -name "*.py" | xargs etags

build:
	python3 -m build

sdist:
	python3 -m build --sdist

upload:
	python3 -m twine check dist/*
	python3 -m twine upload --repository testpypi dist/*

bootstrap:
	python3 -m venv venv
	./venv/bin/pip install -e '.[dev]'

clean:
	rm -rf .pytest_cache
	rm -rf puffmatic.egg-info
	rm -rf build
	rm -rf dist
	rm -rf example.com/output
	rm -rf venv
	rm -f TAGS
	rm -f .coverage
	rm -f coverage.lcov
