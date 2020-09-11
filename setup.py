import codecs
from os import path
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with codecs.open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESC = f.read()

INSTALL_DEPS = ['kubernetes==9.0.0',
                'requests>=2.20.0',
                'urllib3==1.24.2']
TEST_DEPS = [ 'pytest',
              'pyfakefs',
              'pytest-mock',
              'fs',
              'pytest-localftpserver'
            ]

DEV_DEPS = []

setup(
    name='teskcore',

    # https://pypi.python.org/pypi/setuptools_scm
    use_scm_version=True,

    description='TES on Kubernetes',
    long_description=LONG_DESC,
    long_description_content_type="text/markdown",

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

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7'
    ],

    # What does your project relate to?
    keywords='tes kubernetes ebi',

    packages = find_packages('src'),
    package_dir = {'': 'src'},

    entry_points={
        'console_scripts' : [
            'filer = tesk_core.filer:main',
            'taskmaster = tesk_core.taskmaster:main'
        ]
    },
    test_suite='tests',

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=INSTALL_DEPS,

    setup_requires=['setuptools_scm'],

    tests_require=TEST_DEPS,

    python_requires='>=3.5, <4.0',

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': DEV_DEPS,
        'test': TEST_DEPS
    },
)
