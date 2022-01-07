from setuptools import setup,find_packages
setup(
    name='pytermrec',
    version='1.0.2',
    description='Record your terminal and play it',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/donno2048/termrec',
    packages=find_packages(),
    license='MIT',
    install_requires=['questionary>=1.10.0'],
    author='Elisha Hollander',
    classifiers=['Programming Language :: Python :: 3'],
    entry_points={ 'console_scripts': [ 'termrec=termrec.__main__:parse_rec', 'termplay=termrec.__main__:parse_play'] }
)
