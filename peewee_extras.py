import logging
import peewee
import os
import datetime
import binascii
import json
import socket
import passlib.hash
import inspect
import six

from uuid import uuid4, UUID
from warnings import warn
from collections import OrderedDict
from peewee import (DateTimeField, BlobField, Field, TextField)
from helpful import ClassDict, ensure_instance, add_bases, coerce_to_bytes

if six.PY3: # pragma: nocover
    from urllib.parse import urlparse, parse_qsl, urlencode
else: # pragma: nocover
    from urlparse import urlparse, parse_qsl
    from urllib import urlencode

logger = logging.getLogger(__name__)

####################################################################
# Monkey patching
####################################################################

class CallableDatabaseMixin(peewee.ModelOptions):
    @property
    def database(self):
        if callable(self._database):
            return self._database(self)
        return self._database

    @database.setter
    def database(self, value):
        self._database = value


def monkeypatch():
    """
    Peewee does not support plugins, therefore we must monkeypatch
    See https://github.com/coleifer/peewee/issues/804
    See https://github.com/coleifer/peewee/issues/825
    """
    if peewee.ModelOptions != CallableDatabaseMixin:
        peewee.ModelOptions = CallableDatabaseMixin


####################################################################
# DB manager
####################################################################

# XXX: improve KeyError message
class DatabaseManager(dict):
    """Database manager"""

    def connect_all(self):
        """Create connection for all databases"""
        for name, connection in self.items():
            connection.connect()

    def disconnect_all(self):
        """Disconnect from all databases"""
        # closing in-memory databases should cause it to be deleted
        for name, connection in self.items():
            if not connection.is_closed():
                connection.close()


####################################################################
# Model manager
####################################################################

class ModelManager(list):
    """Handles model registration"""

    def create_tables(self, drop_existing=False):
        """
        Create database tables

        :attr drop_existing (bool): If table exists, drop and re-create
        """
        for cls in self:
            if drop_existing:
                cls.drop_table(fail_silently=True)
            cls.create_table(fail_silently=True)

    def destroy_tables(self):
        """Destroy database tables"""
        for cls in self:
            cls.drop_table(fail_silently=True)

    def register(self, model_cls):
        """Register model(s) with app"""
        ensure_instance(model_cls, peewee.Model)
        if model_cls in self:
            raise ValueError("Model already registered")
        self.append(model_cls)
        return model_cls


####################################################################
# Database routing
####################################################################

class DatabaseRoutingMixin(object):
    """
    Although the cleanest approach is to hook into Query._execute,
    this can only be achieved via monkey patching which is not very
    clean. Instead we will override select() and raw(), as all other
    queries are destined for write DB anyway
    """

    @classmethod
    def select(cls, *args, **kwargs):
        query = super(DatabaseRoutingMixin, self).select(*args, **kwargs)
        query.database = cls.get_read_database()
        return query

    @classmethod
    def get_read_database(self):
        return self._meta.database

    @classmethod
    def raw(cls, *args, **kwargs):
        query = super(DatabaseRoutingMixin, self).raw(*args, **kwargs)
        if query._sql.lower().startswith('select'):
            query.database = cls.get_read_database()
        return query


####################################################################
# Model
####################################################################


class Model(peewee.Model, DatabaseRoutingMixin):
    """Custom model for common functionality"""

    def update_instance(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.save()

    @classmethod
    def get_or_none(cls, **kwargs):
        """
        Return object or None
        XXX: needs UT
        """
        try:
            return cls.get(**kwargs)
        except cls.DoesNotExist:
            return None

    def atomic(self):
        """Shortcut method for creating atomic context"""
        return self._meta.database.atomic()

    def get_primary_key_ref(self):
        """
        Returns dict of values needed to refetch row
        :rtype: dict
        :returns: Dict of primary key values
        """
        fields = self._meta.get_primary_key_fields()
        values = {field.name:self._data[field.name] for field in fields}
        return values

    def refetch(self):
        """
        Return new model instance with fresh data from database
        Only works on models which have a primary or compound key
        See https://github.com/coleifer/peewee/issues/638
        XXX: Needs UT
        XXX: Some sort of weird caching bug here?
        XXX: Add support for models without PK
        """
        fields = {field.name: field 
            for field in self._meta.get_primary_key_fields()}
        filters = [ fields[field] == value for field, value 
            in self.get_primary_key_ref().items()]
        results = list(self.__class__.select().where(*filters).execute())
        if len(results) == 0:
            raise peewee.IntegrityError("Row does not exist")
        elif len(results) > 1:
            raise peewee.IntegrityError("Too many rows")
        return results[0]


####################################################################
# Mixins
####################################################################

class TimestampModelMixin(object):
    """Track creation and modification times"""
    created = DateTimeField(default=datetime.datetime.now)
    modified = DateTimeField()

    def save(self, **kwargs):
        self.modified = datetime.datetime.now()
        return super(TimestampModelMixin, self).save(**kwargs)

####################################################################
# Fields
####################################################################


class UUIDField(Field):        
    """       
    Backported from latest peewee, waiting for release
    XXX: Can be removed once fixed
    """
    db_field = 'uuid'     
      
    def db_value(self, value):        
        if isinstance(value, UUID):       
            return value.hex      
        try:      
            return UUID(value).hex        
        except:       
            return value      
      
    def python_value(self, value):        
        if isinstance(value, UUID):       
            return value      
        return None if value is None else UUID(value)     
      

class HexField(BlobField):
    """Store hex data as binary"""

    def db_value(self, value):
        return binascii.unhexlify(value)

    def python_value(self, value):
        return binascii.hexlify(value).decode(encoding='UTF-8')

# XXX: Need to benchmark Postgres
# XXX: Add support for OrderedUUIDField in all databases


class OrderedUUIDField(BlobField):
    """
    Optimized storage for UUID fields in MySQL, based on research by Percona
    https://www.percona.com/blog/2014/12/19/store-uuid-optimized-way/

    XXX: Should storage use BINARY instead of BLOB? Needs benchmark
    """

    def db_value(self, value):
        """
        Convert UUID to binary blob
        """

        # ensure we have a valid UUID
        if not isinstance(value, UUID):
            value = UUID(value)

        # reconstruct for optimal indexing
        parts = str(value).split("-")
        reordered = ''.join([parts[2], parts[1], parts[0], parts[3], parts[4]])
        value = binascii.unhexlify(reordered)
        return super(OrderedUUIDField, self).db_value(value)

    def python_value(self, value):
        """
        Convert binary blob to UUID instance
        """
        value = super(OrderedUUIDField, self).python_value(value)
        u = binascii.b2a_hex(value)
        value = u[8:16] + u[4:8] + u[0:4] + u[16:22] + u[22:32]
        return UUID(value.decode())


class JSONField(BlobField):
    """Store JSON in blob field"""
    def __init__(self, *args, **kwargs):
        self._encoder = kwargs.pop('encoder', json.JSONEncoder)
        self._decoder = kwargs.pop('decoder', json.JSONDecoder)
        super(JSONField, self).__init__(*args, **kwargs)

    def db_value(self, value):
        if value:
            return self._encoder().encode(value)

    def python_value(self, value):
        if value:
            return self._decoder().decode(value)


class IPv4Field(BlobField):
    """
    XXX: Add proper support, possibly duplicate from Django;
    /django/db/models/fields/__init__.py#L1934

    For now, this just converts an IPv4 string into binary and back
    """

    def db_value(self, value):
        return socket.inet_pton(socket.AF_INET, value)

    def python_value(self, value):
        return socket.inet_ntop(socket.AF_INET, value)


####################################################################
# Field hashing and encryption
####################################################################

class HashValue(bytes):
    def check(self, value):
        value = self.field.transform_value(value)
        return self.field.hhash.verify(value, self)


class HashField(TextField):
    """
    Hash field, also supports encryption key

    PBKDF2-SHA512 is used instead of bcrypt, see full discussion here;
    http://security.stackexchange.com/a/6415/84745
    """

    def __init__(self, key=None, rounds=100000, salt_size=32, 
        hash=passlib.hash.pbkdf2_sha512, **kwargs):
        self._key = key
        self.rounds = rounds
        self.hhash = hash
        self.salt_size = salt_size
        super(HashField, self).__init__(**kwargs)

    @property
    def key(self):
        return self._key() if callable(self._key) else self._key

    @key.setter
    def key(self, value):
        self._key = value

    def db_value(self, value):
        """Convert the python value for storage in the database."""
        value = self.transform_value(value)
        return self.hhash.encrypt(value, 
            salt_size=self.salt_size, rounds=self.rounds)

    def python_value(self, value):
        """Convert the database value to a pythonic value."""
        value = coerce_to_bytes(value)
        obj = HashValue(value)
        obj.field = self
        return obj

    def transform_value(self, value):
        value = coerce_to_bytes(value)
        key = coerce_to_bytes(self.key) if self.key else None
        return value+key if key else value

