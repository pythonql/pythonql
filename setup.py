from setuptools import find_packages, setup  
from setuptools.command.install import install as _install  
from setuptools.command.develop import develop as _develop

def _post_install():
  import shutil
  from distutils.sysconfig import get_python_lib

  python_lib = get_python_lib()
  shutil.copy('pythonql.pth', python_lib)

class my_install(_install):  
  def run(self):
    _install.run(self)

    # the second parameter, [], can be replaced with a set of 
    # parameters if _post_install needs any
    self.execute(_post_install, [],  
                 msg="Running post install task")

class my_develop(_develop):  
  def run(self):
    _develop.run(self)
    self.execute(_post_install, [],
                     msg="Running post develop task")

setup(name='pythonql3',  
        version='0.9.0',
        description='PythonQL extension',
        url='http://www.pythonql.org',
        author='Pavel Velikhov',
        author_email='pavel(dot)velikhov(at)gmail(dot)com',
        license='MIT',
        keywords='query extension',
        install_requires=['antlr4-python3-runtime>=4.5.3'],
        packages=find_packages('.'),
        package_dir = {'': '.'},
        classifiers = [ 
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License'
        ],
        cmdclass={'install': my_install,  # override install
                  'develop': my_develop}  # develop is used for pip install -e .
        )
