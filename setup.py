from setuptools import setup
from parselcli.app import APP_NAME

setup(
    name='parsel-cli',
    version='0.26',
    packages=['parselcli'],
    url='https://github.com/granitosaurus/parsel-cli',
    license='GPLv3',
    author='granitosaurus',
    author_email='bernardas.alisauskas@gmail.com',
    description='CLI interpreter for xpath and css selectors',
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
)
