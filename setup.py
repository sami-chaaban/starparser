from distutils.core import setup
from setuptools import find_packages
import starparser

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='starparser',
      version=starparser.__version__,
      description='Manipulate and mine Relion star files.',
      author='Sami Chaaban',
      author_email='chaaban@mrc-lmb.cam.ac.uk',
      url='http://pypi.python.org/pypi/starparser/',
      long_description=long_description,
      long_description_content_type='text/markdown',
      packages=find_packages(),
      entry_points={
          "console_scripts": [
            "starparser = starparser.__main__:main",
            ],
      },
      install_requires=["numpy==1.19.5","pandas==1.1.5","matplotlib==3.3.4", "scipy==1.5.4"],
      python_requires='>=3.6'
     )
