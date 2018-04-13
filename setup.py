from setuptools import setup, find_packages

base_requirements = [
    'peewee>=3.2',
    'six',
]

setup(
    name="peewee-extras",
    description="Extras for Peewee",
    author='Cal Leeming',
    author_email='cal@iops.io',
    url='https://github.com/foxx/peewee-extras',
    keywords=['peewee'],
    version="0.5.0",
    py_modules=['peewee_extras'],
    install_requires=base_requirements,
    tests_require=base_requirements + [
        'pytest-benchmark>=3.0',
        'pytest-raisesregexp>=2.1',
        'pytest-cov>=2.2',
        'pytest>=2.8',
        'python-coveralls',
        'tox',
        'psycopg2',
        'mysqlclient',
    ]
)
