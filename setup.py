from setuptools import setup

setup(name='sbd',
      version="0.0.1",
      packages=['sbd'],
      description='Simple bibliography manager',
      long_description=open('README.md').read().strip(),
      author='Tyler M. Earnest',
      author_email='tylere@rne.st',
      url='http://tyler.ea.rne.st',
      install_requires=['bibtexparser', 'unidecode', 'whoosh'],
      license='MIT License',
      entry_points = {"console_scripts": ['sbd = sbd.Entry:sbd']},
      zip_safe=False)
