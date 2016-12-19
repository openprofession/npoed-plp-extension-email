from setuptools import setup, find_packages

setup(
    name='npoed-plp-extension-email',
    version='0.1.1',
    packages=find_packages(),
    description='PLP extension email',
    url='http://example.com',
    author='author',
    dependency_links=['https://github.com/npoed/npoed-massmail/tarball/master#egg=npoed_massmail-0.1'],
    install_requires=["npoed_massmail==0.1"],
)

