from __future__ import print_function

import sys
#sys.path.insert( 0, "/data/lenin2/Projects/LUT")
#sys.path.insert( 0, "/data/da/Docs/scripts/dev/lib/python2.7/site-packages/")

# Load all the LUT routines 
from chips_contrib.lut import *

# Add some data to a plot

for x in range(8):
    x0 = np.random.rand()*20+10
    y0 = np.random.rand()*20+10
    sig = np.random.rand()*2+2
    xx = np.random.randn(1000)*sig+x0
    yy = np.random.randn(1000)*sig+y0
    add_curve(xx,yy, "symbol.style=circle symbol.size=2 symbol.fill=0 line.style=none")


###xx = np.arange(10)

###add_curve( xx, xx**0)
###add_curve( xx, xx**1)
###add_curve( xx, xx**2)
###add_curve( xx, xx**3)




# Use color map by name -- it will try to find the correct .lut file:

# Use from ciao/ds9's 
color_curves("red")  

# Use from contrib (imagej)

color_curves("smart",skip=1,rskip=1)



# Launch the LUT color picker for the ds9 color maps
ds9 = pick_ds9()

# A new window is created with each of the ds9 color maps.  Now 
# pick a color
cmap = ds9.pick_lut()

# Click on the desired color map in the CMAP2 window
print(cmap)

# Apply colors from LUT to each curve.
color_curves( cmap )

# The LUT is sampled evenly from start to end.  If you want to skip the ends
# you can add a skip (left) or rskip (right)
color_curves( cmap, skip=1, rskip=1 )

# Load the 5-color, ColorBrewer LUT's from my off-to-the-side cache:
cb = LUT_Picker( "/data/lenin2/Projects/LUT/CB/CB_*08" )

# Apply color to curves
color_curves( cb.pick_lut() )

# Undo color changes
undo()

# Get back
redo()

# ----------------


add_window()


for x in range(5):
    data = np.random.randn(1000)*1+x
    hist = np.histogram(data)
    xl = hist[1][:-1]
    xh = hist[1][1:]
    y = hist[0]
    add_histogram( xl, xh, y, "fill.style=solid fill.opacity=0.2")


gmt = LUT_Picker("/data/lenin2/Projects/LUT/gmt/")

color_histograms( gmt.pick_lut())


