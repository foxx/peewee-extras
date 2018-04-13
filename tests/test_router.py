import peewee
import pytest
import playhouse.db_url

from freezegun import freeze_time
from peewee_extras import (Model, DatabaseRouter, DatabaseManager, 
    TimestampModelMixin)

####################################################################
# Fixtures and bases
####################################################################

class PlayModelBase(Model):
    name = peewee.TextField(null=True)
    class Meta:
        db_table = 'test_model'


@pytest.fixture
def dbm():
    # create manager
    dbm = DatabaseManager()

    # create db default
    db_default = playhouse.db_url.connect('sqlite:///:memory:')
    dbm['default'] = db_default

    db_other = playhouse.db_url.connect('sqlite:///:memory:')
    dbm['other'] = db_other
    
    dbm.connect()
    yield dbm
    dbm.disconnect()


@pytest.fixture
def PlayModel(dbm):
    @dbm.models.register
    class PlayModel(PlayModelBase): 
        pass
    
    assert PlayModel._meta.database == dbm['default']
    dbm.models.create_tables()
    return PlayModel

####################################################################
# Model manager test
####################################################################

def test_mm_destroy_tables(dbm, PlayModel):
    dbm.models.destroy_tables()

def test_mm_already_registered(dbm, PlayModel):
    with pytest.raises(RuntimeError):
        dbm.models.register(PlayModel)


####################################################################
# Router test
####################################################################

def test_database_router(dbm):
    """
    Unit test for database routing
    """

    class DBDefault(PlayModelBase): pass
    class DBOther(PlayModelBase): pass

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



####################################################################
# Model tests
####################################################################

def test_update_instance(dbm, PlayModel):
    o1 = PlayModel.create(name='hello')
    o1.update_instance(name='world')
    assert o1.refetch().name == 'world'


def test_crud(dbm, PlayModel):
    # ensure writes are working
    o1 = PlayModel.create(name='hello')
    o2 = PlayModel.get(name='hello')
    assert o1.id == o2.id


def test_refetch(dbm, PlayModel):
    o1 = PlayModel.create(id=1)
    o2 = o1.refetch()
    assert o1 == o2


def test_refetch_does_not_exist(dbm, PlayModel):
    o1 = PlayModel.create(id=1)
    o1.delete().execute()
    with pytest.raises(PlayModel.DoesNotExist):
        o1.refetch()


def test_create_or_get(dbm, PlayModel):
    o1, created = PlayModel.create_or_get(id=1)
    assert created is True

    o1, created = PlayModel.create_or_get(id=1)
    assert created is False


def test_get_or_none(dbm, PlayModel):
    o = PlayModel.get_or_none(id=1)
    assert o is None

    o1 = PlayModel.create(id=1)
    o2 = PlayModel.get_or_none(id=1)
    assert o1 == o2


def test_get_primary_key_ref(dbm, PlayModel):

    o1 = PlayModel.create(id=1)
    assert o1.get_primary_key_ref() == {'id': 1}


####################################################################
# Field tests
####################################################################

import peewee
import datetime

def test_timestamp_model(dbm):
    @dbm.models.register
    class PlayModel(TimestampModelMixin, PlayModelBase):
        pass

    dbm.models.create_tables()
 
    dt = datetime.datetime(2018, 1, 1, 0, 0, 0)
    with freeze_time(dt):
        o1 = PlayModel.create(name='hello')
        assert o1.created == dt

