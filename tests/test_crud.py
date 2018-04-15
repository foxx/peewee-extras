import os
import pickle

import peewee
import peewee_extras as pe
import pytest
import playhouse

from faker import Faker
from pprint import pprint
from tabulate import tabulate


####################################################################
# Test data loader
####################################################################

class ResultStore:
    """
    Ghetto implementation of betamax/VCR for static data
    """
    def __init__(self, record_mode, data_dir):
        assert isinstance(record_mode, bool)
        assert isinstance(data_dir, str)

        self.record_mode = record_mode
        self.data_dir = data_dir

    def check(self, name, value):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        fname = '{}.pickle'.format(name)
        fpath = os.path.join(self.data_dir, fname)

        if not os.path.exists(fpath):
            if self.record_mode is False:
                raise Exception("Result missing and record mode disabled")

            with open(fpath, 'wb') as fh:
                pickle.dump(value, fh)
                return value
        else:
            with open(fpath, 'rb') as fh:
                return pickle.load(fh)


data_dir = os.path.join(os.path.dirname(__file__), 'data')
rs = ResultStore(record_mode=True, data_dir=data_dir)


####################################################################
# Fixtures and bases
####################################################################

class DatabaseManager(pe.DatabaseManager):
    def populate_models(self):
        """
        Populate test models with (predictable) fake data
        """
        fake = Faker()
        fake.seed(0)

        cities = ['Portland', 'Washington', 'Seattle', 'Mountain View']

        items = []
        for x in range(100):
            city = cities[x % len(cities)]
            items += [dict(name=fake.name(), city=city)]
        Person.insert_many(items).execute()
        assert Person.select().count() == 100


@pytest.fixture
def dbm():
    # create manager
    dbm = DatabaseManager()

    # create db default
    dbm.register('default', 'sqlite:///:memory:')
    
    # register models
    dbm.models.register(Person)
    dbm.models.register(CompoundModel)

    dbm.connect()
    dbm.models.create_tables()
    dbm.populate_models()
    yield dbm
    dbm.disconnect()


@pytest.fixture
def faker():
    fake = Faker()
    fake.seed(0)
    return fake


####################################################################
# Test models
####################################################################

class Person(pe.Model):
    name = peewee.TextField(null=False)
    city = peewee.TextField(null=False)


class CompoundModel(pe.Model):
    field1 = peewee.IntegerField()
    field2 = peewee.IntegerField()
    
    class Meta:
        primary_key = peewee.CompositeKey("field1", "field2")



####################################################################
# Test CRUD
####################################################################


class TestPrimaryKeyPagination:
    
    def generate(self, *args, **kwargs):
        query = pe.PrimaryKeyPagination.paginate_query(*args, **kwargs)
        return [ r.__data__ for r in query ]

    def test_limit(self, dbm):
        """Test query limiting"""
        query = Person.select()

        # 100 items, no offset, no user sorting
        results = self.generate(query=query, offset=None, count=100)
        expected = rs.check('test_limit_1', results)
        assert results == expected

        # 50 items, no offset, no user sorting
        results = self.generate(query=query, offset=None, count=50)
        assert len(results) == 50
        expected = rs.check('test_limit_2', results)
        assert results == expected

    def test_sort(self, dbm):
        query = Person.select()

        # 100 items, no offset, sort by name(asc)
        sort = [('name', 'asc')]
        results = self.generate(query=query, offset=None, count=100, sort=sort)
        expected = rs.check('test_sort_1', results)
        assert results == expected
 
        # 100 items, no offset, sort by name(desc)
        sort = [('name', 'desc')]
        results = self.generate(query=query, offset=None, count=100, sort=sort)
        expected = rs.check('test_sort_2', results)
        assert results == expected

        # 100 items, no offset, sorted
        sort = [('city', 'asc'), ('name', 'asc')]
        results = self.generate(query=query, offset=None, count=100, sort=sort)
        expected = rs.check('test_sort_3', results)
        assert results == expected

        # 100 items, no offset, sorted
        sort = [('city', 'asc'), ('name', 'desc')]
        results = self.generate(query=query, offset=None, count=100, sort=sort)
        expected = rs.check('test_sort_4', results)
        assert results == expected

    def test_offset(self, dbm):
        query = Person.select()

        # 100 items (expect 50), offset 50, sort by name(asc)
        sort = [('name', 'asc')]
        results = self.generate(query=query, offset=51, count=100, sort=sort)
        assert len(results) == 50
        expected = rs.check('test_offset_1', results)
        assert results == expected

        # 100 items (expect 50), offset 50, no sort (defaults to pk sort)
        results = self.generate(query=query, offset=51, count=100)
        assert len(results) == 50
        expected = rs.check('test_offset_2', results)
        assert results == expected

        #print(tabulate(results, headers="keys")); assert False


