#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Setup dot py."""
from __future__ import absolute_import, print_function

# import re
from glob import glob
from os.path import basename, dirname, join, splitext

from setuptools import find_packages, setup


def read(*names, **kwargs):
    """Read description files."""
    path = join(dirname(__file__), *names)
    with open(path, encoding=kwargs.get('encoding', 'utf8')) as fh:
        return fh.read()


# previous approach used to ignored badges in PyPI long description
# long_description = '{}\n{}'.format(
#     re.compile(
#         '^.. start-badges.*^.. end-badges',
#         re.M | re.S,
#         ).sub(
#             '',
#             read('README.rst'),
#             ),
#     re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read(join('docs', 'CHANGELOG.rst')))
#     )

long_description = '{}\n{}'.format(
    read('README.rst'),
    read(join('docs', 'CHANGELOG.rst')),
    )

setup(
    name='signposting',
    version='0.9.0',
    description='Parse and navigate FAIR Signposting Link headers',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license='Apache License, version 2.0',
    author='Stian Soiland-Reyes',
    author_email='stain@apache.org',
    url='https://github.com/stain/signposting',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(i))[0] for i in glob("src/*.py")],
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        # complete classifier list:
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Scientific/Engineering',
        ],
    project_urls={
        'webpage': 'https://github.com/stain/signposting',
        'Documentation': 'https://signposting.readthedocs.io/en/latest/',
        'Changelog': 'https://github.com/stain/signposting/blob/main/docs/CHANGELOG.rst',
        'Issue Tracker': 'https://github.com/stain/signposting/issues',
        'Discussion Forum': 'https://github.com/stain/signposting/discussions',
        },
    keywords=[
        'FAIR', 'signposting', 'linked data',
        'DOI', 'HTTP', 'linkset'
        ],
    python_requires='>=3.7',
    install_requires=[
        'beautifulsoup4>=4.10',
        'httplink==0.2.0',
        'rfc3987>=1.3.8',
        'requests>=2.28.1'
        ],
    extras_require={
            'tests': [
                'types-requests>=2.28.1',
                'types-beautifulsoup4>=4.10',
                'requests-mock>=1.9.3'
            ]
        # eg:
        #   'rst': ['docutils>=0.11'],
        #   ':python_version=="2.6"': ['argparse'],
        },
    setup_requires=[
        #   'pytest-runner',
        #   'setuptools_scm>=3.3.1',
        ],
    entry_points={
        'console_scripts': [
            'signposting= signposting.cli:main',
            ]        
        },
    # cmdclass={'build_ext': optional_build_ext},
    # ext_modules=[
    #    Extension(
    #        splitext(relpath(path, 'src').replace(os.sep, '.'))[0],
    #        sources=[path],
    #        include_dirs=[dirname(path)]
    #    )
    #    for root, _, _ in os.walk('src')
    #    for path in glob(join(root, '*.c'))
    # ],
    )
