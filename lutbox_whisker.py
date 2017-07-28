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
from __future__ import absolute_import, print_function


"""
Create and manipulate a box-n-whisker style plot.


"""

import numpy as np
from pychips.advanced import open_undo_block, close_undo_block
from pychips import *
from pycrates import read_file, get_colvals
from .lutplot import LUTPlot


__all__ = ["BoxWhiskerPlot"]

class BoxWhiskerPlot(LUTPlot):
    """
    Create a box-and-whisker style plot.
    
    Box-and-whisker plots, also known as box plots or quartile plots,
    are a way to show scatter data that combine each individual
    data point into bins and plots the quartiles (25%, 50% [median],
    and 75%) as a pair of stack boxes.   The limits (min
    and max values) of the data in each bin are represented as a line --
    which resemble "whiskers". 
    
    The advantage is it allows users to see trends in the data 
    that can be obscured dense scatter plots with limited screen 
    resolution. 

    >>> xx = np.arange(1000)
    >>> yy = map( lambda x: np.random.uniform(0.0), xx)
    >>> b = BoxWhiskerPlot( xx, yy )
    >>> b.plot()
    
    This creates a dataset with 1000 data points, distributed
    uniformly around 0.5.  The plot that is created will be binned
    into 10 bins ( 0<=x<100, 100<=x<200, etc).  Data within
    those bins are then used to create the box and whisker plots.
    The number of bins can be changed
 
    >>> b.set_grid(nbin=20)
    
    Or the grid can be specified explicity
    
    >>> b.set_grid( grid=[(1,500), (500,750), (750,1000)])

    Rather than using quartiles, arbitrary quantiles can be used.
    Here the 33% and 67% quartiles are used.
    
    >>> b.plot(qlo=0.33, qhi=0.67)

    The limits and mean can also be enable/disabled.
    
    >>> b.plot(limit=False, mean=False)

    The properties of the plot elements can be controlled using the
    set routines

    >>> b.set_region( "*.color=red")
    >>> b.set_line( ['thickness', '3.0' ])
    >>> b.set_point( { 'style' : 'square' } )
    
    The number of values in each of the grids can be color coded
    using the colorize method.  It takes the name of a
    color lookup table
    
    >>> b.colorize("/soft/ciao/data/bb.lut")

    The color bar can be set to different values an the plot will
    be updated.  You can specify the full path or if just the
    name it will try to locate the file in common CIAO dirs.

    After the data are color coded a color bar can be attached:
    
    >>> b.add_colorbar()

    Note:  There is currently a bug/feature that does not
    pick up on the region's transparency/opacity setting so
    the color bar may look different than the box plots.  
    By default regions are drawn at 70% opacity.    Making
    another call to colorize should get things updated correctly:
    
    >>> b.colorize("bb")
    >>> b.set_region( "opacity=0.3")
    >>> b.add_colorbar()
    >>> b.colorize("bb")
        
    """


    
    def __init__( self, xx, yy, curve=None, point=None, line=None, region=None, grid=None, nbin=10 ):
        """
        Create a BoxWhiskerPlot object
        
        Data in the X and Y arrays are copied.  Default grid
        and plot properties are setup.
        
        
        """
        if xx is None or yy is None:
            raise ValueError("X and Y must be specified (cannot contain None's")        
        if len(xx) != len(yy):
            raise ValueError("X and Y arrays must be same length")
        if len(xx) < 1:
            raise ValueError("Must have 1 or more value")
    
        if curve and not isinstance( curve, ChipsCurve ):
            raise ValueError("curve must be a ChipsCurve object")
        if point and not isinstance( symbol, ChipsPoint ):
            raise ValueError("point must be a ChipsSymbol object")
        if line and not isinstance( line, ChipsLine ):
            raise ValueError("line must be a ChipsLine object")
        if region and not isinstance(region, ChipsRegion ):
            raise ValueError("region must be a ChipsRegion object")
        
        self.xx = np.array(xx)
        self.yy = np.array(yy)
        self.curve = curve if curve else ChipsCurve()
        self.point = point if point else ChipsPoint()
        self.line = line if line else ChipsLine()
        self.region = region if region else ChipsRegion()
        self.grid = None
        self.y0 = None
        self.all_regions = None
        self.all_points = None
        self.all_lines = None
        self.all_curves = None
        self.lut_win = None
        self.lut_frame = None
        self.lut_plot = None
        self.qlo=None
        self.qhi=None
        self.limit=None
        self.mean=None
        self.sdev=None       
        self.set_grid( grid, nbin)

        self.image = None
        self.min_z = None
        self.max_z = None
        self.lut_win = None
        self.lut_frame = None
        self.lut_plot = None
        self.old_win = None
        self.old_frame = None
        self.old_plot = None
        self.order = None
        self.cmap = None


    def set_grid( self, grid=None, nbin=10 ):
        """
        Set the grid for the X-axis.
        
        The default is 10 equally spaced bins from the min to the max
        X value.
        
        The number of bins can be changed using the nbin parameter
        
        >>> b.set_grid(nbin=20)
        
        or an explicity grid can be supplied:
        
        >>> b.set_grid( grid=[ [1,500], [500,750], [750,1000] ] )
        
        The grid can overlap, have gaps, extend beyond and or not
        include the ends of the data.        
        """

        if None == grid:
            lo=np.min(self.xx)
            hi=np.max(self.xx)
            binwidth=(hi-lo+1)/nbin

            _lo = np.arange(nbin)*binwidth
            _hi = (1+np.arange(nbin))*binwidth
            grid = list(zip( _lo, _hi ))

        else:
            # just run some sanity checks
            for l,h in grid:
                if h < l:
                    raise ValueError("High grid value cannot be less than low")
        
        self.grid = grid
        self.y0 = dict(zip(self.grid, [None]*len(self.grid)))
        self._fill_grid()
        
        if self.lut_plot:
            self.plot( qlo=self.qlo, qhi=self.qhi, limit=self.limit, mean=self.mean, sdev=self.sdev )
        

    def _fill_grid( self ):
        """
        Save the Y values in each X bin.  Data are sorted so that
        that quartiles can be easily extracted.
        """        
        for g in self.grid:
            xlo = g[0]
            xhi = g[1]
            rng,=np.where( (self.xx>=xlo) & ( self.xx<xhi ))
            sz=rng.size
            if 0 == sz:
                continue
            self.y0[g] = self.yy[rng]
            self.y0[g].sort()
        
    def _restore_plot( self ):
        """
        Make sure the chips window/frame/plot are set before
        doing any changes.
        """     
        if self.lut_win and self.lut_frame and self.lut_plot:
            set_current_window( self.lut_win )
            set_current_frame( self.lut_frame )
            set_current_plot( self.lut_plot )

    def set_region( self, prop ):
        """
        Set region properties.  The same properties are applied to
        all the regions associated with this dataset.

        >>> b.set_region("*.color=red")
        >>> b.set_region(["fill.style", "userfill1"])
        >>> b.set_region( { 'edge.style' : 'none' })
        >>> r = ChipsRegion()
        >>> r.opacity = 1.0
        >>> b.set_region(r)        

        """
        open_undo_block()
        self._restore_plot()
        
        if self.all_regions:
            map( set_region, self.all_regions, [prop]*len(self.all_regions))
            self.region = get_region( self.all_regions[0] )
        else:
            self.region = prop
        
        close_undo_block()
        

    def set_line( self, prop ):
        """
        Set line properties.  The same properties are applied to
        all the lines associated with this dataset.
        
        Lines are used to show the "limit" (min to max).

        >>> b.set_line("color=red")
        >>> b.set_line(["style", "dot"])
        >>> b.set_line( { 'thickness' : '2' })
        >>> l = ChipsLine()
        >>> l.color = "FFFF00"
        >>> b.set_line(l)        
        
        """
        open_undo_block()
        self._restore_plot()
        
        if self.all_lines:
            map( set_line, self.all_lines, [prop]*len(self.all_lines))
            self.line = get_line( self.all_lines[0] )
        else:
            self.line = prop
        
        close_undo_block()


    def set_point( self, prop ):
        """
        Set point properties.  The same properties are applied to
        all the point associated with this dataset.
        
        Points are used to show the mean value.

        >>> b.set_point("color=red")
        >>> b.set_point(["style", "square"])
        >>> b.set_point( { 'size' : '4' })
        >>> p = ChipsPoint()
        >>> p.fill = False
        >>> b.set_point(p)        
        
        """
        open_undo_block()
        self._restore_plot()
        
        if self.all_points:
            map( set_point, self.all_points, [prop]*len(self.all_points))
            self.point = get_point( self.all_points[0] )
        else:
            self.point = prop
        
        close_undo_block()


    def set_curve( self, prop ):
        """
        Set point properties.  The same properties are applied to
        all the point associated with this dataset.
        
        Curves are used to show the standard deviation, sdev.
        The sdev is drawn as an "error", err. 

        >>> b.set_curve("err.color=red")
        >>> b.set_curve(["symbol.style", "square"])
        >>> b.set_curve( { 'symbol.size' : '4' })
        >>> p = ChipsCurve()
        >>> p.err.style = "cap"
        >>> b.set_curve(p)        
        
        """
        open_undo_block()
        self._restore_plot()
        
        if self.all_curves:
            map( set_curve, self.all_curves, [prop]*len(self.all_curves))
            self.curve = get_curve( self.all_curves[0])
        else:
            self.curve = prop
            
        close_undo_block()


                
    def plot( self, qlo=0.25, qhi=0.75,  limit=True, mean=True, sdev=False) :
        """        
        Box and whiskers plot
        
        The default is to plot the quartiles: data representing 
        the 25%, 50% (median), and 75% of the values in each
        X bin with a line through the mean showing the
        min and max values.

        >>> b.plot()
        
        The quantiles can be changed 
        
        >>> b.plot( qlo=0.33, qhi=0.67 )
        >>> b.plot( qlo=0.05, qhi=0.95 )
        
        The limit (min/max) line aka the whiskers can be disabled
        
        >>> b.plot( limit=False)
        
        and the mean value (point) can also be removed
        
        >>> b.plot( mean=False)
        
        
        """

        open_undo_block()

        try:
            self.clear()
        except:
            #Window may have been deleted/closed/etc.
            pass

        # setup axes
        add_curve( self.xx, self.yy, "stem=delme line.style=none symbol.style=none")
        delete_curve(self._get_current_object_name("Curve"))

        # save plot info
        self.lut_win = self._get_current_object_name("Window")
        self.lut_frame = self._get_current_object_name("Frame")
        self.lut_plot = self._get_current_object_name("Plot")

        self.all_regions = []
        self.all_points = []
        self.all_lines = []
        self.all_curves = []
    
        self.qlo = qlo
        self.qhi = qhi
        self.limit = limit
        self.mean = mean
        self.sdev = sdev
        
        self.grid_regions = {}
    
        for g in self.grid:
            xlo = g[0]
            xhi = g[1]
            y0 = self.y0[g]
            if y0 is None:
                continue
            sz = len(y0)
            if 0 == sz:
                continue
            
            # TODO move this into the fill grid method?  qlo and qhi
            # would need to move to different i/f
            q000=np.min(y0)
            q100=np.max(y0)
            q050=np.median(y0)
            qmid=np.mean(y0)
            qstd =np.std(y0)
            q033=y0[np.max([int(qlo*sz+0.5),0])]
            q066=y0[np.min([int(qhi*sz+0.5),sz-1])]
            xmid = (xhi+xlo)/2.0

            self.grid_regions[g] = []
        
            if q033 != q050:
                add_region( [xlo, xhi, xhi, xlo], [q033, q033, q050, q050], self.region )
                self.all_regions.append( self._get_current_object_name("Region"))
                self.grid_regions[g].append(self._get_current_object_name("Region"))

            if q050 != q066:
                add_region( [xlo, xhi, xhi, xlo], [q050, q050, q066, q066], self.region )
                self.all_regions.append( self._get_current_object_name("Region"))
                self.grid_regions[g].append(self._get_current_object_name("Region"))

            if True == mean:
                add_point( xmid, qmid, self.point )
                self.all_points.append(self._get_current_object_name("Point"))
            if True == limit:
                add_line( xmid, q000, xmid, q100 )
                self.all_lines.append(self._get_current_object_name("Line"))
            if True == sdev:
                add_curve( [xmid], [qmid], [qstd], self.curve )
                self.all_curves.append(self._get_current_object_name("Curve"))

        close_undo_block()

        
    def colorize( self,  filename, cmap=chips_usercmap1, reverse=False, invert=False ):
        """
        Color each histogram bin based on the number of values in the bin.
        

        The number of values in each of the grids can be color coded
        using the colorize method.  It takes the name of a
        color lookup table
        
        >>> b.colorize("/soft/ciao/data/bb.lut")

        The color bar can be set to different values an the plot will
        be updated.  You can specify the full path or if just the
        name it will try to locate the file in common CIAO dirs.

        After the data are color coded a color bar can be attached:
        
        >>> b.add_colorbar()

        Note:  There is currently a bug/feature that does not
        pick up on the region's transparency/opacity setting so
        the color bar may look different than the box plots.  
        By default regions are drawn at 70% opacity.    Making
        another call to colorize should get things updated correctly:
        
        >>> b.colorize("bb")
        >>> b.set_region( "opacity=0.3")
        >>> b.add_colorbar()
        >>> b.colorize("bb")

        """
        from ._utils import get_rgb_hexcodes, get_rgb_values


        if cmap not in [chips_usercmap1,chips_usercmap2,chips_usercmap3]:
            raise ValueError("Invalid color map selected")

        rr,gg,bb = get_rgb_values( filename, reverse=reverse, invert=invert )
        self.hex_codes = get_rgb_hexcodes( rr, gg, bb )
        load_colormap( rr,gg,bb, cmap )
        self.num_colors = len(self.hex_codes)
        self.filename = filename
        self.cmap = cmap

        counts = []
        for g in self.grid:
            y0 = self.y0[g]
            if y0 is None:
                continue
            sz = len(y0)
            if 0 == sz:
                continue
            counts.append( sz )
        cmin = float(min(counts))
        cmax = float(max(counts))
        dc = cmax - cmin

        self.min_z = cmin
        self.max_z = cmax
        
        
        for g in self.grid:
            y0 = self.y0[g]
            if y0 is None:
                continue
            sz = len(y0)
            if 0 == sz:
                continue
            
            nn = (sz-cmin)/(dc) if dc > 0 else 0.5
            ii = int(np.floor(self.num_colors * nn))
            ii = ii-1 if ii == self.num_colors else ii
            
            for rr in self.grid_regions[g]:
                set_region(rr, "*.color={}".format( self._get_color_code( ii) ))
        
        if self.image:
            al = get_region(self.all_regions[0]).opacity

            set_image(self.image, 'colormap={} alpha=[{}]'.format(self.cmap, al) )


        

    def clear(self):
        """
        clear all plot elements associated with this object, only.
        The plot is retained.
        
        >>> b.clear()
        
        """
        
        open_undo_block()
        
        self._restore_plot()
        if self.all_regions:
            map( delete_region, self.all_regions)
        if self.all_lines:
            map( delete_line, self.all_lines)
        if self.all_points:
            map( delete_point, self.all_points )
        if self.all_curves:
            map( delete_curve, self.all_curves )

        close_undo_block()

    @staticmethod
    def _get_current_object_name( name ):
        """
        We often need the chips name/id of the current object : curve, axis, etc.
        This can only be retrieved by parsing the info_current() command.
        """
        ii = info_current().split("\n")
        ff = [x for x in ii if name in x]
        ff = ff[-1] # last one
        name = ff.split("[")[1]
        name = name.split("]")[0]
        return name

def __test():
    
    xx = np.arange(1000)
    yy = map( lambda x: np.random.poisson(x/100.0), xx)
    clear()
    b = BoxWhiskerPlot( xx, yy )
    b.plot()

"""
xx = np.random.normal(5,size=10000)*10 # np.arange(10000)/1000.0
yy = map( lambda x: np.random.poisson(x), xx)
clear()

b = BoxWhiskerPlot( xx, yy )
b.plot()
b.colorize("neota_sword")
"""
