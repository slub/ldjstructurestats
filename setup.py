"""
A commandline command (Python3 program) that determines the structure of given line-delimited JSON records.
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='ldjstructurestats',
      version='0.0.1',
      description='a commandline command (Python3 program) that determines the structure of given line-delimited JSON records',
      url='https://github.com/slub/ldjstructurestats',
      author='Bo Ferri',
      author_email='zazi@smiy.org',
      license="Apache 2.0",
      packages=[
          'ldjstructurestats',
      ],
      package_dir={'ldjstructurestats': 'ldjstructurestats'},
      install_requires=[
          'argparse>=1.4.0'
      ],
      entry_points={
          "console_scripts": ["ldjstructurestats=ldjstructurestats.ldjstructurestats:run"]
      }
      )
