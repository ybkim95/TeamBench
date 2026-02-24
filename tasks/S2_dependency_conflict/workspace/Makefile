.PHONY: test install

install:
	pip install -r requirements.txt
	pip install -e vendor/libfoo -e vendor/libbar

test: install
	python -m pytest tests/ -q
