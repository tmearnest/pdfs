import glob, os, subprocess, json, time, getpass, socket
from setuptools import setup
import setuptools.command.build_py as duc

pkgName = 'sbd'
ver = '0.0.2'
description='Simple bibliography manager'
long_description=open("README.md").read().strip()


class build_py(duc.build_py):
      def run(self):
            if not self.dry_run:
                  target_dir = os.path.join(self.build_lib, pkgName)
                  self.mkpath(target_dir)

                  try:
                        gitCmd = subprocess.check_output(["git", "log", "--pretty=format:%H", "-n", "1"]).decode()
                  except:
                        gitCmd = '<<not build under version control>>'

                  buildData = dict(buildTime=time.strftime("%Y-%m-%d %H:%M:%S"),
                                   name=pkgName,
                                   version=ver,
                                   gitHash=gitCmd,
                                   user=getpass.getuser(),
                                   host=socket.gethostname())

                  json.dump(buildData, open(os.path.join(target_dir, "build.json"), "w"))

            duc.build_py.run(self)

setup(name=pkgName,
      version=ver,
      cmdclass={'build_py': build_py},
      packages=['sbd'],
      description=description,
      long_description=long_description,
      data_files=[('sbd/templates', glob.glob("sbd/templates/*"))],
      author='Tyler M. Earnest',
      author_email='tylere@rne.st',
      url='http://tyler.ea.rne.st',
      license='MIT License',
      entry_points = {"console_scripts": ['sbd = sbd.__main__:main']},
      install_requires = ["inotify", "flask", "termcolor", "whoosh", "pdfminer.six", "unidecode", "pybtex", "requests"],
      zip_safe=False)
