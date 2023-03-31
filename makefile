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

	pip install requirements_dev.txt
	pre-commit install

ci:
	@autoflake --remove-all-unused-imports -vv --ignore-init-module-imports -r .
	@echo "make format is calling for autoflake, which  will remove all unused imports listed above. Are you sure?"
	@echo "Enter to proceed. Ctr-C to abort."
	@read
	autoflake --in-place --remove-all-unused-imports  --ignore-init-module-imports -r .
	black .
	isort .
	mypy .
	flake8 .

database:
	@echo "Drop current database, remove all migrations file and generate completely new ones. Are you sure?"
	@echo "Enter to proceed. Ctr-C to abort."
	@read
	rm -f alembic/versions/*
	python tmp_database.py
	alembic revision --autogenerate
	alembic upgrade head

push:
	pre-commit run --all-files || True
	@git status
	@echo "All files listed above will be added to commit. Enter commit message to proceed. Ctr-C to abort."
	@read -p "Commit message: " COMMIT_MESSAGE; git add . ; git commit -m "$$COMMIT_MESSAGE"
	@git push

# for local testing in containers
build_run:
	docker build -t vybornyy/bart-bot .
	docker-compose up -d --force-recreate polling
	docker-compose logs -f polling



update_server: user := vybornyy
update_server: host := 158.160.11.4
update_server: workdir := bart-bot
update_server:
	@echo "## Copy files to project dir at production server ##"
	scp data/1678041517_dump.json $(user)@$(host):/home/$(user)/$(workdir)/data/
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
