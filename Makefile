VENV_ACTIVATE = source venv/bin/activate

run:
	PYTHONPATH=src uvicorn app.main:app --reload

test:
	$(VENV_ACTIVATE) && pytest

install:
	$(VENV_ACTIVATE) && pip install -r requirements.txt 