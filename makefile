# This file presents CLI shortcuts.
# Go there to find more details: https://makefiletutorial.com/#variables


.PHONY: venv	# to ignore such folder makefile get deal with
venv: ver := 3.10
venv: msg1 := "Virtual environment already exist. Should be activated."
venv: msg2 := "Virtual environment created. Activate it to use."
venv:
	@if [ -d "./venv/" ]; \
		then echo "$(msg1)"; \
		else \
			python$(ver) -m venv venv; \
			echo "$(msg2)"; \
	fi;

install:
	@echo "Is virtual environment activated? (venv) "
	@echo "Enter to proceed. Ctr-C to abort."
	@read
	@pip3 install --upgrade pip;

	pip install black mypy isort
	pip install flake8 pep8-naming flake8-broken-line flake8-return flake8-isort Flake8-pyproject
	pip install autoflake==1.7.8
	pip install sqlalchemy[asyncio] asyncpg psycopg2-binary
	pip install types-PyYAML

	pip install pre-commit
	pre-commit install


format:
	@autoflake --remove-all-unused-imports -vv --ignore-init-module-imports -r .
	@echo "make format is calling for autoflake, which  will remove all unused imports listed above. Are you sure?"
	@echo "Enter to proceed. Ctr-C to abort."
	@read
	autoflake --in-place --remove-all-unused-imports  --ignore-init-module-imports -r .
	black .
	isort .
	mypy .
	flake8 .


push:
	pip freeze > requirements.txt
	cp .github/workflows/github-ci-cd.yml .
	@git status
	@echo "All files listed above will be added to commit. Enter commit message to proceed. Ctr-C to abort."
	@read -p "Commit message: " COMMIT_MESSAGE; git add . ; git commit -m "$$COMMIT_MESSAGE"
	@git push


update_server: user := vybornyy
update_server: host := 158.160.24.209
update_server: workdir := bart-bot
update_server:
	@echo "## Copy files to project dir at production server ##"
	scp data/bart-bot.dump.json $(user)@$(host):/home/$(user)/$(workdir)/data/
	scp docker-compose.yml $(user)@$(host):/home/$(user)/$(workdir)/
	scp build.env $(user)@$(host):/home/$(user)/$(workdir)/


webhook: token := 5382265508:AAGQmTrWJPyu5sS5NRkSyVBzHi9Fv8sj6z8
webhook: url := https://functions.yandexcloud.net/d4e5c65sh996i1k7ap7g
webhook:
	curl \
  		--request POST \
  		--url https://api.telegram.org/bot$(token)/setWebhook \
  		--header 'content-type: application/json' \
  		--data '{"url": "$(url)"}'
