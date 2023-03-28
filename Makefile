install_reqs:
		pip install -r requirements.txt
run:
		python3 ipset-util.py $(ARGS)
build:
		pyinstaller -F ipset-util.py