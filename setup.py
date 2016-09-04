try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Firewall Policy Automation Engine',
    'author': 'John Anderson',
    'url': 'https://github.com/lampwins/oragengine',
    'download_url': 'https://github.com/lampwins/oragengine',
    'author_email': 'lampwins@gmail.com.',
    'version': '0.0.1',
    'install_requires': [''],
    'packages': ['oragengine'],
    'scripts': [],
    'name': 'oragengine'
}

setup(**config)
