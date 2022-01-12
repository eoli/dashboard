clear:
	rm -rf build dist main.spec
	rm -rf __pycache__

build:
	pyinstaller -F main.py

run:
	python3 main.py