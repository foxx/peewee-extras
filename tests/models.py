from peewee_extras import Model, OrderedUUIDField, IPv4Field
from peewee import CharField

class OrderedUUIDModel(Model):
    value = OrderedUUIDField()


class IPv4Model(Model):
    value = IPv4Field()

