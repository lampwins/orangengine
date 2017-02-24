try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requirements = ['pandevice', 'lxml', 'netaddr', 'junos-eznc', 'terminaltables']

config = {
    'description': 'Firewall Policy Automation Engine',
    'author': 'John Anderson',
    'url': 'https://github.com/lampwins/orangengine',
    'download_url': 'https://github.com/lampwins/orangengine',
    'author_email': 'lampwins@gmail.com.',
    'version': '0.0.1',
    'packages': ['orangengine'],
    'scripts': [],
    'name': 'orangengine',
    'install_requires': requirements
}

setup(**config)
