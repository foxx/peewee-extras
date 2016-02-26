from peewee_extras import Model
from peewee import SqliteDatabase

def test_database_callable():
    db = SqliteDatabase(':memory:')

    class A(Model):
        class Meta:
            database = db
    
    class B(Model):
        class Meta:
            database = lambda meta: db

    assert A._meta.database == db
    assert B._meta.database == db



'''
import os
import test
import tempfile
import py.test
import playhouse.db_url

from uuid import uuid4
from unittest import TestCase

from peewee_extras import monkeypatch
monkeypatch()

from peewee_extras import (Model, HashField, OrderedUUIDField,
    ModelManager, DatabaseManager, JSONField)
from peewee import SqliteDatabase, TextField




####################################################################
# Helpers
####################################################################

def all_databases(func):
    """Decorator for testing against all database types"""
    databases = [
        'sqlite:///:memory:',
        'sqlite:////tmp/lalal.sql',
        'postgresql://127.0.0.1/example',
        'mysql://127.0.0.1/example']
    databases = [ playhouse.db_url.connect(url) for url in databases ]
    return pytest.mark.parametrize("database", databases)(func)




####################################################################
# Tests
####################################################################

class TestModelManager(object):
    def test_register(self):
        manager = ModelManager()
        manager.register(Model)
        with py.test.raises_regexp(ValueError, r"^Model already registered"):
            manager.register(Model)
        with py.test.raises(TypeError):
            manager.register(object)

    def test_create_destroy(self):
        db = playhouse.db_url.connect('sqlite:///:memory:')
        class ExampleModel(Model):
            class Meta:
                database = db

        manager = ModelManager()
        manager.register(ExampleModel)
        manager.create_tables()
        manager.create_tables(drop_existing=True)
        manager.destroy_tables()

    def test_refetch(self):
        class ExampleModel(Model):
            value = TextField()

        manager = ModelManager()
        manager.register(ExampleModel)
        manager.create_tables()

        v1 = ExampleModel.create(value='v1')
        v2 = ExampleModel.create(value='v2')

        assert v1.id
        assert v2.id
        assert v1.id != v2.id

        v1r = v1.refetch()
        assert v1r.id == v1.id
        assert v1r.value == v1.value


class TestDatabaseManager(object):
    def test_connect_disconnect(self):
        database = playhouse.db_url.connect('sqlite:///:memory:')
        manager = DatabaseManager()
        manager['default'] = database
        assert manager['default'] == database

        manager.connect_all()
        assert database.is_closed() is False

        manager.disconnect_all()
        assert database.is_closed() is True


class TestSqliteDatabaseMixin(object):
    def test_create_destroy_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as fh:
            url = "sqlite:///{}".format(fh.name)
            os.unlink(fh.name)
            assert os.path.exists(fh.name) is False

            db = playhouse.db_url.connect(url)
            db.create_database()
            assert db.database_list == [('main', fh.name)]
            assert os.path.exists(fh.name) is True

            db.destroy_database()
            assert os.path.exists(fh.name) is False

    def test_in_memory(self):
        db = SqliteDatabase(database=":memory:")
        db.create_database()
        assert db.database_list == [('main', '')]
        db.destroy_database()


class TestModel(object):
    pass


####################################################################
# Fields
####################################################################

def test_json_field():
    class JSONModel(Model):
        value = JSONField()
        class Meta:
            database = SqliteDatabase(database=':memory:')
    JSONModel.create_table()

    values = [[1,2,3], dict(a=1, b=2), 'helloworld', 1234]
    for value in values:
        m = JSONModel()
        m.value = value
        m.save()
        assert m.value == value

        m = m.get(id=m.id)
        assert m.value == value


def test_hash_field():
    class HashModel(Model):
        value = HashField(rounds=1000)
        class Meta:
            database = SqliteDatabase(database=':memory:')
    HashModel.create_table()

    values = ['str1234', b'bytes1234']
    for value in values:
        # try without key
        m = HashModel()
        m.value = value
        m.save()
        m = m.get(id=m.id)
        assert m.value.check(value) is True
        assert m.value.check('invalid') is False

        # try with key
        m._meta.fields['value'].key = 'helloworld'
        m = HashModel()
        m.value = value
        m.save()
        m = m.get(id=m.id)
        assert m.value.check(value) is True
        assert m.value.check('invalid') is False

        # try with bad key
        m._meta.fields['value'].key = 'somethingelse'
        assert m.value.check(value) is False
        assert m.value.check('invalid') is False    


'''