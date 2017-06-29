from setuptools import setup

setup(
    name='parsel-cli',
    version='0.22',
    packages=['parselcli'],
    url='https://github.com/granitosaurus/parsel-cli',
    license='GPLv3',
    author='granitosaurus',
    author_email='bernardas.alisauskas@gmail.com',
    description='CLI interpreter for xpath and css selectors',
    install_requires=[
        'click',
        'parsel',
    ],
    entry_points="""
        [console_scripts]
        parsel=parselcli.cli:cli
    """,
)
