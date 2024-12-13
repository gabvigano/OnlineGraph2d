from setuptools import setup, find_packages

setup(
    name="OnlineGraph2d",
    version="0.1.0",
    packages=find_packages(include=['OnlineGraph2d']),
    install_requires=['pygame>=2.0.0'],
    author='Gabriele Viganò',
    description='A small Python library to create 2D online games'
)
