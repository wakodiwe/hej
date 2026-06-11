.PHONY: install uninstall devinstall devuninstall tests docs clean lint check coverage all-checks

NAME = hej

install:
	pipx install .

uninstall:
	pipx uninstall $(NAME)

venv:
	python3 -m venv venv

devinstall: venv
	venv/bin/pip install -e '.[tests,docs]'

devuninstall:
	venv/bin/pip uninstall $(NAME) -y

tests:
	venv/bin/pytest -q

docs:
	venv/bin/pdoc -o docs/api hej

lint:
	venv/bin/black src/hej tests/
	venv/bin/isort src/hej tests/

check:
	venv/bin/black --check src/hej tests/
	venv/bin/isort --check-only src/hej tests/
	venv/bin/flake8 src/hej tests/ --max-line-length=88
	venv/bin/mypy src/hej

coverage:
	venv/bin/pytest --cov=src/hej --cov-report=html --cov-report=term

all-checks: check tests coverage docs

clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
