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

alembic-migration-dev:
	export APP_ENV=development && \
	alembic revision --autogenerate -m "New migration"

alembic-migration-prod:
	export APP_ENV=production && \
	alembic revision --autogenerate -m "New migration"

alembic-upgrade-dev:
	export APP_ENV=development && \
	alembic upgrade head

alembic-upgrade-prod:
	export APP_ENV=production && \
	alembic upgrade head


alembic-downgrade-dev:
	export APP_ENV=development && \
	alembic downgrade -1

alembic-downgrade-prod:
	export APP_ENV=production && \
	alembic downgrade -1

alembic-current-dev:
	export APP_ENV=development && \
	alembic current

alembic-current-prod:
	export APP_ENV=production && \
	alembic current

alembic-history-dev:
	export APP_ENV=development && \
	alembic history

alembic-history-prod:
	export APP_ENV=production && \
	alembic history