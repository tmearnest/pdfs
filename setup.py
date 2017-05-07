from setuptools import setup

setup(name='sbd',
      version="0.0.2",
      packages=['sbd'],
      description='Simple bibliography manager',
      long_description=open('README.md').read().strip(),
      author='Tyler M. Earnest',
      author_email='tylere@rne.st',
      url='http://tyler.ea.rne.st',
      license='MIT License',
      entry_points = {"console_scripts": ['sbd = sbd.__main__:main']},
      install_requires = ["termcolor", "whoosh", "pdfminer.six", "unidecode", "pybtex", "requests"],
      zip_safe=False)
