import peewee
import datetime
from peewee import DateTimeField


####################################################################
# Model manager
####################################################################

class ModelManager(list):
    """Handles model registration"""

    def __init__(self, database_manager):
        self.dbm = database_manager

    def create_tables(self):
        """Create database tables"""
        for cls in self:
            cls.create_table(fail_silently=True)

    def destroy_tables(self):
        """Destroy database tables"""
        for cls in self:
            cls.drop_table(fail_silently=True)

    def register(self, model_cls):
        """Register model(s) with app"""
        assert issubclass(model_cls, peewee.Model)
        assert not hasattr(model_cls._meta, 'database_manager')
        if model_cls in self:
            raise RuntimeError("Model already registered")
        self.append(model_cls)
        model_cls._meta.database = self.dbm
        return model_cls


####################################################################
# DB manager
####################################################################

# XXX: improve KeyError message
class DatabaseManager(dict):
    """Database manager"""

    def __init__(self):
        self.routers = set()
        self.models = ModelManager(database_manager=self)

    def connect(self):
        """Create connection for all databases"""
        for name, connection in self.items():
            connection.connect()

    def disconnect(self):
        """Disconnect from all databases"""
        for name, connection in self.items():
            if not connection.is_closed():
                connection.close()

    def get_database(self, model):
        """Find matching database router"""
        for router in self.routers:
            r = router.get_database(model)
            if r is not None:
                return r
        return self.get('default')


####################################################################
# Database routers
####################################################################

class DatabaseRouter(object):
    def get_database(self, model):
        return None


####################################################################
# Model
####################################################################


class Metadata(peewee.Metadata):
    _database = None

    @property
    def database(self):
        if isinstance(self._database, DatabaseManager):
            db = self._database.get_database(self)
            if db: return db
        return self._database

    @database.setter
    def database(self, value):
        self._database = value


class Model(peewee.Model):
    """Custom model"""

    class Meta:
        model_metadata_class = Metadata

    def update_instance(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.save()

    @classmethod
    def create_or_get(self, **kwargs):
        with self.atomic():
            try:
                return self.create(**kwargs), True
            except peewee.IntegrityError:
                return self.get(**kwargs), False

    @classmethod
    def get_or_none(cls, **kwargs):
        """
        XXX: needs unit test
        """
        try:
            return cls.get(**kwargs)
        except cls.DoesNotExist:
            return None

    @classmethod
    def atomic(self):
        """Shortcut method for creating atomic context"""
        return self._meta.database.atomic()
    
    def to_cursor_ref(self):
        """Returns dict of values to uniquely reference this item"""
        fields = self._meta.get_primary_keys()
        assert fields
        values = {field.name:self.__data__[field.name] for field in fields}
        return values

    @classmethod
    def from_cursor_ref(self, cursor):
        """Returns model instance from unique cursor reference"""
        return self.get(**cursor)

    def refetch(self):
        """
        Return new model instance with fresh data from database
        Only works on models which have a primary or compound key
        See https://github.com/coleifer/peewee/issues/638

        XXX: Add support for models without PK
        """
        ref = self.to_cursor_ref()
        return self.from_cursor_ref(ref)


####################################################################
# Mixins
####################################################################

def utcnow_no_ms():
    """Returns utcnow without microseconds"""
    return datetime.datetime.utcnow().replace(microsecond=0)


class TimestampModelMixin(Model):
    """Track creation and modification times"""
    created = DateTimeField(default=utcnow_no_ms)
    modified = DateTimeField()

    def save(self, **kwargs):
        self.modified = datetime.datetime.now()
        return super(TimestampModelMixin, self).save(**kwargs)


####################################################################
# Pagination
####################################################################

class Pagination:
    pass




class PrimaryKeyPagination(Pagination):
    """
    Primary key pagination
    
    It does not support models with compound keys or no primary key
    as doing so would require using LIMIT/OFFSET which has terrible
    performance at scale. If you want this, send a PR. 

    XXX: Do we want to add encryption support? (yes but it should be outside here)
    """

    @classmethod
    def paginate_query(self, query, offset, count, sort_params=None):
        """
        Apply pagination to query

        :attr query: Instance of `peewee.Query`
        :attr offset: Pagination offset, str/int
        :attr count: Max rows to return
        :attr sort_params: List of tuples, e.g. [('id', 'asc')]

        :returns: Instance of `peewee.Query`
        """
        assert isinstance(query, peewee.Query)
        assert isinstance(offset, (str, int))
        assert isinstance(count, int)
        assert isinstance(sort_params, (list, set, tuple, type(None)))

         # ensure our model has a primary key
        fields = query.model._meta.get_primary_keys()
        if len(fields) == 0:
            raise peewee.ProgrammingError(
                'Cannot apply pagination on model without primary key')

        # ensure our model doesn't use a compound primary key
        if len(fields) > 1:
            raise peewee.ProgrammingError(
                'Cannot apply pagination on model with compound primary key')

        # apply offset
        query = query.where(fields[0] >= offset)
        query = query.order_by(fields[0].asc())

        # do we need to apply sorting?
        if sort_params is None: return query

        order_bys = []
        for field, direction in sort_params:
            # does this field have a valid sort direction?
            if not isinstance(direction, str):
                raise ValueError("Invalid sort direction on field '{}'".format(field))

            direction = direction.lower().strip()
            if direction not in ['asc', 'desc']:
                raise ValueError("Invalid sort direction on field '{}'".format(field))

            # apply sorting
            order_by = peewee.SQL(field)
            order_by = getattr(order_by, direction)()
            order_bys += [order_by]

        query = query.order_by(*order_bys)
        return query


####################################################################
# Model List
# XXX: Restrict which fields can be filtered
# XXX: Add sort capabilities
####################################################################


class ModelCRUD:
    paginator = None
    query = None

    sort_fields = []
    filter_fields = []

    '''
    def get_sort_schema(self):
        """
        Returns marshmallow schema for validating sort parameters

        This is dynamically generated from `sort_fields` but can be
        overwritten with custom logic if desired
        """
        attrs = {}
        for field in self.sort_fields:
            # convert sort direction to lower and remove any whitespace
            key = 'lower_{}'.format(field)
            attrs[key] = post_load(lambda item: item.lower().strip())

            # validate sort direction
            attrs[field] = marshmallow.fields.String(
                validator=marshmallow.validate.OneOf('asc', 'desc'))

        return type('SortSchema', (marshmallow.Schema,), attrs)

        # do we have valid sort parameters?
        sort_schema = self.get_sort_schema()
        try:
            clean_params = sort_schema.dump(params)
        except marshmallow.ValidationError as exc:
            nexc = ValueError("Invalid sort parameters specified")
            nexc.errors = exc.messages
            raise nexc
    '''


    def get_query(self):
        """Return query for our model"""
        return self.query

    def get_paginator(self):
        """Return pagination for our model"""
        return self.paginator

    def apply_filters(self, query, filters):
        """
        Apply user specified filters to query
        """
        assert isinstance(query, peewee.Query)
        assert isinstance(filters, dict)

    def list(self, filters, cursor, count):
        """
        List items from query
        """
        assert isinstance(filters, dict), "expected filters type 'dict'"
        assert isinstance(cursor, dict), "expected cursor type 'dict'"

        # start with our base query
        query = self.get_query()
        assert isinstance(query, peewee.Query)

        # XXX: convert and apply user specified filters
        #filters = {field.name: cursor[field.name] for field in fields}
        #query.where(

        paginator = self.get_paginator()
        assert isinstance(paginator, Pagination)

        # always include an extra row for next cursor position
        count += 1

        # apply pagination to query
        pquery = paginator.filter_query(query, cursor, count)
        items = [ item for item in pquery ]

        # determine next cursor position
        next_item = items.pop(1)
        next_cursor = next_item.to_cursor_ref()

        '''
        # is this field allowed for sort?
        if field not in self.sort_fields:
            raise ValueError("Cannot sort on field '{}'".format(field))
        '''

        return items, next_cursor

    def retrieve(self, cursor):
        """
        Retrieve items from query
        """
        assert isinstance(cursor, dict), "expected cursor type 'dict'"

        # look for record in query
        query = self.get_query()
        assert isinstance(query, peewee.Query)

        query
        return query.get(**cursor)

