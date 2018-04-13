"""
import peewee_extras

import os
import py.test
import playhouse.db_url

url_defaults = {
    'postgres': 'postgresql://postgres@127.0.0.1/peewee_test',
    'sqlite': 'sqlite:///:memory:',
    'mysql': 'mysql://root@127.0.0.1/peewee_test'
}


def get_databases():
    # XXX: ugly code, sorry
    db_engine = os.environ.get('TEST_BACKEND', '')
    values = db_engine.split(",") if db_engine else url_defaults.keys()
    for value in values:
        assert value in url_defaults, \
            "Invalid database engine: {}".format(value)
        yield os.environ.get('TEST_BACKEND_URL', url_defaults[value])


@py.test.fixture(scope="function", params=get_databases())
def database(request):
    # determine database from env var
    db_uri = os.environ.get('DATABASE', ':memory:')
    db = playhouse.db_url.connect(db_uri)

    for model in required_models:
        model._meta.database = db

    # setup
    db.drop_tables(required_models, safe=True)
    db.create_tables(required_models)

    def teardown():
        db.drop_tables(required_models, safe=True)
        for model in required_models:
            model._meta.database = None

    request.addfinalizer(teardown)
    return db
"""
