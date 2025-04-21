VENV_ACTIVATE = source venv/bin/activate

run:
	$(VENV_ACTIVATE) && uvicorn main:app --reload

test:
	$(VENV_ACTIVATE) && pytest

install:
	$(VENV_ACTIVATE) && pip install -r requirements.txt 