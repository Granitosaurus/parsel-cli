from setuptools import setup

with open('readme.md') as f:
    long_description = f.read()

setup(
    name='parselcli',
    version='0.32.1',
    packages=['parselcli'],
    url='https://github.com/granitosaurus/parsel-cli',
    license='GPLv3',
    author='granitosaurus',
    author_email='bernardas.alisauskas@gmail.com',
    description='CLI interpreter for xpath and css selectors',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'toml',
        'click',
        'parsel',
        'prompt-toolkit',
        'requests-cache',
        'brotli'
    ],
    entry_points=f"""
        [console_scripts]
        parsel=parselcli.cli:cli
    """,
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Internet',
    ]
)
