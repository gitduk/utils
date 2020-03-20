from setuptools import find_packages, setup

with open ( "README.md" , "r" ) as fh :
    long_description = fh . read ()

setup(
    name='tfuc',
    version='1.0.8',
    author = "dongkai",
    author_email = "wdkany@qq.com",
    description = "some useful tools",
    long_description = long_description ,
    long_description_content_type = "text/markdown",
    url = "https://github.com/gitduk/tfuc.git",
    keywords=['selenium', 'bs4', 'web_craw'],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'bs4', 'fake_useragent', 'openpyxl', 'sqlalchemy', 'selenium', 'requests', 'urllib3'
    ],
)
