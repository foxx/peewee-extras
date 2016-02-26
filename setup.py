from setuptools import setup, find_packages

base_requirements = [
    'peewee>=2.8',
    'six',
    'passlib>=1.6',
    'helpful>=0.8'
]

setup(
    name="peewee-extras",
    description="Extras for Peewee",
    author='Cal Leeming',
    author_email='cal@iops.io',
    url='https://github.com/imsofly/peewee-extras',
    keywords=['peewee'],
    version="0.4.0",
    py_modules=['peewee_extras'],
    setup_requires=[
        'pytest-runner>=2.6',
        'yanc>=0.3'
    ],
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
