from setuptools import setup, find_packages

setup(
    name='hello64',
    version='0.0.1',
    url='https://github.com/mypackage.git',
    author='Peter Romianowski',
    author_email='pero@cling.com',
    description='A "Hello world" needs a computer first',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[],
)
