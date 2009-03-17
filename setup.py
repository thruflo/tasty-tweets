import sys
from setuptools import setup, find_packages

sock = open('src/tastytweets/README.rst')
long_description = sock.read()
sock.close()

install_requires = [
    'DirectoryQueue',
    'python-crontab', # this is unix only
    'nose'
]

try:
    import json # py 2.6
except ImportError:
    install_requires.append('simplejson')


setup(
    name = 'tastytweets',
    version = '0.2.1',
    description = "delicious twitter mashup; finds twitter users posting links to urls you've tagged so you can start following them",
    long_description = long_description,
    author = 'thruflo',
    author_email = 'thruflo@googlemail.com',
    url = 'http://github.com/thruflo/tastytweets',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Programming Language :: Python'
    ],
    license = 'Public Domain',
    packages = find_packages('src'),
    package_dir = {
        '': 'src'
    },
    include_package_data = True,
    zip_safe = False,
    dependency_links = [
        'http://pypi.python.org/packages/source/p/python-crontab/python-crontab-0.7.tar.gz',
        'http://pypi.python.org/simple'
    ],
    install_requires = install_requires,
    test_suite = 'nose.collector',
    entry_points = {
        'console_scripts': [
            'tastytweets-find = tastytweets.client:find',
            'tastytweets-follow = tastytweets.client:follow',
            'tastytweets-push = tastytweets.client:push',
            'tastytweets-automate = tastytweets.client:automate',
            'tastytweets-reset-everything = tastytweets.client:reset',
            'tastytweets-reset-status-id = tastytweets.client:reset_status_id'
        ]
    }
)