.PHONY: install seed backend frontend test build

install:
	npm install
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

seed:
	.venv/bin/python -m backend.seed_demo

backend:
	PORT=5000 .venv/bin/python -m backend

frontend:
	npm run dev:frontend

test:
	.venv/bin/pytest
	npm test

build:
	npm run build
