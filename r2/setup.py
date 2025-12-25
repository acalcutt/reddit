#!/usr/bin/env python
# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
#
# The Original Code is reddit.
#
# The Original Developer is the Initial Developer.  The Initial Developer of
# the Original Code is reddit Inc.
#
# All portions of the code written by reddit are Copyright (c) 2006-2015 reddit
# Inc. All Rights Reserved.
###############################################################################

import fnmatch
import os

from setuptools import Extension, find_packages, setup

commands = {}


try:
    from Cython.Build import cythonize
except ImportError:
    print("Cannot find Cython. Skipping Cython build.")
    pyx_extensions = []
else:
    pyx_files = []
    for root, directories, files in os.walk('.'):
        for f in fnmatch.filter(files, '*.pyx'):
            pyx_files.append(os.path.join(root, f))
    pyx_extensions = cythonize(pyx_files)


# guard against import errors in case this is the first run of setup.py and we
# don't have any dependencies (including baseplate) yet
try:
    from baseplate.integration.thrift.command import ThriftBuildPyCommand
except ImportError:
    print("Cannot find Baseplate. Skipping Thrift build.")
else:
    commands["build_py"] = ThriftBuildPyCommand


setup(
    name="r2",
    # Provide a valid version string to satisfy packaging/version
    version="0.0.0",
    install_requires=[
        "pyramid",
        "pyramid-mako",
        "Routes",
        "baseplate",
        "mako>=0.5",
        "boto >= 2.0",
        "pytz",
        # pycrypto is deprecated and doesn't build on modern systems
        # pycryptodome is a drop-in replacement with the same API
        "pycryptodome",
        "Babel>=1.0",
        "cython>=0.14",
        "SQLAlchemy",
        "beautifulsoup4",
        "chardet",
        "psycopg2",
        # Modern Cassandra driver (DataStax) replaces pycassa
        "cassandra-driver",
        # Modern captcha library (Python 3 compatible) replaces pycaptcha
        "captcha",
        # amqp is the modern Python 3 replacement for amqplib
        "amqp",
        # py-bcrypt works but bcrypt is the modern maintained version
        "bcrypt",
        # snudown requires compilation with gperf. On Ubuntu: apt install gperf build-essential python3-dev
        "snudown @ https://github.com/reddit/snudown/archive/v1.5.0.tar.gz",
        # l2cs (Lucene to CloudSearch) was an internal Reddit library, not publicly available.
        # Only needed for CloudSearch provider. Use Solr provider instead (search_provider = solr)
        # which doesn't require l2cs and is fully open source.
        # "l2cs>=2.0.2",
        "lxml",
        "kazoo",
        "stripe",
        "requests",
        "tinycss2",
        "unidecode",
        "PyYAML",
        "Pillow",
        # pylibmc requires libmemcached-dev on Ubuntu: apt install libmemcached-dev
        "pylibmc",
        "webob",
        "webtest",
        # python-snappy requires libsnappy-dev on Ubuntu: apt install libsnappy-dev
        "python-snappy",
        # httpagentparser - remove version pin for latest Python 3 compatible version
        "httpagentparser",
        # raven is deprecated, sentry-sdk is the replacement
        # Using raven for now as it still works, but consider migrating to sentry-sdk
        "raven",
    ],
    # setup tests (allowing for "python setup.py test")
    tests_require=['mock', 'nose', 'coverage'],
    test_suite="nose.collector",
    packages=find_packages(exclude=["ez_setup"]),
    cmdclass=commands,
    ext_modules=pyx_extensions + [
        Extension(
            "Cfilters",
            sources=[
                "r2/lib/c/filters.c",
            ]
        ),
    ],
    entry_points="""
    [paste.app_factory]
    main=r2:make_app
    [paste.paster_command]
    run = r2.commands:RunCommand
    shell = pylons.commands:ShellCommand
    [paste.filter_app_factory]
    gzip = r2.lib.gzipper:make_gzip_middleware
    [r2.provider.media]
    s3 = r2.lib.providers.media.s3:S3MediaProvider
    filesystem = r2.lib.providers.media.filesystem:FileSystemMediaProvider
    [r2.provider.cdn]
    fastly = r2.lib.providers.cdn.fastly:FastlyCdnProvider
    cloudflare = r2.lib.providers.cdn.cloudflare:CloudFlareCdnProvider
    null = r2.lib.providers.cdn.null:NullCdnProvider
    [r2.provider.auth]
    cookie = r2.lib.providers.auth.cookie:CookieAuthenticationProvider
    http = r2.lib.providers.auth.http:HttpAuthenticationProvider
    [r2.provider.support]
    zendesk = r2.lib.providers.support.zendesk:ZenDeskProvider
    [r2.provider.search]
    cloudsearch = r2.lib.providers.search.cloudsearch:CloudSearchProvider
    solr = r2.lib.providers.search.solr:SolrSearchProvider
    [r2.provider.image_resizing]
    imgix = r2.lib.providers.image_resizing.imgix:ImgixImageResizingProvider
    no_op = r2.lib.providers.image_resizing.no_op:NoOpImageResizingProvider
    unsplashit = r2.lib.providers.image_resizing.unsplashit:UnsplashitImageResizingProvider
    [r2.provider.email]
    null = r2.lib.providers.email.null:NullEmailProvider
    mailgun = r2.lib.providers.email.mailgun:MailgunEmailProvider
    """,
)
