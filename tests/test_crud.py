import peewee
import peewee_extras as pe
import pytest
import playhouse

####################################################################
# Fixtures and bases
####################################################################

class Animal(pe.Model):
    tag = peewee.IntegerField(null=False)
    species = peewee.TextField(null=False)


class CompoundModel(pe.Model):
    field1 = peewee.IntegerField()
    field2 = peewee.IntegerField()
    
    class Meta:
        primary_key = peewee.CompositeKey("field1", "field2")


@pytest.fixture
def dbm():
    # create manager
    dbm = pe.DatabaseManager()

    # create db default
    db_default = playhouse.db_url.connect('sqlite:///:memory:')
    dbm['default'] = db_default
    
    # register models
    dbm.models.register(SingleModel)
    dbm.models.register(CompoundModel)

    dbm.connect()
    dbm.models.create_tables()
    yield dbm
    dbm.disconnect()



####################################################################
# Test CRUD
####################################################################

class TestPrimaryKeyPagination:
    def generate_single_rows(self):
        """Generate 100 rows of predictable data"""

        # create 10 cats
        items = [ dict(label='a') for x in range(50) ]
        items += [ dict(label='b') for x in range(50) ]
        SingleModel.insert_many(items).execute()
        assert SingleModel.select().count() == 100

    def generate_compound_rows(self):
        """Insert 100 predictable compound items"""
        items = [ dict(field1=x, field2=x%2) for x in range(100) ]
        CompoundModel.insert_many(items).execute()
        assert CompoundModel.select().count() == 100

    def test_offset_query_missing_pk(self, dbm):
        self.generate_compound_rows()
        # TODO: implement (should fail)
 
    def test_offset_query_compound_pk(self, dbm):
        self.generate_compound_rows()
        # TODO: implement (should fail)
   
    def test_offset_query_single(self, dbm):
        """Test query offset on single PK"""
        self.generate_single_rows()
        query = SingleModel.select()

        # expect 50 items starting from id=50
        squery = pe.PrimaryKeyPagination.paginate_query(
            query=query, offset=51, count=100)
        results = list(squery.tuples())
        assert len(results) == 50
        assert results[0] == (51, 'b')
        assert results[-1] == (100, 'b')

    def test_sort_asc_single(self, dbm):
        """Test ascending sorting with single field"""
        self.generate_single_rows()

        query = SingleModel.select()
        sort_params = [('label', 'asc')]
        query = pe.PrimaryKeyPagination.paginate_query(
            query=query, offset=0, count=100, sort_params=sort_params)
        results = list(query.tuples())
        assert results[0] == (1, 'a')
        assert results[-1] == (100, 'b')

    def test_sort_desc_single(self, dbm):
        """Test descending sorting with single field"""
        self.generate_single_rows()

        query = SingleModel.select()
        sort_params = [('label', 'desc')]
        query = pe.PrimaryKeyPagination.paginate_query(
            query=query, offset=0, count=100, sort_params=sort_params)
        results = list(query.tuples())
        #print(query.sql())
        #print(results)
        assert results[0] == (100, 'b')
        assert results[-1] == (1, 'a')

    def test_sort_multi(self, dbm):
        """Test sorting with multiple fields"""
        self.generate_single_rows()

        # asc/asc
        query = SingleModel.select()
        sort_params = [('label', 'asc'), ('id', 'asc')]
        query = pe.PrimaryKeyPagination.paginate_query(
            query=query, offset=0, count=100, sort_params=sort_params)
        results = list(query.tuples())
        assert results[0] == (1, 'a')
        assert results[-1] == (100, 'b')

        # asc/desc
        query = SingleModel.select()
        sort_params = [('label', 'asc'), ('id', 'desc')]
        query = pe.PrimaryKeyPagination.paginate_query(
            query=query, offset=0, count=100, sort_params=sort_params)
        results = list(query.tuples())
        assert results[0] == (50, 'a')
        assert results[50] == (100, 'b')
        assert results[-1] == (51, 'b')

