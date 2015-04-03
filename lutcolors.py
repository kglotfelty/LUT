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
    def wrapper( color, cmap="usercmap1"):
        from pychips import info_current, set_image
        from pychips import chips_usercmap1, chips_usercmap2, chips_usercmap3

        trans = { 'usercmap1' : chips_usercmap1, 'usercmap2' : chips_usercmap2, 'usercmap3' : chips_usercmap3 }
        if cmap in trans:
            cmap = trans[cmap]
        else:
            if cmap not in [chips_usercmap1, chips_usercmap2, chips_usercmap3]:
                raise ValueError("Unsupported color map slot")

        # Do the real work!
        fun( color, cmap )
        
        ii = info_current()  # If any images, then change set colormap
        if ii and any( map(lambda x: ' Image [' in x, ii.split("\n"))):
            set_image( { 'colormap' : cmap } )

    return wrapper


@_check_cmap
def white_to_color(color, cmap="usercmap1"):
    """
    Create a custom color lookup table that fades from white to 
    the specified color.  The color map is loaded into the 
    specified slot (default="usercmap1")
    
    >>> white_to_color("darkgreen")    
    >>> white_to_color("firebrick", chips_usercmap2)    
    >>> white_to_color("slateblue", "usercmap3")
    """
    lut_colors( ['white', color], cmap)


@_check_cmap
def black_to_color(color, cmap="usercmap1"):
    """
    Create a custom color lookup table that fades from black to 
    the specified color. The color map is loaded into the 
    specified slot (default="usercmap1")
    
    >>> black_to_color("yellow")
    >>> black_to_color("firebrick", chips_usercmap2)    
    >>> black_to_color("slateblue", "usercmap3")
    """
    lut_colors( ['black', color], cmap )


@_check_cmap
def black_to_color_to_white( color, cmap="usercmap1"):
    """
    Create a custom color lookup table that fades from black to 
    the specified color to white. The color map is loaded into the 
    specified slot (default="usercmap1")
    
    >>> black_to_color_to_white("firebrick")
    >>> black_to_color_to_white("magenta", chips_usercmap2)
    >>> black_to_color_to_white("orange", cmap="usercmap3")
    
    """
    lut_colors( ['black', color, 'white'], cmap )

    
@_check_cmap
def lut_colors( colors, cmap="usercmap1"):
    """
    Create a custom color lookup table that fades from each
    color listed.  The color map is loaded into the 
    specified slot (default="usercmap1")
    
    >>> lut_colors( ["red","white","blue"] )
    >>> lut_colors( ["black","red","orange", "yellow","white"], chips_usercmap2 )
    >>> lut_colors( ["cyan", "magenta"], cmap="usercmap3" )
    
    """
    from pychips import load_colormap

    rgbs = map( _color_to_tripple, colors )
    rr = [x[0] for x in rgbs]
    gg = [x[1] for x in rgbs]
    bb = [x[2] for x in rgbs]
    load_colormap( rr, gg, bb, cmap )

