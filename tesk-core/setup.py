import codecs
from os import path
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with codecs.open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESC = f.read()

INSTALL_DEPS = ['kubernetes==5.0.0',
                'requests==2.18.4',
                'future==0.16.0']
TEST_DEPS = ['pytest',
             'unittest2']
DEV_DEPS = []

setup(
    name='teskcore',

    # https://pypi.python.org/pypi/setuptools_scm
    use_scm_version={'root': '..', 'relative_to': __file__},

    description='AAP Client',
    long_description=LONG_DESC,

    url='https://github.com/EMBL-EBI-TSI/TESK',

    author='Erik van der Bergh',
    author_email='evdbergh@ebi.ac.uk',

    license='Apache License 2.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        'Intended Audience :: System Administrators',

        'License :: OSI Approved :: Apache Software License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],

    # What does your project relate to?
    keywords='tes kubernetes ebi',

    packages=find_packages(exclude=['examples', 'docs', 'tests', 'containers']),

    scripts=[
        'tesk_core/taskmaster.py',
        'tesk_core/filer.py'
    ],
    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=INSTALL_DEPS,

    setup_requires=['setuptools_scm'],

    python_requires='>=2.7, <3.0',

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': DEV_DEPS,
        'test': TEST_DEPS
    },
)
