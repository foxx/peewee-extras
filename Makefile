clean:
	rm -rf *.egg *.egg-info .tox .benchmarks .cache pytestdebug.log \
		.coverage dist build .eggs
	find . -name "*.pyc" -exec rm -rf {} \;
	find . -name "__pycache__" -exec rm -rf {} \;

submit:
	python setup.py sdist upload

setup_databases:
	psql -c 'drop database if exists peewee_test;' -U postgres
	psql -c 'create database peewee_test;' -U postgres
	mysql -u root -e 'drop database if exists peewee_test;'
	mysql -u root -e 'create database peewee_test;'

