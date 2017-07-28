import traceback
import warnings
import sys

def warn_with_traceback(message, category, filename, lineno, file=None, line=None):
    traceback.print_stack()
    log = file if hasattr(file,'write') else sys.stderr
    log.write(warnings.formatwarning(message, category, filename, lineno, line))

warnings.showwarning = warn_with_traceback

from lutbox_whisker import *
from chips_contrib.lut.lutcolors import *

xx = np.random.normal(5,size=10000)*10 # np.arange(10000)/1000.0
yy = map( lambda x: np.random.poisson(x), xx)
clear()

b = BoxWhiskerPlot( xx, yy )
b.plot()
b.set_region("opacity=0.9")
b.colorize( lut_colors( ["pink", "cadetblue"], colorsys="hsv"))
b.add_colorbar()
b.colorize( lut_colors( ["pink", "cadetblue"], colorsys="hsv"))


