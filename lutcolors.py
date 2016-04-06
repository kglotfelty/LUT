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
Create custom color lookup tables based on color names

This package provides a set of functions to create custom
color maps based on named colors ( eg 'orange', 'yellow', 'slateblue').

These color maps are only available for chips images.

A simple example looks like this:

>>> white_to_color("darkgreen")
>>> add_image(np.arange(100),10,10, { 'colormap' : chips_usercmap1 })
>>> add_colorbar(0.5,1)

which creates a custom color lookup table that fades from white to 
the color 'darkgreen'.  If an image is already displayed, the colormap
for current image will be automatically changed:

>>> add_image("img.fits")  # uses default gray-scale colors
>>> get_image().colormap
3
>>> black_to_color_to_white("mediumblue")
>>> get_image().colormap
8

The chips undo() command can be used to undo the automatic 
image color map setting; however, undo() does not restore the 
previous user color map settings.

The named colors are taken from the colors.par parameter file

>>> from paramio import plist
>>> plist("colors.par")

After the colormap is created, the image's colormap properties: 

  colormap_interpolate = True|False
  colormap_size=[1...256]
  invert_colormap=True|False

be set adjust the custom color lookup table.

>>> add_image("img.fits")  
>>> lut_colors( ['black', 'red', 'orange', 'yellow', 'white'])
>>> c = ChipsImage()
>>> c.colormap_interpolate = False
>>> c.colormap_size = 10
>>> c.invert_colormap = True
>>> set_image(c)

"""

__all__ = [ 'white_to_color', 'black_to_color', 'black_to_color_to_white', 'lut_colors']

import numpy as np

def _color_to_tripple( color ):
    """
    Convert a named color into a normalized RGB tripple
    
    >>> _color_to_tripple("red")
    [1.0, 0, 0]
    
    The named colors are taken from the 'colors.par' 
    parameter file which includes a superset of 
    the named colors available in chips.
    
    """
    from paramio import pget, plist

    if color not in plist("colors.par"):
        raise ValueError("Cannot locate color='{}' in colors.par".format(color))

    rgb = pget('colors.par', color )    
    rgb = rgb.split()
    rgb = map(float, rgb)
    return rgb


def _check_cmap(fun):
    """
    Decorator to check for valid color map value.  Translates
    the string version to the integer version need by load_colormap
    """
    from functools import wraps

    @wraps(fun)
    def wrapper( color, **kwargs):
        from pychips import info_current, set_image
        from pychips import chips_usercmap1, chips_usercmap2, chips_usercmap3

        if "cmap" not in kwargs:
            cmap = chips_usercmap1
            kwargs["cmap"] = cmap
        else:
            cmap = kwargs["cmap"]
            trans = { 'usercmap1' : chips_usercmap1, 'usercmap2' : chips_usercmap2, 'usercmap3' : chips_usercmap3 }
            if cmap and cmap in trans:
                kwargs["cmap"] = trans[cmap]
            else:
                if cmap not in [chips_usercmap1, chips_usercmap2, chips_usercmap3]:
                    raise ValueError("Unsupported color map slot")

        # Do the real work!
        fun( color, **kwargs )
        
        ii = info_current()  # If any images, then change set colormap
        if cmap and ii and any( map(lambda x: ' Image [' in x, ii.split("\n"))):
            set_image( { 'colormap' : cmap } )

    return wrapper


def white_to_color(color, **kwargs):
    """
    Create a custom color lookup table that fades from white to 
    the specified color.  The color map is loaded into the 
    specified user color map
    
    >>> white_to_color("darkgreen")    
    >>> white_to_color("firebrick", cmap=chips_usercmap2)    
    >>> white_to_color("slateblue", cmap="usercmap3")

    The colors can be interpolated either in the RGB color system (default)
    or in the HSV or HLS color systems.
    
    >>> white_to_color("red", colorsys="rgb")
    >>> white_to_color("red", colorsys="hsv")
    >>> white_to_color("red", colorsys="hls")

    The default is to create a lookup table with 256 colors.  
    The number of colors can be changed using the num_color parameter
    
    >>> white_to_color("yellow", num_colors=16)
    
    The color lookup table can be saved to an ASCII file using 
    the outfile parameter
    
    >>> white_to_color("purple", outfile="purple.lut")
    
    The outfie is always clobbered if it exists.
    """
    lut_colors( ['white', color], **kwargs)


def black_to_color(color, **kwargs):
    """
    Create a custom color lookup table that fades from black to 
    the specified color. The color map is loaded into the 
    specified slot (default="usercmap1")
    
    >>> black_to_color("yellow")
    >>> black_to_color("firebrick", chips_usercmap2)    
    >>> black_to_color("slateblue", "usercmap3")

    The colors can be interpolated either in the RGB color system (default)
    or in the HSV or HLS color systems.
    
    >>> black_to_color("red", colorsys="rgb")
    >>> black_to_color("red", colorsys="hsv")
    >>> black_to_color("red", colorsys="hls")

    The default is to create a lookup table with 256 colors.  
    The number of colors can be changed using the num_color parameter
    
    >>> black_to_color("yellow", num_colors=16)
    
    The color lookup table can be saved to an ASCII file using 
    the outfile parameter
    
    >>> black_to_color("purple", outfile="purple.lut")
    
    The outfie is always clobbered if it exists.
    """
    lut_colors( ['black', color], **kwargs )


def black_to_color_to_white( color, **kwargs):
    """
    Create a custom color lookup table that fades from black to 
    the specified color to white. The color map is loaded into the 
    specified slot (default="usercmap1")
    
    >>> black_to_color_to_white("firebrick")
    >>> black_to_color_to_white("magenta", chips_usercmap2)
    >>> black_to_color_to_white("orange", cmap="usercmap3")

    The colors can be interpolated either in the RGB color system (default)
    or in the HSV or HLS color systems.
    
    >>> black_to_color_to_white("red", colorsys="rgb")
    >>> black_to_color_to_white("red", colorsys="hsv")
    >>> black_to_color_to_white("red", colorsys="hls")

    The default is to create a lookup table with 256 colors.  
    The number of colors can be changed using the num_color parameter
    
    >>> black_to_color_to_white("yellow", num_colors=16)
    
    The color lookup table can be saved to an ASCII file using 
    the outfile parameter
    
    >>> black_to_color_to_white("purple", outfile="purple.lut")
    
    The outfie is always clobbered if it exists.
    
    """
    lut_colors( ['black', color, 'white'], **kwargs )



def _circular_interp( x0, xx, hh ):
    # Hue values are cyclical going from 0 to 1.  To interpolate
    # we pick the shortest path (length < 0.5) and shift the 
    # values so that we can interpolate them.

    h_out = []
    for x in x0:
        idx = np.where(xx<=x)[0][-1]
        if idx == len(hh)-1:
            hh_o = hh[-1]
        elif hh[idx+1]-hh[idx] > 0.5 :
            th = hh[:]
            th[idx] = th[idx]+1
            hh_o = np.interp( x, xx, th )
            hh_o = np.mod( hh_o, 1.0 )
        elif hh[idx+1]-hh[idx] < -0.5 :
            th = hh[:]
            th[idx+1] = th[idx+1]+1
            hh_o = np.interp( x, xx, th )
            hh_o = np.mod( hh_o, 1.0 )
        else:
            hh_o = np.interp( x, xx, hh )
        h_out.append(hh_o)
        
    return np.array( h_out )

    

@_check_cmap
def lut_colors( colors, cmap="usercmap1", num_colors=256, outfile=None, colorsys="rgb"):
    """
    Create a custom color lookup table that fades from each
    color listed.  The colors are interpoalted in HSV colorspace
    The color map is loaded into the 
    specified slot (default="usercmap1")
    
    >>> lut_colors( ["red","white","blue"] )
    >>> lut_colors( ["black","red","orange", "yellow","white"], chips_usercmap2 )
    >>> lut_colors( ["cyan", "magenta"], cmap="usercmap3" )
    
    The colors can be interpolated either in the RGB color system (default)
    or in the HSV or HLS color systems.
    
    >>> lut_colors(["pink", "cadetblue"], colorsys="rgb")
    >>> lut_colors(["pink", "cadetblue"], colorsys="hsv")
    >>> lut_colors(["pink", "cadetblue"], colorsys="hls")

    The default is to create a lookup table with 256 colors.  
    The number of colors can be changed using the num_color parameter
    
    >>> lut_colors(["yellow","mediumblue"], num_colors=16)
    
    The color lookup table can be saved to an ASCII file using 
    the outfile parameter
    
    >>> lut_colors(["green","purple"], outfile="purple.lut")
    
    The outfie is always clobbered if it exists.
    """

    from colorsys import rgb_to_hsv, hsv_to_rgb, rgb_to_hls, hls_to_rgb
    from pychips import load_colormap

    def _noop( x,y,z):  return x,y,z

    rgbs = map( _color_to_tripple, colors )

    if "rgb" == colorsys:
        hsvs = rgbs
        interp = np.interp
        invert = _noop
    elif "hsv" == colorsys:
        hsvs = map( lambda x: rgb_to_hsv(*x), rgbs )
        interp = _circular_interp
        invert = hsv_to_rgb
    elif "hls" == colorsys:
        hsvs = map( lambda x: rgb_to_hls(*x), rgbs )
        interp = _circular_interp
        invert = hls_to_rgb
    else:
        raise ValueError("Unknow value of colorsys")

    hh = [x[0] for x in hsvs]
    ss = [x[1] for x in hsvs]
    vv = [x[2] for x in hsvs]

    xx = np.arange(len(hh))/(len(hh)-1.0)
    x0 = np.arange(num_colors)/(num_colors-1.0)

    hh_i = interp( x0, xx, hh )
    ss_i = np.interp( x0, xx, ss )
    vv_i = np.interp( x0, xx, vv )

    rgbs_i = map( invert, hh_i, ss_i, vv_i )
    
    rr_i = [x[0] for x in rgbs_i]
    gg_i = [x[1] for x in rgbs_i]
    bb_i = [x[2] for x in rgbs_i]
        
    load_colormap( rr_i, gg_i, bb_i, cmap )

    if None == outfile:
        return
    
    lines = [ "{}\t{}\t{}\n".format(*a) for a in zip(rr_i,gg_i,bb_i) ]    
    with open(outfile, "w") as fp:
        fp.writelines( lines )
    
    

