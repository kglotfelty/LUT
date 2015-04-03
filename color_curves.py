#
#  Copyright (C) 2015  Smithsonian Astrophysical Observatory
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
Color all existing plot objects (curves, lines, regions, points, histograms)
based on an external color lookup table (LUT) file.

"""


__all__ = [ 'color_curves', 'color_histograms', 'color_regions', 'color_points', 'color_lines']

from pychips import *
import numpy as np


def _linear( x ):
    return x


def _sample_from_lut( lutfile, num_sample, reverse=False, invert=False, xform=_linear):
    """
    Load a color lookup table and sample num_sample many colors from it.
    
    """
    from pycrates import read_file, get_colvals

    def _try_hard_to_locate( filename ):
        """
        Try to locate the LUT file just based on the name (eg returned
        by ds9).  Looks in CIAO-ish places then in home dir
        ~/.ds9
        """
        import os as os
        import glob as glob
        
        tox = [ "", "{}/data/".format( os.environ["ASCDS_INSTALL"] ), 
                  "{}/data/".format(os.environ["ASCDS_CONTRIB"]),
                  "{}/.ds9/".format(os.environ["HOME"])]

        tox.extend(glob.glob( "{}/.ds9/LUT/*/".format( os.environ["HOME"]) ) )
       
        for tt in tox:
            try:
                return read_file( tt+filename )
            except:
                pass
            
            try:
                return read_file( tt+filename+".lut")
            except:
                pass
        
        raise IOError("Could not find lookup table '{}'.  Maybe try full path?".format(filename ))


    def _create_hex_codes( rr, gg, bb ):
        """
        Store the 6digit hex color code for each curve/color
        """
        from hexify import hexify
        red = map( hexify, rr )
        grn = map( hexify, gg )
        blu = map( hexify, bb )
        
        hex_codes = map( lambda r,g,b: r+g+b, red, grn, blu )
        
        return hex_codes

    def _get_rgb( filename, reverse=False, invert=False ):
        """
        Load the color lookup table.
        
        Conver the rgb values into their 6digit hex color code
        """
        myclr = _try_hard_to_locate(filename)        
        rr = get_colvals(myclr, 0)*1.0 # multiply by 1.0 detach from crate        
        gg = get_colvals(myclr, 1)*1.0
        bb = get_colvals(myclr, 2)*1.0

        if reverse:
            rr = rr[::-1]
            gg = gg[::-1]
            bb = bb[::-1]
        
        if invert:
            rr = 1.0-rr
            gg = 1.0-gg
            bb = 1.0-bb

        hex_codes = _create_hex_codes(rr, gg, bb )
        return hex_codes
        
    hex_codes = _get_rgb( lutfile, reverse=reverse, invert=invert)

    if 1 == num_sample:
        return [hex_codes[0]]


    def _trans( fn, clrs ):
        nclrs = len(clrs)
        clrgrid = np.arange(1,nclrs+1)

        a = np.array(map( fn, clrgrid))
        z = fn(clrgrid)
        z0 = z-np.min(z)
        zp = (z0)/(1.0*np.max(z0))
        zz= np.round(zp*(nclrs-1.0)).astype("i4")
        return list(zz)

    tmap = _trans( xform, hex_codes )
    dl = (len(hex_codes)-1.0)/(num_sample-1.0)
    retval = [ hex_codes[tmap[int(i)]] for i in np.arange(0,num_sample)*dl]
    
    return retval
    

def _find_names_in( ii, name ):
    """
    Parse the info() output.  Find lines that start with the
    input name (eg Frame, Window, Plot, Curve) and then returns
    the individual instance of it which is stored in square
    brackets:
    
    
    >>> foo = info()
    >>> print foo
      Plot [plt1] (...stuff...)
    >>> _find_names_in( foo, "Plot")
    ["plt1"]
      
    
    """

    ff = filter( lambda x: x.strip().startswith(name) , ii )
    names = [ f.split("[")[1].split("]")[0] for f in ff ]
    return names


def _get_current_window_frame_plot():
    """
    We need to know the current window, frame, and plot to 
    correctly locate the curves in the current plot.
    """

    crnt = info_current()
    if None == crnt:
        raise RuntimeError("No {} objects to operate on".format(name))        

    crnt = crnt.split("\n")
    crnt_win = _find_names_in( crnt, "Window" )
    crnt_frm = _find_names_in( crnt, "Frame" )
    crnt_plot = _find_names_in( crnt, "Plot" )
    if None == crnt_plot or len(crnt_plot) == 0:
        # We only need to check plot since it cannot exist with a window and frame
        raise RuntimeError("No plots")
    if len(crnt_plot) > 1 :
        raise RuntimeError("Only 1 plot can be current")

    crnt_win = crnt_win[0]
    crnt_frm = crnt_frm[0]
    crnt_plot = crnt_plot[0]
    
    crnt_cfg = "Window [{}] Frame [{}] Plot [{}]".format( crnt_win, crnt_frm, crnt_plot)

    return crnt_cfg



def _get_flat_info():
    """
    The info() command returns a hierarchical list of objects which is 
    hard to filters.  This routine will append the window, frame, and 
    plot to each object in the info().

    So
    
    Window [win1]
      Frame [frm1]
        Plot [plt1]
          Curve [crv1]
          Curve [crv2]
        Plot [plt2]
          Curve [crv1]
    
    becomes:
    
    Window [win1] Frame [frm1] Plot [plt1] Curve [crv1]
    Window [win1] Frame [frm1] Plot [plt1] Curve [crv2]
    Window [win1] Frame [frm1] Plot [plt2] Curve [crv1]


    """

    # TODO: info() has options controled by preferences.  Should over
    # ride those here and reset at end.

    ii = info()
    if None == ii:
        raise RuntimeError("No {} objects to operate on".format(name))        
    ii = [ x.strip() for x in ii.split("\n")]    
    mtrx = []
    for i in ii:
        if i.startswith("Window"):
            atwin = i
            continue
        if i.startswith("Frame"):
            atfrm = i
            continue
        if i.startswith("Plot"):
            atplt = i.split("]")[0]+"]"  # plot lines have extra stuff after ]
            continue
        mtrx.append( "{} {} {} {}".format( atwin, atfrm, atplt, i ) )

    return mtrx


def _get_all_object_type_in_current_plot( plot_object):
    """
    Get all objects named "plot_object"
    """


    crnt_cfg = _get_current_window_frame_plot()
    flat_info = _get_flat_info()

    objects_in_current_plot = filter( lambda x: x.startswith( crnt_cfg), flat_info )
    objects_in_current_plot = [x.replace( crnt_cfg, "") for x in objects_in_current_plot]
    all_curves_in_current_plot = _find_names_in( objects_in_current_plot, plot_object)
    
    return all_curves_in_current_plot
    



def _color_object( lutfile, reverse=False, invert=False, skip=0, rskip=0, plot_object="Curve", setter=set_curve, xform=_linear):
    """
    Color all of a certain object type based on a color lookup table    
    
    """    
       
    curves = _get_all_object_type_in_current_plot( plot_object)
    if len(curves) == 0:
        raise RuntimeError("No {}s found in the current plot.".format(plot_object.lower()))

    colors = _sample_from_lut( lutfile, len(curves)+skip+rskip, reverse=reverse, invert=invert, xform=xform)
    
    from pychips.advanced import open_undo_block, close_undo_block
    open_undo_block()
    for cc in zip( curves, colors[skip:] ):
        setter(cc[0], "*.color={}".format(cc[1]))
    close_undo_block()


def color_curves( lutfile, reverse=False, invert=False, skip=0, rskip=0, xform=_linear):
    """
    Color all curves based on a color lookup table    
    
    Change the color of curves (lines, symbols, error bars) based on
    colors found in a color lookup table (LUT).
    
    The colors will be evenly sampled from the LUT.  If there are more 
    objects than colors, the same color will be used multiple times.
    
    >>> add_curve(np.arange(10), np.arange(10))
    >>> add_curve(np.arange(10), np.arange(10)+10)
    >>> add_curve(np.arange(10), np.arange(10)+20)
    >>> color_curves("red")
    
    This will locate the 'red.lut' color lookup table in $ASCDS_INSTALL/data
    and will sample 3 colors from it (first, middle, and last).  Each color
    will be applied to the objects in the order that they were created.
    
    The color lookup table can be reversed (last color first, first color last)
    or inverted where each red, green, and blue value are inverted, so
    black becomes white and red becomes cyan (green+blue):
    
    >>> color_curves( "red", reverse=True )
    >>> color_curves( "red", invert=True )
    >>> color_curves( "red", reverse=True, invert=True )

    The color lookup table can be compressed and shifted by artificially
    adding extra "skip" objects.  So for example if the LUT's first color
    is black and the background is black it will not be visible.  Using 
    a skip an extra sample is added that shifts and compresses the 
    color map. The rskip does the same thing for the upper end of the
    LUT.
    
    >>> color_curves( "red", skip=1 )
    >>> color_curves( "red", rskip=1)
    >>> color_curves( "red", skip=1, rskip=1)
    
    All the colors are undone with a single undo() command
    
    >>> color_curves( "green")
    >>> undo()

    Normally colors are linearly samples from the input lookup table.
    This can be changed by supplying an optional xform parameter
    
    >>> color_curves( "red", xform=np.log )
    >>> color_curves( "red", xform=lambda x: x**2)

    The routine will look for the color lookup table file 
    name in these directories:

        {name}.lut
        $ASCDS_INSTALL/data/{name}.lut 
        $ASCDS_INSTALL/contrib/{name}.lut

    or the full path to LUT file can be specified.  

    """    
    from pychips import set_curve
    
    _color_object( lutfile, plot_object="Curve", setter=set_curve, 
        reverse=reverse, invert=invert, skip=skip, rskip=rskip, xform=xform )


def color_histograms( lutfile, reverse=False, invert=False, skip=0, rskip=0, xform=_linear):
    """
    Color all histograms based on a color lookup table    
    
    Change the color of histogrmas (lines, symbols, error bars, fill) based on
    colors found in a color lookup table (LUT).
    
    The colors will be evenly sampled from the LUT.  If there are more 
    objects than colors, the same color will be used multiple times.
    
    >>> add_histogram( np.arange(10), np.arange(10)+1, np.random.randn(10))
    >>> add_histogram( np.arange(10), np.arange(10)+1, np.random.randn(10))
    >>> add_histogram( np.arange(10), np.arange(10)+1, np.random.randn(10))
    >>> set_histogram("all", "fill.style=solid fill.opacity=0.6")
    >>> color_histograms("red")
    
    This will locate the 'red.lut' color lookup table in $ASCDS_INSTALL/data
    and will sample 3 colors from it (first, middle, and last).  Each color
    will be applied to the objects in the order that they were created.
    
    The color lookup table can be reversed (last color first, first color last)
    or inverted where each red, green, and blue value are inverted, so
    black becomes white and red becomes cyan (green+blue):
    
    >>> color_histograms( "red", reverse=True )
    >>> color_histograms( "red", invert=True )
    >>> color_histograms( "red", reverse=True, invert=True )

    The color lookup table can be compressed and shifted by artificially
    adding extra "skip" objects.  So for example if the LUT's first color
    is black and the background is black it will not be visible.  Using 
    a skip an extra sample is added that shifts and compresses the 
    color map. The rskip does the same thing for the upper end of the
    LUT.
    
    >>> color_histograms( "red", skip=1 )
    >>> color_histograms( "red", rskip=1)
    >>> color_histograms( "red", skip=1, rskip=1)

    All the colors are undone with a single undo() command
    
    >>> color_histograms( "green")
    >>> undo()

    Normally colors are linearly samples from the input lookup table.
    This can be changed by supplying an optional xform parameter
    
    >>> color_histograms( "red", xform=np.log )
    >>> color_histograms( "red", xform=lambda x: x**2)
    
    The routine will look for the color lookup table file 
    name in these directories:

        {name}.lut
        $ASCDS_INSTALL/data/{name}.lut 
        $ASCDS_INSTALL/contrib/{name}.lut

    or the full path to LUT file can be specified.  
    """    
    from pychips import set_histogram
    
    _color_object( lutfile, plot_object="Histogram", setter=set_histogram, 
        reverse=reverse, invert=invert, skip=skip, rskip=rskip, xform=xform )


def color_regions( lutfile, reverse=False, invert=False, skip=0, rskip=0, xform=_linear):
    """
    Color all regions based on a color lookup table    
    
    Change the color of regions (fill and edge colors) based on
    colors found in a color lookup table (LUT).
    
    The colors will be evenly sampled from the LUT.  If there are more 
    objects than colors, the same color will be used multiple times.
    
    >>> add_curve( [1], [1] )
    >>> limits(XY_AXIS, 1, 10 )
    >>> add_region( 3, 4,4, 1 ) # Triangle
    >>> add_region( 4, 4, 8, 2 ) # Square
    >>> add_region( 6, 8, 4, 3 ) # Hexagon
    >>> color_regions("red")
    
    This will locate the 'red.lut' color lookup table in $ASCDS_INSTALL/data
    and will sample 3 colors from it (first, middle, and last).  Each color
    will be applied to the objects in the order that they were created.
    
    The color lookup table can be reversed (last color first, first color last)
    or inverted where each red, green, and blue value are inverted, so
    black becomes white and red becomes cyan (green+blue):
    
    >>> color_regions( "red", reverse=True )
    >>> color_regions( "red", invert=True )
    >>> color_regions( "red", reverse=True, invert=True )

    The color lookup table can be compressed and shifted by artificially
    adding extra "skip" objects.  So for example if the LUT's first color
    is black and the background is black it will not be visible.  Using 
    a skip an extra sample is added that shifts and compresses the 
    color map. The rskip does the same thing for the upper end of the
    LUT.
    
    >>> color_regions( "red", skip=1 )
    >>> color_regions( "red", rskip=1)
    >>> color_regions( "red", skip=1, rskip=1)

    All the colors are undone with a single undo() command
    
    >>> color_regions( "green")
    >>> undo()
    
    Normally colors are linearly samples from the input lookup table.
    This can be changed by supplying an optional xform parameter
    
    >>> color_regions( "red", xform=np.log )
    >>> color_regions( "red", xform=lambda x: x**2)

    The routine will look for the color lookup table file 
    name in these directories:

        {name}.lut
        $ASCDS_INSTALL/data/{name}.lut 
        $ASCDS_INSTALL/contrib/{name}.lut

    or the full path to LUT file can be specified.  
    """    
    from pychips import set_region
    
    _color_object( lutfile, plot_object="Region", setter=set_region, 
        reverse=reverse, invert=invert, skip=skip, rskip=rskip, xform=xform )


def color_points( lutfile, reverse=False, invert=False, skip=0, rskip=0, xform=_linear):
    """
    Color all regions based on a color lookup table    
    
    Change the color of regions (fill and edge colors) based on
    colors found in a color lookup table (LUT).
    
    The colors will be evenly sampled from the LUT.  If there are more 
    objects than colors, the same color will be used multiple times.
    
    >>> add_curve( [1], [1] )
    >>> limits(XY_AXIS, 1, 10 )
    >>> add_point( 4,4, "style=circle fill=True size=13" )
    >>> add_point( 4, 8,"style=square fill=True size=15" )
    >>> add_point( 8, 4,"style=plus fill=True size=18" )
    >>> color_points("red")
    
    This will locate the 'red.lut' color lookup table in $ASCDS_INSTALL/data
    and will sample 3 colors from it (first, middle, and last).  Each color
    will be applied to the objects in the order that they were created.
    
    The color lookup table can be reversed (last color first, first color last)
    or inverted where each red, green, and blue value are inverted, so
    black becomes white and red becomes cyan (green+blue):
    
    >>> color_points( "red", reverse=True )
    >>> color_points( "red", invert=True )
    >>> color_points( "red", reverse=True, invert=True )

    The color lookup table can be compressed and shifted by artificially
    adding extra "skip" objects.  So for example if the LUT's first color
    is black and the background is black it will not be visible.  Using 
    a skip an extra sample is added that shifts and compresses the 
    color map. The rskip does the same thing for the upper end of the
    LUT.
    
    >>> color_points( "red", skip=1 )
    >>> color_points( "red", rskip=1)
    >>> color_points( "red", skip=1, rskip=1)

    All the colors are undone with a single undo() command
    
    >>> color_points( "green")
    >>> undo()
    
    Normally colors are linearly samples from the input lookup table.
    This can be changed by supplying an optional xform parameter
    
    >>> color_points( "red", xform=np.log )
    >>> color_points( "red", xform=lambda x: x**2)

    The routine will look for the color lookup table file 
    name in these directories:

        {name}.lut
        $ASCDS_INSTALL/data/{name}.lut 
        $ASCDS_INSTALL/contrib/{name}.lut

    or the full path to LUT file can be specified.  
    """    
    from pychips import set_point
    
    _color_object( lutfile, plot_object="Point", setter=set_point, 
        reverse=reverse, invert=invert, skip=skip, rskip=rskip, xform=xform )



def color_lines( lutfile, reverse=False, invert=False, skip=0, rskip=0, xform=_linear):
    """
    Color all regions based on a color lookup table    
    
    Change the color of regions (fill and edge colors) based on
    colors found in a color lookup table (LUT).
    
    The colors will be evenly sampled from the LUT.  If there are more 
    objects than colors, the same color will be used multiple times.
    
    >>> add_curve( [1], [1] )
    >>> limits(XY_AXIS, 1, 10 )
    >>> add_hline(5, "thickness=4")
    >>> add_vline(8, "thickness=6")
    >>> add_line( [3,5,7], [8,2,8], "thickness=8")
    >>> color_lines("red")
    
    This will locate the 'red.lut' color lookup table in $ASCDS_INSTALL/data
    and will sample 3 colors from it (first, middle, and last).  Each color
    will be applied to the objects in the order that they were created.
    
    The color lookup table can be reversed (last color first, first color last)
    or inverted where each red, green, and blue value are inverted, so
    black becomes white and red becomes cyan (green+blue):
    
    >>> color_lines( "red", reverse=True )
    >>> color_lines( "red", invert=True )
    >>> color_lines( "red", reverse=True, invert=True )

    The color lookup table can be compressed and shifted by artificially
    adding extra "skip" objects.  So for example if the LUT's first color
    is black and the background is black it will not be visible.  Using 
    a skip an extra sample is added that shifts and compresses the 
    color map. The rskip does the same thing for the upper end of the
    LUT.
    
    >>> color_lines( "red", skip=1 )
    >>> color_lines( "red", rskip=1)
    >>> color_lines( "red", skip=1, rskip=1)

    All the colors are undone with a single undo() command
    
    >>> color_lines( "green")
    >>> undo()
    
    Normally colors are linearly samples from the input lookup table.
    This can be changed by supplying an optional xform parameter
    
    >>> color_lines( "red", xform=np.log )
    >>> color_lines( "red", xform=lambda x: x**2)

    The routine will look for the color lookup table file 
    name in these directories:

        {name}.lut
        $ASCDS_INSTALL/data/{name}.lut 
        $ASCDS_INSTALL/contrib/{name}.lut

    or the full path to LUT file can be specified.  
    """    
    from pychips import set_line
    
    _color_object( lutfile, plot_object="Line", setter=set_line, 
        reverse=reverse, invert=invert, skip=skip, rskip=rskip, xform=xform )

