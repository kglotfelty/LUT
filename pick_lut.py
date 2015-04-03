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
Create an interactive object to select a color map

Create a new chips window that will contain a sample image showing
each color map.  The returned object has a pick_lut() method that
allows the user to click to select the desired color lookup table.

  >>> from chips_contrib.pick_lut import *
  >>> ll = LUT_Picker( "/soft/ciao/data/")
  >>> ll.pick_lut()
  'cool'
  
  >>> ds9 = pick_ds9()
  >>> ximage = pick_ximage()
  >>> imagej = pick_imagej()
  
"""


__all__ = [ "LUT_Picker", "LUT_Picker_Chips", "pick_ds9", "pick_imagej", "pick_ximage", "pick_chips"]

from pychips import *

class LUT_Picker():
    """
    Load color lookup tables into a new windw and return an object that
    allows them to be selected.
    
    The LUT_Picker class takes a directory+basename as the input to 
    the constructor.  It will do a wild card/glob search for files with a
    '.lut' suffix, create a new chips window and return an object that
    can be used to pick the color map by clicking in the window.
    
    For example to load all the CIAO color maps:
    
    >>> ll = LUT_Picker("/soft/ciao/data/")
    >>> ll.pick_lut()
    'cool'
    
    Loads only the files in the data directory begining with the letter 'c'
    
    >>> ll = LUT_Picker("/soft/ciao/data/c")
    >>> ll.pick_lut()

    This routine uses color map slot chips_usercmap1. The default color map
    in that slot cannot be restored.  It will be left with the last
    color map that was loaded.

    Note:  It may take a few to several seconds for the color maps to load.
    Please do not move or resize the Chips window while this is happening
    as it may cause the chipsServer to crash.
    
    """


    @staticmethod
    def _get_current_object_name( name ):
        """
        We often need the chips name/id of the current object : curve, axis, etc.
        This can only be retrieved by parsing the info_current() command.
        """
        ii = info_current().split("\n")
        ff = filter( lambda x: x.strip().startswith(name), ii )
        ff = ff[-1] # last one
        name = ff.split("[")[1]
        name = name.split("]")[0]
        return name

    def __init__(self, cmaps):
        
        self.cmaps = cmaps
        self._build_list_of_cmaps(cmaps)
        self._create_window_and_grid()
        self._add_images()
        if self.origplt:
            set_current_window(self.origwin)
            set_current_frame(self.origfrm)
            set_current_plot(self.origplt)

    def __del__( self ):
        try:
            delete_window( self.win_name)
        except:
            pass
            
        
    def _build_list_of_cmaps( self, cmaps):        
        """
        
        """
        from glob import glob
        from math import sqrt


        if type(cmaps) == str:
            self.lut = glob( cmaps+"*.lut" )
        else:
            self.lut = [ c for c in cmaps]

        self.lut.sort()

        if len(self.lut) > 100:
            print "Only the first 100 color maps will be used"
            self.lut = self.lut[:100]

        self.nx = int(sqrt( len(self.lut)))
        self.ny = self.nx+1
        if self.nx * self.ny < len(self.lut):
            self.ny = self.ny+1


    def _create_window_and_grid(self):
        """
        
        """

        try:
            self.origwin = self._get_current_object_name("Window")
            self.origfrm = self._get_current_object_name("Frame")
            self.origplt = self._get_current_object_name("Plot")
        except:
            self.origwin = None
            self.origfrm = None
            self.origplt = None


        add_window(512,512,"pixels","stem=CMAP")
        self.win_name = self._get_current_object_name("Window")
        set_window(self.win_name, "display=0")


        old_pref = {}
        for pp in [ "bottom", "top", "left", "right" ]:
            nm = "plot.{}margin".format(pp)
            old_pref[nm] = get_preference( nm )    
            set_preference(nm, "0.01")

        split( self.ny, self.nx )
        adjust_grid_gaps(0.005, 0.005)

        for pp in old_pref:
            set_preference( pp, old_pref[pp] )

        set_plot("all", "style=open")
        set_window(self.win_name, "display=1")




    def _add_images( self ):
        """
        
        """
        from os.path import basename as bname

        set_window(self.win_name, "display=0")

        frm_imgs = self._get_current_object_name("Frame")
        add_frame()
        frm_load = self._get_current_object_name("Frame")
        
        add_label( 0.10, 0.25, "Please do not move or resize this window while loading", "size=12 fontstyle=italic")
        add_label(0.15, 0.5, "Loading", "size=20 valign=0.5 halign=0")
        set_plot("style=open")
        set_window(self.win_name, "display=1")

        self.locations = {}

        cbar = range(256)*256
        for cmap in enumerate( self.lut ):

            iname = bname( cmap[1]).replace(".lut","")

            set_current_frame( frm_load )
            set_label_text( "({}/{}) Loading {}".format( cmap[0]+1, len(self.lut), iname.replace("_",r"\_") ))

            set_current_frame( frm_imgs )
            plt = "plot{}".format(cmap[0]+1)
            set_current_plot(plt)
            load_colormap( cmap[1] )

            add_image( cbar, 256, 256, "colormap=usercmap1 stem={}#".format(iname) )
            hide_axis("all")
            hide_minor_ticks()
            hide_major_ticks()

            plt_obj = get_plot()

            self.locations[iname] = { 'xmin' : plt_obj.leftmargin, 
                                      'ymin' : plt_obj.bottommargin,
                                      'xmax' : 1.0 - plt_obj.rightmargin,
                                      'ymax' : 1.0 - plt_obj.topmargin,
                                      'fullpath' : cmap[1] } 
        hide_frame( frm_load)
        set_current_frame( frm_imgs)
        
        
                        
    def _match_location( self, winx, winy ):
        """
        
        """
        for l in self.locations:
            ll = self.locations[l]
            if ( ll['xmin'] <= winx <= ll['xmax'] ) & ( ll['ymin'] <= winy <= ll['ymax'] ):
                return ll["fullpath"]
        
        return None


    def pick_lut(self):
        
        try:
            oldwin = self._get_current_object_name("Window")
            oldfrm = self._get_current_object_name("Frame")
            oldplt = self._get_current_object_name("Plot")
        except: 
            oldwin = None
            oldfrm = None
            oldplt = None
            
        try:
            set_current_window( self.win_name )
        except:
            if self.cmaps:
                self.__init__(self.cmaps)
            else:
                self.__init__()

        cid = ChipsId()
        cid.coord_sys = FRAME_NORM
        a = get_pick(cid)

        if oldplt:
            set_current_window( oldwin )
            set_current_frame(oldfrm)
            set_current_plot(oldplt)
        
        winx = a[0][0]
        winy = a[1][0]
        
        cmap = self._match_location( winx, winy )

        
        if not cmap:
            raise RuntimeError("No colormap found at that location, try again")
        
        return cmap


class LUT_Picker_Chips(LUT_Picker):
    """
    Create a LUT_Picker object for the internal chips color maps.
    
    >>> cmaps = LUT_Picker_Chips()
    >>> add_image( np.arange(100),10,10)
    >>> set_image( { 'cmap' : cmaps.pick() } )
    
    """
    def __init__(self):
        
        self.cmaps = None
        self._build_list()
        self._create_window_and_grid()
        self._add_images()
        if self.origplt:
            set_current_window(self.origwin)
            set_current_frame(self.origfrm)
            set_current_plot(self.origplt)


    def _build_list(self):
        from math import sqrt
        self.lut = ["red", "green", "blue", "grayscale", "rainbow", "hsv", "heat", "cool", "usercmap1", "usercmap2", "usercmap3" ]
        self.nx = int(sqrt( len(self.lut)))
        self.ny = self.nx+1

    def _add_images( self ):
        """
        Replace above with 
        """

        self.locations = {}
        set_window(self.win_name, "display=0")

        cbar = range(256)*256
        for cmap in enumerate( self.lut ):
            plt = "plot{}".format(cmap[0]+1)
            set_current_plot(plt)            
            iname = cmap[1]

            add_image( cbar, 256, 256, "colormap={} stem={}#".format(iname,iname) )
            hide_axis("all")
            hide_minor_ticks()
            hide_major_ticks()

            plt_obj = get_plot()

            self.locations[iname] = { 'xmin' : plt_obj.leftmargin, 
                                      'ymin' : plt_obj.bottommargin,
                                      'xmax' : 1.0 - plt_obj.rightmargin,
                                      'ymax' : 1.0 - plt_obj.topmargin,
                                      'fullpath' : cmap[1] } 

        set_window(self.win_name, "display=1")




def pick_ds9():
    """
    Create a LUT_Picker objects based on the ds9 color maps found in the
    $ASCDS_INSTALL/data directory.
    
    >>> ds9 = pick_ds9()
    >>> ds9.pick_lut()
    
    """    
    from paramio import plist, pget    
    luts = [ pget("lut",x) for x in plist( "lut") if x != 'mode' ]
    ds9 = LUT_Picker( luts ) 
    return ds9
    

def pick_ximage():
    """
    Create a LUT_Picker object based on the XImage color maps found in the
    $ASCDS_INSTALL/contrib/data directory.  The files are listed in the
    ximage_lut.par parameter file.

    >>> xi = pick_ximage()
    >>> xi.pick_lut()
    
    """
    from paramio import plist, pget    
    luts = [ pget("ximage_lut",x) for x in plist( "ximage_lut") if x != 'mode' ]
    ximage = LUT_Picker( luts ) 
    return ximage
    

def pick_imagej():
    """
    Create a LUT_Picker object based on the ImageJ color maps found in the
    $ASCDS_INSTALL/contrib/data directory.  The files are listed in the
    imagej_lut.par parameter file.

    >>> ij = pick_imagej()
    >>> ij.pick_lut()
    
    """

    from paramio import plist, pget    
    luts = [ pget("imagej_lut",x) for x in plist( "imagej_lut") if x != 'mode' ]
    imagej = LUT_Picker( luts ) 
    return imagej

    
def pick_chips():
    """
    Create a LUT_Picker object based on the internal chips color maps.
    This color maps can only be used with Chips Images.
    
    >>> ch = pick_chips()
    >>> ch.pick_lut()
    'red'
    
    """

    return LUT_Picker_Chips()
    
