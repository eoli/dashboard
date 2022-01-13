.PHONY: build

clear:
	rm -rf build dist main.spec
	rm -rf __pycache__

build:
	pyinstaller -F main.py
	cp config.json dist/
	cp logo.png dist/

run:
	python3 main.py

