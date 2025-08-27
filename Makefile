# Use the virtualenv's python
PYTHON=python

seed-dump:
	$(PYTHON) manage.py dumpdata core.Brand core.Agency core.Ad core.Tag --indent 2 > seed.json

seed-load:
	$(PYTHON) manage.py loaddata seed.json

migrate:
	$(PYTHON) manage.py makemigrations
	$(PYTHON) manage.py migrate

run:
	$(PYTHON) manage.py runserver