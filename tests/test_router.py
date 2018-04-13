import peewee
import pytest
import playhouse.db_url
from peewee_extras import Model, DatabaseRouter, DatabaseManager

class TestModelBase(Model):
    name = peewee.TextField()
    class Meta:
        db_table = 'test_model'


@pytest.fixture
def TestModel():
    class TestModel(TestModelBase): pass
    return TestModel


@pytest.fixture
def dbm():
    # create manager
    dbm = DatabaseManager()

    # create db default
    db_default = playhouse.db_url.connect('sqlite:///:memory:')
    dbm['default'] = db_default

    # create db read/write pair
    db_read = playhouse.db_url.connect('sqlite:///:memory:')
    dbm['read'] = db_read
    db_write = playhouse.db_url.connect('sqlite:///:memory:')
    dbm['write'] = db_write

    return dbm


def test_database_manager(dbm):
    dbm.connect()
    dbm.disconnect()


def test_database_router(dbm):
    """
    Unit test for database routing
    """

    class DBDefault(TestModelBase): pass
    class DBRead(TestModelBase): pass
    class DBWrite(TestModelBase): pass

    class Router1(DatabaseRouter):
        def db_for_read(self, model_cls):
            if model_cls == DBRead: 
                return dbm['read']
            return None

    class Router2(DatabaseRouter):
        def db_for_write(self, model_cls):
            if model_cls == DBWrite: 
                return dbm['write']
            return None

    r1 = Router1()
    dbm.routers.add(r1)

    r2 = Router2()
    dbm.routers.add(r2)

    assert dbm.db_for_read(DBDefault) == dbm['default']
    assert dbm.db_for_read(DBRead) == dbm['read']
    assert dbm.db_for_write(DBWrite) == dbm['write']


def test_crud(dbm):
    @dbm.models.register
    class TestModel(TestModelBase):
        pass

    # ensure writes are working
    dbm.models.create_tables()
    o1 = DBDefault.create(name='hello')
    o2 = DBDefault.get(name='hello')
    assert o1.id == o2.id



def test_create_or_get(dbm):
    @dbm.models.register
    class TestModel(TestModelBase):
        pass

    # create db tables
    dbm.models.create_tables()

    o1 = TestModel.create_or_get(name='lol')
