VENV_ACTIVATE = source venv/bin/activate

run:
	uvicorn app.main:app --reload

test:
	pytest

install:
	pip install -r requirements.txt 

alembic-init:
	alembic init alembic

alembic-migration:
	alembic revision --autogenerate -m "New migration"

alembic-upgrade:
	alembic upgrade head

alembic-downgrade:
	alembic downgrade -1

alembic-current:
	alembic current

alembic-history:
	alembic history