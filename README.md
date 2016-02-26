## Peewee Extras

[![Travis CI](https://travis-ci.org/imsofly/peewee-extras.svg)](https://travis-ci.org/imsofly/peewee-extras)
[![Coverage Status](https://coveralls.io/repos/imsofly/peewee-extras/badge.svg?branch=master&service=github)](https://coveralls.io/github/imsofly/peewee-extras?branch=master)
[![Python Versions](https://img.shields.io/pypi/pyversions/peewee-extras.svg)](https://pypi.python.org/pypi/peewee-extras)
[![PyPI](https://img.shields.io/pypi/v/peewee-extras.svg)](https://pypi.python.org/pypi/peewee-extras)

> **WARNING: This library is still in development, not production ready**

## Testing

```
tox
python setup.py test
TEST_BACKEND=postgres python setup.py test
TEST_BACKEND=sqlite python setup.py test
TEST_BACKEND=mysql python setup.py test
```

Provides some extra features for Peewee, including;

* Database manager for grouping connections
* Model manager for grouping models
* Read/write database routing
* Model helpers, such as `get_or_none()` and `r`efetch()
* HexField for storing hex data as binary
* OrderedUUIDField for index optimized UUID binary storag
* JSONField for storing JSON with any custom encoder/decoder
* IPv4AddressField for storing IPv4 addresses
* HashValue for storing cryptographic hashes, with optional encryption key

## Todo

```
XXX: Add testing for all databases
XXX: Better test coverage
XXX: Move to pytest
XXX: Add `UNIQUE constraint failed` check onto `create_or_get()`
     https://github.com/coleifer/peewee/issues/443
XXX: Add connection pool support?
XXX: Add migrations?
XXX: Fix binary field support
```
