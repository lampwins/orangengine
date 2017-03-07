try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requirements = ['pandevice', 'lxml', 'netaddr', 'junos-eznc', 'terminaltables']
packages = ['orangengine',
            'orangengine/drivers',
            'orangengine/errors',
            'orangengine/models',
            'orangengine/models/generic',
            'orangengine/models/paloalto',
            'orangengine/mappers']

config = {
    'description': 'Firewall Policy Automation Engine',
    'author': 'John Anderson',
    'url': 'https://github.com/lampwins/orangengine',
    'download_url': 'https://github.com/lampwins/orangengine',
    'author_email': 'lampwins@gmail.com.',
    'version': '0.0.1',
    'scripts': [],
    'name': 'orangengine',
    'install_requires': requirements,
    'packages': packages
}

setup(**config)
