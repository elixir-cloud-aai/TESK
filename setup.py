import codecs
from os import path
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with codecs.open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESC = f.read()

INSTALL_DEPS = ['kubernetes==5.0.0',
                'requests>=2.20.0',
                'urllib3==1.22',
                'future==0.16.0',
                'enum34==1.1.6']
TEST_DEPS = [ 'pytest'
            , 'unittest2'
            , 'mock'
            , 'fs'
            ]

INSTALL_DEPS += TEST_DEPS    # Python 2 only

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

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],

    # What does your project relate to?
    keywords='tes kubernetes ebi',

    packages = find_packages('src'),
    package_dir = {'': 'src'},

    scripts=[
        'src/tesk_core/taskmaster.py',
        'src/tesk_core/filer.py',
        'src/tesk_core/filer_class.py',
        'src/tesk_core/pvc.py',
        'src/tesk_core/job.py'
    ],
    test_suite='tests',

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=INSTALL_DEPS,

    setup_requires=['setuptools_scm', 'pytest-runner'],

    tests_requires=TEST_DEPS,

    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*,  !=3.3.*, <4.0',

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': DEV_DEPS,
        'test': TEST_DEPS
    },
)
