VENV_ACTIVATE = source venv/bin/activate

run-dev:
	export APP_ENV=development && \
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	export APP_ENV=production && \
	uvicorn app.main:app --host 0.0.0.0 --port 8000

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

install:
	pip install -r requirements.txt 

alembic-init:
	alembic init alembic

alembic-migration:
	export APP_ENV=development && \
	alembic revision --autogenerate -m "New migration"

alembic-upgrade:
	export APP_ENV=development && \
	alembic upgrade head

alembic-downgrade:
	export APP_ENV=development && \
	alembic downgrade -1

alembic-current:
	export APP_ENV=development && \
	alembic current

alembic-history:
	export APP_ENV=development && \
	alembic history