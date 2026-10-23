.PHONY: install test run lint clean docker-build

install:
	pip install -r requirements.txt

run:
	python3 -m app

test:
	python3 -m pytest -v

lint:
	python3 -m pytest tests/test_guard_security.py

docker-build:
	docker build -t ask-the-numbers .

clean:
	rm -rf __pycache__ app/**/__pycache__ tests/__pycache__ .pytest_cache data/sales.db
