from setuptools import find_packages, setup

setup(
    name='tfuc',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'bs4', 'fake_useragent', 'openpyxl', 'sqlalchemy', 'selenium', 'requests', 'urllib3'
    ],
)
