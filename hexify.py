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
Return hexidecimal color code for X11 named colors

The CIAO parameter file 'colors.par' contains all the standard
X11 named colors which is a superset of the named colors available
in chips.  For example chips has 'steelblue' but does not know
about 'steelblue1', 'steelblue2', etc.

This routine will look up the RGB value in colors.par and return
the hexidecimal color code.

"""

__all__ = ['hexify', 'color_by_name', 'color_by_value', 'all_colors']


_colors_dot_par_ = "colors.par"

def hexify( value ):
    """
    Convert decimal 0.0-1.0 into a byte 0-255 in hexidecimal

    >>> hexify(0)
    '00'
    >>> hexify(1)
    'FF'
    >>> hexify(0.5)
    '80'
    >>> hexify(2)
    ValueError: Color values must be between 0 and 1
    """
    if value < 0 or value > 1:
        raise ValueError("Color values must be between 0 and 1")

    val = value * 256
    ival = int(val)  # truncate
    ival = ival if ival <= 255 else 255  # handle 1.0 case (ie 256)
    sval = "{:02X}".format(ival)
    return sval


def color_by_value( red, green, blue ):
    """
    Return hex code for color tripple 

    Each color channel value must be 0 <= value <= 1.

    >>> color_by_value( 1, 0, 0 )
    'FF0000'
    >>> color_by_value( 0.2, 0.5, 0.7 )
    '3380B3'
    """
    red = hexify( red )
    grn = hexify( green )
    blu = hexify( blue )    
    return red+grn+blu


def color_by_name( color_name ):
    """
    Return hexidecimal color code string for the named color:
    
    >>> color_by_name("blue")
    '0000FF'
    >>> color_by_name("steelblue4")
    '36648B'
    >>> add_curve([1,2],[3,4])
    >>> c = ChipsCurve()
    >>> c.symbol.color = color_by_name("thistle")
    >>> set_curve(c)
    """
    from paramio import pget, plist
    
    has = plist(_colors_dot_par_)
    if color_name not in has:
        raise ValueError("Color '{}' was not found in '{}'".format(color_name, _colors_dot_par_))
        
    rgb = [float(x) for x in pget( _colors_dot_par_, color_name ).split()]
    
    return color_by_value( *rgb )

def all_colors():
    """
    Return a dictionary with all CIAO colors hexified
    
    >>> clrs = all_colors()
    >>> clrs['firebrick']
    'B22222'
    """
    from paramio import pget, plist
    
    has = plist(_colors_dot_par_)
    retval = {}

    for color_name in has:        
        if color_name == 'mode': continue
        rgb = [float(x) for x in pget( _colors_dot_par_, color_name ).split()]
        retval[color_name] = color_by_value( *rgb )

    return retval
    
