from setuptools import find_packages, setup  
from setuptools.command.install import install as _install  
from setuptools.command.develop import develop as _develop
from setuptools.command.test import test as TestCommand

def _post_install():
  import shutil
  import site
  site_packages = site.getsitepackages()
  # We only copy python encoding file into the first site package directory
  shutil.copy('pythonql.pth', site_packages[0])

class install(_install):  
  def run(self):

    # the second parameter, [], can be replaced with a set of 
    # parameters if _post_install needs any
    self.execute(_post_install, [],  
                 msg="Running post install task")

    super().run()

class my_develop(_develop):  
  def run(self):
    _develop.run(self)
    self.execute(_post_install, [],
                     msg="Running post develop task")

# Inspired by the example at https://pytest.org/latest/goodpractises.html
class NoseTestCommand(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # Run the nose ensuring that argv simulates running nosetests directly
        import nose
        nose.run_exit(argv=['nosetests'])

setup(name='pythonql3',  
        version='0.9.76',
        description='PythonQL Query Language Extension',
        long_description="""
PythonQL Query Language Extension


PythonQL allows you to use powerful queries against files, databases, XML and JSON data, Pandas DataFrames and any collections.


Just run pip install pythonql (pythonql3 for Python3) and you can start using a powerful query language right inside you Python code!
PythonQL won't break your existing code, you just need to mark PythonQL files with #coding: pythonql and you're set to go.
""",
        url='http://www.pythonql.org',
        author='Pavel Velikhov',
        author_email='pavel.velikhov@gmail.com',
        license='MIT',
        keywords='query extension',
        setup_requires=['ply>=3.9'],
        install_requires=['ply>=3.9'],
        tests_require=['nose'],
        packages=find_packages('.'),
        package_dir = {'': '.'},
        classifiers = [ 
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License'
        ],
        cmdclass={'install': install,  # override install
                  'develop': my_develop,  # develop is used for pip install -e .
                  'test': NoseTestCommand }  
        )
