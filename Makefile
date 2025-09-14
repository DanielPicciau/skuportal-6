SHELL := /bin/sh

.PHONY: up down build logs dev venv migrate run mise-fix

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f

# Local dev without Docker (uses system Python)
venv:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt

migrate:
	. .venv/bin/activate && python manage.py migrate

run:
	. .venv/bin/activate && python manage.py runserver

dev: venv migrate run

# Fix mise to compile Python instead of downloading .zst archives
mise-fix:
	mise trust || true
	mise settings set python_compile 1
	rm -rf ~/.local/share/mise/downloads/python/3.12.11 || true
	mise install python@3.12
	mise exec python -- python -V

