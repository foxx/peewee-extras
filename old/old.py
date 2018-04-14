

class OrderedUUIDField(BlobField):
    """
    Optimized storage for UUID fields in MySQL, based on research by Percona
    https://www.percona.com/blog/2014/12/19/store-uuid-optimized-way/

    XXX: needs benchmark in postgres (didn't we already do this?!)
    XXX: Should storage use BINARY instead of BLOB? Needs benchmark
    XXX: Add support for OrderedUUIDField in all databases
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

class HexField(BlobField):
    """Store hex data as binary"""

    def db_value(self, value):
        return binascii.unhexlify(value)

    def python_value(self, value):
        return binascii.hexlify(value).decode(encoding='UTF-8')


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



"""

if six.PY3: # pragma: nocover
    from urllib.parse import urlparse, parse_qsl, urlencode
else: # pragma: nocover
    from urlparse import urlparse, parse_qsl
    from urllib import urlencode

"""


        '''

        # cursor offset should match primary key
        pk_field_names = [ field.name for field in fields ]
        if pk_field_names != list(params.keys()):
            raise ValueError("Cursor fields do not match primary key fields")
 
        x = functools.reduce(operator.and_, x, True)
        query = query.where(x)
       
        # apply filters to query
        import operator
        import functools

        x = []
        for fname, fvalue in params.items():
            f = query.model._meta.fields[fname]
            #query = query.where(f >= fvalue)
            x += [f >= fvalue]
 
        # model has a compound primary key
        if len(fields) > 1:
            # ensure our cursor keys match the compound index keys
            assert isinstance(cursor, dict), "Expected cursor type 'dict'"
            expect_field_names = [ field.name for field in fields ]
            if cursor.keys() != expect_field_names:
                raise ValueError("Cursor field names do not match compound primary key")

            # apply cursor to filter
            filters = {field.name: cursor[field.name] for field in fields}
            return query.where(**filters).limit(count)
        '''


