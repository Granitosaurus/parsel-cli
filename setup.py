from setuptools import setup
from parselcli.app import APP_NAME

with open('readme.md') as f:
    long_description = f.read()

setup(
    name='parselcli',
    version='0.26.1',
    packages=['parselcli'],
    url='https://github.com/granitosaurus/parsel-cli',
    license='GPLv3',
    author='granitosaurus',
    author_email='bernardas.alisauskas@gmail.com',
    description='CLI interpreter for xpath and css selectors',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'click',
        'parsel',
        'prompt-toolkit',
        'requests-cache',
    ],
    entry_points=f"""
        [console_scripts]
        {APP_NAME}=parselcli.cli:cli
    """,
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Topic :: Internet',
    ]
)
