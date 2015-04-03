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
Create a color Look Up Table (LUT) coded plot in Chips.


    lut = LUTPlot( filename , cmap=chips_usercmap1)
        Create a new plot object with the color lookuptable from the
        specified file name.

        Reads an ASCII color lookup table, a file with 3 columns
        that represent the red, green, and blue fractions.

        >>> lut = LUTPlot( "/soft/ciao/data/bb.lut")
        
        CIAO has "lut.par" that points to the lookup tables 
        that match ds9.
        
        Additionally, the CIAO contrib package has 2 additional sets
        of .lut files which are discussed here:
        http://cxc.harvard.edu/ciao/threads/auxlut/

        You can use the parameter interface to access the file names.
        
        >>> from paramio import pget
        >>> sls_filename = pget( "lut", "sls" )
        >>> lut = LUTPlot( sls_filename )

        The object will also look in standard CIAO data directories
        for a matching file name:
        
        >>> lut = LUTPlot("bb")
        
        will load the $ASCDS_INSTALL/data/bb.lut file.

        The color lookup table is by default loaded into first
        user color lookup table slot: 'chips_usercmap1'.  This can
        be changed 
        
        >>> lut = LUTPlot( "/soft/ciao/data/grey.lut", cmap=chips_usercmap2)
        
    
    LUTPlot.plot( x, y, z, name="lutpoint", zgrid=None)
    
        Will create a scatter plot at each X,Y value.  The Z values are 
        color coded by the r,g,b values that come from read_lut.
    
        For example:

        >>> tab = read_file("pcad_asol1.fits")
        >>> x = tab.get_column("ra").values
        >>> y = tab.get_column("dec").values
        >>> z = tab.get_column("time").values
        >>> lut.plot( x,y,z )

        The z values are by default split into equally spaced
        bins (colors) based on the number of colors in the 
        color map.  Users can supply their own grid of colors
        by passing in a zgrid
        
        >>> zlo = range(256)
        >>> zhi = range(1,257)
        >>> zgrid = zip(zlo, zhi)
        >>> lut.plot(x,y,z,zgrid=zgrid)
        
        
    LUTPlot.add_colorbar()

        After the data are plotted, then you can add a color bar
        using this command.

        >>> lut.add_colorbar()
        
        Once the color bar is created it is easiest to manipulate it
        with the GUI 
        
        >>> show_gui()        
    
    LUTPlot.replace_cmap(filename)

        After a dataset has been plotted you might want to change the
        color map.  This requires changing all the individual curves.  
        
        It is required that the old color map and the new color map
        must have the same number of colors.
    
        >>> lut.replace_cmap("/soft/ciao/data/red.lut")

    LUTPlot.set_curve( params )
    
        Once the data are plotted it may be necessary to change the 
        curve properties -- change symbol, size, add lines, etc.
        This routine will apply the curve parameters to all
        the LUTPlot curves it has created.
        
        >>> lut.set_curve("symbol.style=circle")
        >>> lut.set_curve(["symbol.style", "circle"])
        >>> c = ChipsCurve()
        >>> c.symbol.style = 'circle'
        >>> lut.set_curve(c)
    
    LUTPlot.shuffle()
        
        The shuffle command can be used to shuffle the order curves
        are drawn in which can be useful when the curves overlap.
        
        >>> lut.shuffle()
        
        
    

"""

import numpy as np
from pychips.advanced import open_undo_block, close_undo_block
from pychips import *
from pycrates import read_file, get_colvals
from hexify import color_by_value


__all__ = [ "LUTPlot" ]





class LUTPlot(object):
    """
    
    A lookup table (LUT) is a simple ASCII file with 3 columns representing
    Red, Green, and Blue values ranging from 0 to 1.
    
    This routine will read in the lookup table. 
    It sets the user color map (default usercmap1) to the new table
    and returns a tuple with the  Red, Green, and Blue lists.    

    Example:
    
        >>> rgb = LUTPlot( "/soft/ciao/data/sls.lut" )        
      or
        >>> lut = LUTPlot( "/soft/ciao/data/bb.lut", cmap=chips_usercmap2 )
    
    """    

    num_colors = None
    filename = None
    cmap = None
    curves = None
    image = None
    min_z = None
    max_z = None
    rx = None
    ry = None
    lut_win = None
    lut_frame = None
    lut_plot = None
    old_win = None
    old_frame = None
    old_plot = None
    order = None

    @staticmethod
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


    def _create_hex_codes( self, rr, gg, bb ):
        """
        Store the 6digit hex color code for each curve/color
        """
        self.hex_codes = map( color_by_value, rr, gg, bb )



    def __init__( self, filename, cmap=chips_usercmap1, reverse=False, invert=False ):
        """
        Load the color map file values and set the chips user color map.
        
        >>> lut = LUTPlot( "/soft/ciao/data/bb.lut")
        
        The object will try to locate the color table by name
        based on common locations where it might be.  
        
        >>> lut = LUTPlot( "bb" )
        
        Alternatively users can use the paramio module to locate files:
        
        >>> from paramio import pget
        >>> lut = LUTPlot( pget("imagej_lut", "heart")) 
        
        By default the object uses the 1st user color map slot
        "chip_usercmap1",  this can be changed with the cmap
        parameter:
        
        >>> lut = LUTPlot( "heart", cmap=chips_usercmap2 )
        
        The color map can be manipulated in two ways.  The order of the
        colors reverse, and/or the colors themselves inverted
        
        >>> lut = LUTPlot( "bb", reverse=True )
        >>> lut = LUTPlot( "bb", invert=True )
        >>> lut = LUTPlot( "bb", invert=True, reverse=True )

        """
        if cmap not in [chips_usercmap1,chips_usercmap2,chips_usercmap3]:
            raise ValueError("Invalid color map selected")


        rr,gg,bb = self._get_rgb( filename, reverse=reverse, invert=invert )

        load_colormap( rr,gg,bb, cmap )          # new in ciao4.6, load from arrays

        self.num_colors = len(self.hex_codes)
        self.filename = filename
        self.cmap = cmap
        
    def _get_color_code( self, ii ):
        return self.hex_codes[ii]


    def _get_rgb( self, filename, reverse=False, invert=False ):
        """
        Load the color lookup table.
        
        Conver the rgb values into their 6digit hex color code
        """

        myclr = self._try_hard_to_locate(filename)        
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

        self._create_hex_codes(rr, gg, bb )
        
        return rr, gg, bb

    
    def replace_cmap( self,filename, reverse=False, invert=False ):
        """
        This utility routine can be used to change the color map of 
        and existing series plot.
        
        >>> lut.replace_cmap( "/soft/ciao/data/bb.lut")

        As with the init routine, the color map can be 
        auto-located, reversed, or inverted.

        >>> lut.replace_cmap("16_colors")
        >>> lut.replace_cmap("heart", invert=True )
        >>> lut.replace_cmap("standard", reverse=True )
        
        The color map that is loaded must have the same number of
        colors as the original or an exception is raised.

        """
        
        open_undo_block()
        self._set_lut_window()  # save current window/frame/plot info

        if not self.curves:
            close_undo_block()
            raise RuntimeError("You can only replace a color map after it has been plotted")

        # consistency check that #colors == #curves
        assert len(self.hex_codes) == len( self.curves)

        rr,gg,bb = self._get_rgb( filename, reverse=reverse, invert=invert )

        if len(rr) != self.num_colors:
            self._restore_window()
            close_undo_block()
            raise IOError("New lookup table must have same number of colors as previous table")

        self.filename = filename

        load_colormap( rr, gg, bb, self.cmap )
        
        if self.image:
            set_image(self.image, "colormap={}".format(self.cmap))

        nn = self.num_colors
        for ii in xrange(nn) :
            # Construct the color hex value
            mycol = self._get_color_code( ii) 
            if self.curves[ii]:
                set_curve( self.curves[ii], "line.color={0} symbol.color={0}".format(mycol))        

        self._restore_window()
        close_undo_block()


    def _get_current_object_name( self, name ):
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


    def _save_limits( self ):
        # We want to save the current axis limits; they get reset when
        # we add an image to the same frame.
        ax = self._get_current_object_name("X Axis")
        ay = self._get_current_object_name("Y Axis")    
        self.axis_names = [ ax, ay ] 
        self.rx = get_axis_range( ax )
        self.ry = get_axis_range( ay )


    def _restore_limits(self):
        # restore limits        
        limits(  X_AXIS, self.rx[0], self.rx[1] )
        limits(  Y_AXIS, self.ry[0], self.ry[1] )

    def _get_window_info(self):
        """
        """
        win = self._get_current_object_name("Window") 
        frame = self._get_current_object_name("Frame") 
        plot = self._get_current_object_name("Plot") 
        return (win, frame, plot)


    def _set_lut_window(self):
        """
        """        
        (self.old_win,self.old_frame,self.old_plot) = self._get_window_info()
        set_current_window( self.lut_win )
        set_current_frame( self.lut_frame)
        set_current_plot( self.lut_plot)


    def _restore_window(self):
        """
        """
        set_current_window( self.old_win)
        set_current_frame(self.old_frame)
        set_current_plot(self.old_plot)

    
    def plot( self, xx, yy, zz, name="lutpoint", zgrid=None ):
        """
        Plots the X, Y for each Z slice color coded by the LUT
    
        >>> x = np.random.rand(100)
        >>> y = np.random.rand(100)
        >>> z = np.arange(100)
        >>> lut.plot( x, y, z )

        The ZZ values are split into an equal number of bins going from
        min(zz) to max(zz).  The number of bins is equal to the 
        number of colors in LUT.  The zgrid can be
        explicitly input but must have the same number of grid
        points as the number of colors

        >>> zlo = np.arange(256)
        >>> zhi = zlo + 1
        >>> zlo[0] = -999
        >>> zhi[-1] = 999
        >>> zgrid = zip(zlo,zhi)
        >>> plot(x, y, z, zgrid=zgrid)
                
        Note:  The color bar tick labels will not correctly 
        show the arbitrary zgrid values.


        A curve is created for each color.  All the curves have 
        a name that starts with the prefix "lutpoint" which can
        be changed using the 'name' argument.

        >>> plot(x, y, z, name="asoldata")
        >>> info()
           ...
              Curve [asoldata1]


        """    
        if self.curves:
            raise RuntimeError("The same object cannot be used to plot multiple series")
            
        # All commands in the routine are undone with a single undo()
        open_undo_block()

        nn = self.num_colors
        if not zgrid:
            # Determine the Z bins to plot; use linear/fixed bin widths
            self.min_z = min(zz)
            self.max_z = max(zz)    
            dt = float(self.max_z - self.min_z)/(nn-1)
            tlo = self.min_z + dt* np.arange(nn)
            thi = tlo  + dt
            thi[-1] = np.inf  # make sure max value is always included (< vs <= below)
        else:
            # check zgrid to make sure is OK
            if len(zgrid) != self.num_colors:
                close_undo_block()
                raise ValueError("zgrid must have same number of elements as number of colors")
            
            if not all( [len(zgrid[i]) == 2 for i in xrange(nn)] ):
                close_undo_block()
                raise ValueError("zgrid must have 2 elements in each slot")

            try:
                tlo = np.array( [float(zgrid[i][0]) for i in xrange(nn) ])
                thi = np.array( [float(zgrid[i][1]) for i in xrange(nn) ])
                self.min_z = tlo[0]
                self.max_z = thi[-1]
            except:
                close_undo_block()
                raise ValueError("All elements of zgrid must be numbers")
        
        #We add a curve w/ no line/symbol just to get axes setup
        add_curve( xx, yy, "symbol.style=none line.style=none stem=delme")
        self._save_limits()
        delname = self._get_current_object_name("Curve")

        self.lut_win, self.lut_frame,self.lut_plot = self._get_window_info()

        all_curves = []    
        for ii in xrange(nn) :
            # Construct the color hex value
            mycol = self._get_color_code( ii )

            # filter data in i-th range
            jj, = np.where( (zz >= tlo[ii]) & (zz < thi[ii]))
            if len(jj) == 0:
                all_curves.append(None)
                continue            
            add_curve( np.array(xx)[jj], np.array(yy)[jj], 
                """stem={0} line.style=none symbol.style=point 
                symbol.color={1} line.color={1}""".format(name,mycol))
            all_curves.append( self._get_current_object_name("Curve") )
    
        # save list of curves plotted
        self.curves = all_curves 
        self.order = 1  # 1st color plotted on bottom

        # delete initial curve used to setup axes
        delete_curve(delname)

        close_undo_block()


    def set_curve( self, args ):
        """
        Loop thru curves appling the style to each

        >>> lut.set_curve("symbol.style=circle")
        >>> lut.set_curve( ["symbol.size", "3"] )
        >>> lut.set_curve( { "symbol.fill" : True } )
        >>> cc = ChipsCurve()
        >>> cc.symbol.angle = 270
        >>> lut.set_curve(cc)

        Users should not set the color parameters.

        """        
        open_undo_block()
        self._set_lut_window()

        for cc in self.curves:
            if cc:
                set_curve(cc, args)

        self._restore_window()        
        close_undo_block()


    def shuffle( self ):
        """
        Shuffle the curves so that 1st is last
        
        >>> lut.shuffle()

        """
        
        cc = map(None, self.curves)
        cc.reverse()

        if 1 == self.order :
            dd = chips_back
            self.order=-1
        else:
            dd = chips_front
            self.order=1
        
        for cc in self.curves:
            shuffle_curve(cc, dd)


        
    def add_colorbar( self ):
        """
        We now want to add a color bar to describe the Z axis.  What we do is add
        an 2x2 image with values set to min/max of the Z axis (or
        in our case offsets); hide the image, and then create the colorbar

        Example:
        
        >>> lut.add_colorbar()        
        
        """    

        if self.image:
            raise RuntimeError("Cannot set multiple colorbars")


        open_undo_block()
        self._set_lut_window()
        self._save_limits()
            
        # We set alpha to all 0 so we don't get an image flahsed on screen
        tmin = self.min_z if self.min_z else 0
        tmax = self.max_z if self.max_z else 1
        cmap = self.cmap if self.cmap else chips_usercmap1
        add_image( tmin+np.arange(4)*((tmax-tmin)/3.0),2,2,
            "colormap={0} alpha=[0,0]".format(cmap))


        # save the image name incase we want to change colormap
        self.image = self._get_current_object_name("Image") 
        set_data_aspect_ratio('')
        hide_image()

        # then we reset alphas back to 1 so colorbar matches plotted data
        set_image("alpha=[1,1]")
    
        add_colorbar(1.075,0.5, """orientation=vertical
                    ticklabel.angle=90
                    ticklabel.halign=center
                    label.angle=180
                    label.valign=base
                    stem=lutcolorbar"""
                )

        self._restore_limits()
        self._restore_window()
        
        close_undo_block()
    


def __test():
    """
    Commands to test above commands
    
    """
    #tab = read_file("/export/byobsid/15403/primary/pcadf479143901N001_asol1.fits")
    tab  = read_file("/lenin2.real/Test/Merge/repro/pcadf474115095N001_asol1.fits")
    x = tab.get_column("dy").values
    y = tab.get_column("dz").values
    z = tab.get_column("time").values
    z= (z-min(z))/1000.0 # offset and convert to ksec
    from paramio import pget 
    lut = LUTPlot( pget("imagej_lut", "16_equal"), cmap=chips_usercmap2)
    clear()
    lut.plot( x,y,z)
        
    lut.add_colorbar( )

    lut.set_curve( "symbol.style=circle")
    lut.set_curve( { 'symbol.size' : 2 } )
    
    lut.replace_cmap( pget("imagej_lut", "005-random"))
    lut.shuffle()
    


