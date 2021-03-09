from setuptools import setup
import versioneer

setup(name='iTask',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
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
