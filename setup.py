

import os
import sys

assert "ASCDS_INSTALL" in os.environ

ver = sys.version_info
os.environ["PYVER"] = "python{}.{}".format(ver[0],ver[1])

from distutils.core import setup


setup( name='LUTPlot',
        version='0.9.0',
        description='Create and Colorize plots using Look Up Tables',
        author='Anonymous',
        author_email='WhoDat@cfa.harvard.edu',
        url='https://github.com/kglotfelty/legend/',
        packages=['.']

        )

