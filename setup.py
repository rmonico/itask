from setuptools import setup
from itask import get_version

version = get_version()

setup(name='iTask',
      version=version,
      description='A CLI frontend to easier the use of Taskwarrior',
      url='https://github.com/rmonico/itask',
      author='Rafael Monico',
      author_email='rmonico1@gmail.com',
      license='GPL3',
      packages=['itask'],
      include_package_data=True,
      entry_points={
          'console_scripts': ['itask=itask.__main__:main'],
      },
      zip_safe=False,
      install_requires=['PyYaml==6.0.3', 'rmonico.tabular==0.0.1'])
