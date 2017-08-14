import sys
from setuptools import setup, find_packages
from glob import glob

if sys.version_info < (3,6):
    sys.exit("Python 3.6 or newer required")

setup(
    name='bibs',
    version='0.1.0',
    python_requires=">=3.6",
    packages=find_packages(),
    description='Simple bibliography manager',
    keywords = ['doi', 'bibtex', 'pdf', 'bibliography'],
    classifiers = [ 
          'Intended Audience :: Developers',
          'Intended Audience :: Education',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Operating System :: POSIX :: Linux',
          'Development Status :: 3 - Alpha'],
    long_description=open("README.md").read().strip(),
    author='Tyler M. Earnest',
    author_email='tylere@rne.st',
    url='https://github.com/tmearnest/pdfs',
    package_data={'pdfs': ['templates/*', 'static/*', 'data/*']},
    license='MIT License',
    entry_points = {"console_scripts": ['pdfs = pdfs.Main:main']},
    zip_safe=False,
    install_requires = ["argcomplete", "colored", "flask", "inotify", "jinja2",
                        "pdfminer.six", "prompt_toolkit", "python-dateutil",
                        "requests",  "unidecode", "whoosh"])
