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

    def get_primary_key_ref(self):
        """
        Returns dict of values needed to refetch row
        :rtype: dict
        :returns: Dict of primary key values
        """
        fields = self._meta.get_primary_keys()
        assert fields
        values = {field.name:self.__data__[field.name] for field in fields}
        return values

    def refetch(self):
        """
        Return new model instance with fresh data from database
        Only works on models which have a primary or compound key
        See https://github.com/coleifer/peewee/issues/638

        XXX: Add support for models without PK
        """
        filters = self.get_primary_key_ref()
        return self.__class__.get(**filters)


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

