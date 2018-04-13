import peewee
import pytest
import playhouse.db_url
from peewee_extras import Model, DatabaseRouter, DatabaseManager

class TestModelBase(Model):
    name = peewee.TextField(null=True)
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

    db_other = playhouse.db_url.connect('sqlite:///:memory:')
    dbm['other'] = db_other
    
    return dbm


def test_database_manager(dbm):
    dbm.connect()
    dbm.disconnect()


def test_database_router(dbm):
    """
    Unit test for database routing
    """

    class DBDefault(TestModelBase): pass
    class DBOther(TestModelBase): pass

    class RouterDefault(DatabaseRouter):
        pass

    class RouterOther(DatabaseRouter):
        def get_database(self, model_cls):
            if model_cls == DBOther:
                return dbm['other']
            return None

    r1 = RouterDefault()
    dbm.routers.add(r1)

    r2 = RouterOther()
    dbm.routers.add(r2)

    assert dbm.get_database(DBDefault) == dbm['default']
    assert dbm.get_database(DBOther) == dbm['other']


def test_database_router_model(dbm):

    @dbm.models.register
    class TestModel(TestModelBase):
        pass

    assert TestModel._meta.database == dbm['default']


def test_crud(dbm):
    @dbm.models.register
    class TestModel(TestModelBase):
        pass

    # ensure writes are working
    dbm.models.create_tables()
    o1 = TestModel.create(name='hello')
    o2 = TestModel.get(name='hello')
    assert o1.id == o2.id


def test_create_or_get(dbm):
    @dbm.models.register
    class TestModel(TestModelBase):
        pass

    # create db tables
    dbm.models.create_tables()

    o1, created = TestModel.create_or_get(id=1)
    assert created is True

    o1, created = TestModel.create_or_get(id=1)
    assert created is False

def test_get_or_none(dbm):
    @dbm.models.register
    class TestModel(TestModelBase):
        pass

    # create db tables
    dbm.models.create_tables()

    o = TestModel.get_or_none(id=1)
    assert o is None

    o1 = TestModel.create(id=1)
    o2 = TestModel.get_or_none(id=1)
    assert o1 == o2
    
