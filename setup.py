from setuptools import setup

setup(name='iTask',
      version='0.3.10',
      description='A CLI frontend to easier the use of Taskwarrior',
      url='https://github.com/rmonico/itask',
      author='Rafael Monico',
      author_email='rmonico1@gmail.com',
      license='GPL3',
      packages=['itask'],
      entry_points={
          'console_scripts': ['itask=itask.itask:main'],
      },
      zip_safe=False)
