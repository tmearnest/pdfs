import glob, os, subprocess, json, time, getpass, socket
from setuptools import setup
import setuptools.command.build_py as duc

pkgName = 'sbd'
ver = '0.0.3'
description='Simple bibliography manager'
long_description=open("README.md").read().strip()

setup(name=pkgName,
      version=ver,
      cmdclass={'build_py': duc.build_py},
      packages=['sbd', 'sbd.Commands'],
      description=description,
      long_description=long_description,
      author='Tyler M. Earnest',
      data_files=[('sbd/templates', glob.glob("sbd/templates/*"))],
      author_email='tylere@rne.st',
      url='http://tyler.ea.rne.st',
      license='MIT License',
      entry_points = {"console_scripts": ['sbd = sbd.__main__:main']},
      install_requires = ["prompt_toolkit", "inotify", "flask", "termcolor", "requests", "unidecode", "pdfminer.six", "pygments"],
      zip_safe=False)
