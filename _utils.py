"""
Utility routines that lutplot and colorcurves share

"""

from __future__ import absolute_import

def _try_hard_to_locate( filename ):
    """
    Try to locate the LUT file just based on the name (eg returned
    by ds9).  Looks in CIAO-ish places then in home dir
    ~/.ds9
    """
    import os as os
    import glob as glob
    from pycrates import read_file, get_colvals
    
    tox = [ "", "{}/data/".format( os.environ["ASCDS_INSTALL"] ), 
              "{}/data/".format(os.environ["ASCDS_CONTRIB"]),
              "{}/.ds9/".format(os.environ["HOME"])]

    tox.extend(glob.glob( "{}/.ds9/LUT/*/".format( os.environ["HOME"]) ) )

    tab = None
    for tt in tox:
        
        try:
            tab = read_file( tt+filename )
            break
        except:
            pass
        
        try:
            tab = read_file( tt+filename+".lut")
            break
        except:
            pass

    if tab is None:
        raise IOError("Could not find lookup table '{}'.  Maybe try full path?".format(filename ))
    
    rr = get_colvals(tab, 0)*1.0 # multiply by 1.0 detach from crate        
    gg = get_colvals(tab, 1)*1.0
    bb = get_colvals(tab, 2)*1.0
    return (rr, gg, bb)

def _unzip_stuff( filename ):        
    if 3 != len(filename):
        raise IndexError("The input tuple must have 3 elements")
    
    r = filename[0]
    g = filename[1]
    b = filename[2]

    if len(r) != len(g) or len(r) != len(b) or len(g) != len(b):
        raise IndexError("Must have the same number of red, green, and blue values")


    chk = [(x<0.0 or x>1.0) for x in r]
    if any(chk):
        raise IndexError( "All the red values must be between 0 and 1.")
    chk = [(x<0.0 or x>1.0) for x in g]
    if any(chk):
        raise IndexError( "All the green values must be between 0 and 1.")
    chk = [(x<0.0 or x>1.0) for x in b]
    if any(chk):
        raise IndexError( "All the blue values must be between 0 and 1.")

    return (r,g,b)

def _create_hex_codes( rr, gg, bb ):
    """
    Store the 6digit hex color code for each curve/color
    """
    from .hexify import hexify
    red = [hexify(x) for x in rr ]
    grn = [hexify(x) for x in gg ]
    blu = [hexify(x) for x in bb ]
    
    hex_codes = [r+g+b for r,g,b in zip(red,grn,blu)]
    
    return hex_codes

def get_rgb_hexcodes( rr, gg, bb):

    hex_codes = _create_hex_codes(rr, gg, bb )
    return hex_codes


def get_rgb_values( filename, reverse=False, invert=False ):
    """
    Load the color lookup table.
    
    Conver the rgb values into their 6digit hex color code
    """

    if isinstance( filename, type("foo") ):
        rr,gg,bb = _try_hard_to_locate(filename)        
    else:
        rr,gg,bb = _unzip_stuff(filename)

    if reverse:
        rr = rr[::-1]
        gg = gg[::-1]
        bb = bb[::-1]
    
    if invert:
        rr = 1.0-rr
        gg = 1.0-gg
        bb = 1.0-bb

    return rr, gg, bb
