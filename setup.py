from setuptools import setup

setup(
    name='parsel-cli',
    version='0.1',
    packages=['parselcli'],
    url='',
    license='',
    author='granitosaurus',
    author_email='',
    description='',
    install_requires=[
        'click',
        'parsel',
    ],
    entry_points="""
        [console_scripts]
        parsel=parselcli.cli:cli
    """,
)
