from setuptools import setup, find_packages

setup(name='sbd',
      version='0.0.3',
      packages=find_packages(),
      description='Simple bibliography manager',
      long_description=open("README.md").read().strip(),
      author='Tyler M. Earnest',
      author_email='tylere@rne.st',
      url='https://github.com/tmearnest/sbd',
      license='MIT License',
      entry_points = {"console_scripts": ['sbd = sbd.__main__:main']},
      install_requires = ["flask", "inotify", "pdfminer.six",
                          "prompt_toolkit", "pygments", "requests",
                          "termcolor", "unidecode"])
