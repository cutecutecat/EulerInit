from setuptools import setup, find_packages
import os

install_requires = []
long_description = ''
with open(os.path.join(__file__, '../requirements.txt')) as f:
    install_requires = f.readlines()
with open(os.path.join(__file__, '../readme.md'), errors='ignore') as f:
    long_description = f.read()

setup(
    name='EulerInit',
    version='0.1',
    author='cutecutecat',
    description="A mirror generating tool designed for OpenEuler from ISO file to VM file.",
    long_description=long_description,
    packages=find_packages(),
    package_data={'EulerInit.Convertor': ['template/ALI/*', 'template/HUAWEI/*', 'template/TENCENT/*']},
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'EulerInit = EulerInit.entry:cli',
        ],
    },
)
