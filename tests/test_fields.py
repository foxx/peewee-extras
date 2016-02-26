from uuid import uuid1
from peewee_extras import Model, OrderedUUIDField, IPv4Field

from .models import OrderedUUIDModel, IPv4Model


class TestOrderedUUIDField(object):
    required_models = [OrderedUUIDModel]

    def test_with_model(self, database):
        for x in range(10):
            id = uuid1().hex
            o = OrderedUUIDModel.create(value=id)
            o = o.refetch()
            assert o.value.hex == id

    def test_field(self):
        id = uuid1()
        a = OrderedUUIDField()
        as_binary = a.db_value(id)
        as_result = a.python_value(as_binary)
        assert id == as_result
        assert str(id) == str(as_result)



class TestIPv4Field(object):
    required_models = [IPv4Model]

    def test_with_model(self, database):
        pass

    def test_field(self):
        f = IPv4Field()
        ip = '127.0.0.1'
        db_value = f.db_value(ip)
        assert db_value == b'\x7f\x00\x00\x01'
        python_value = f.python_value(db_value)
        assert python_value == ip
