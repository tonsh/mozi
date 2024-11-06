.PHONY: lint

clean:
	@find . -name "*.pyc" -exec rm -f {} +
	@find . -name "__pycache__" -exec rm -rf {} +
	@find . -name ".pytest_cache" -exec rm -rf {} +

pylint: clean
	@pylint --rcfile=.pylintrc --recursive=y .

flake8: clean
	@flake8 . --count --max-complexity=10 --max-line-length=200 --ignore=F401,W504 --statistics --show-source

lint: pylint flake8

test: clean
	@pytest -c pytest.ini

check: lint test
