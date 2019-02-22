from setuptools import setup, find_packages

setup(
    name='zappa-call-later',
    version='1.0.0',
    packages=find_packages('src'),
    package_dir={'':'src'},
    url='https://github.com/andytwoods/zappa-call-later',
    license='MIT License',
    author='andytwoods',
    author_email='andytwoods@gmail.com',
    description='store future tasks in the db and call them after set delays'
)
