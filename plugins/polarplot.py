#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

## system imports
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.colors import LinearSegmentedColormap
import colorsys
import numpy as np
import pandas as pd
import ast
import wx

import msgwrap
from wxquery import WxQuery
from flexpanzoom import PanZoomFactory

class PolarPlotPlugin(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.MapPanel = kwargs.pop('MapPanel', None)
        self.TimePanel = kwargs.pop('TimePanel', None)
        self.cfg = kwargs.pop('cfg', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.gpx=None
        self.thetasrc='heading'
        self.radiussrc='speed'
        self.dotsize=5
        self.autoscale=True
        self.grid=True
        self.convert=True
        self.cmap=LinearSegmentedColormap.from_list('hsv',colors=[colorsys.hsv_to_rgb(h,1.0,1.0) for h in np.linspace(0.666,0,255)])
        self.enveloppe=''
        self.binsize=5
        self.linewidth=2
        self.linecolor=(1.0,0.0,0.0)

        self.gpxfig = Figure() ## the trick is to create a figure large enough at the beginning
        self.ax = self.gpxfig.add_subplot(111,polar=True)
        self.gpxcanvas=FigureCanvas(self,-1,self.gpxfig)
        self.pz=PanZoomFactory(self.gpxfig, clip=(0.0,0.0))
        # canvas and events
        #self.gpxcanvas.mpl_connect('draw_event', self.OnDraw)
        self.gpxcanvas.mpl_connect('scroll_event', self.OnMouseWheel)
        self.gpxcanvas.mpl_connect('button_press_event', self.OnLeftMouseDown)
        #self.gpxcanvas.mpl_connect('button_release_event', self.OnLeftMouseUp)
        #self.gpxcanvas.mpl_connect('motion_notify_event', self.OnMouseMotion)
        #self.gpxcanvas.mpl_connect('resize_event', self.OnSize)
        #self.gpxcanvas.mpl_connect('figure_enter_event', self.OnMouseEnter)
        #self.gpxcanvas.mpl_connect('figure_leave_event', self.OnMouseLeave)
        self.Bind(wx.EVT_SIZE,self.OnSize)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.gpxcanvas, -1, wx.LEFT|wx.TOP|wx.EXPAND)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

        msgwrap.register(self.OnIndexChanged, "INDEX_CHANGED")
        msgwrap.register(self.OnSelectionChanged, "SELECTION_CHANGED")
        msgwrap.register(self.OnDataChanged, "DATA_CHANGED")
        
        #that code does not work on linux...
        #color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)
        self.gpxfig.set_facecolor((1.0, 1.0, 1.0))
        self.gpxfig.set_edgecolor((1.0, 1.0, 1.0))
        self.gpxcanvas.SetBackgroundColour((1.0,1.0,1.0))
        self.gpxfig.set_facecolor((1.0, 1.0, 1.0))
        self.OnSize(self.GetSize())


    def Plot(self):
        self.ax.cla()
        if not self.gpx is None and \
            self.thetasrc in self.gpx.columns and \
            self.radiussrc in self.gpx.columns:
            scale=np.pi/180 if self.convert else 1
            self.ax.scatter(self.gpx[self.thetasrc][self.gpx.ok]*scale,
                            self.gpx[self.radiussrc][self.gpx.ok].unit.scaled,
                            c=self.gpx[self.radiussrc][self.gpx.ok],
                            marker='o',
                            s=self.dotsize,
                            cmap=self.cmap
                            )
        
            #if self.enveloppe in ['mean','median','10% highest']:
            if self.enveloppe!='':
                theta=pd.Series([t*scale for t in range(0,359,self.binsize)])
                data=[self.gpx[self.radiussrc][(self.gpx.ok) & 
                                                (deg<=self.gpx[self.thetasrc]) & 
                                                (self.gpx[self.thetasrc]<deg+self.binsize)].unit.scaled
                             for deg in range(0,359,self.binsize)]
                if 'max' in self.enveloppe:
                    radius=pd.Series([np.nanmax(d) if len(d) else np.nan for d in data])
                    self.ax.plot(theta[radius.notna()],
                                 radius[radius.notna()],
                                 linewidth=self.linewidth,color=self.linecolor)
                if 'mean' in self.enveloppe:
                    radius=pd.Series([np.nanmean(d) if len(d) else np.nan for d in data])
                    self.ax.plot(theta[radius.notna()],
                                 radius[radius.notna()],
                                 linewidth=self.linewidth,color=self.linecolor)
                if 'median' in self.enveloppe:
                    radius=pd.Series([np.nanmedian(d) if len(d) else np.nan for d in data])
                    self.ax.plot(theta[radius.notna()],
                                 radius[radius.notna()],
                                 linewidth=self.linewidth,color=self.linecolor)
                if '10% highest' in self.enveloppe:
                    radius=pd.Series([np.nanpercentile(d,90) if len(d) else np.nan for d in data])
                    self.ax.plot(theta[radius.notna()],
                                 radius[radius.notna()],
                                 linewidth=self.linewidth,color=self.linecolor)

        self.ax.set_theta_zero_location("N")
        self.ax.set_theta_direction(-1)
        self.ax.grid(self.grid)
        #self.gpxfig.subplots_adjust(right=0.9,left=0.1,top=0.9,bottom=0.1)
        self.gpxfig.tight_layout()
        self.gpxcanvas.draw()

    def AttachGpx(self,data):
        self.gpx=data
        self.idx=0
        self.Plot()

    def DetachGpx(self):
        self.gpx=None
        self.thetasrc='heading'
        self.radiussrc='speed'

    def OnSelectionChanged(self,emitter):
        if emitter!=self:
             self.Plot()

    def OnDataChanged(self,emitter):
        if emitter!=self:
            self.Plot()

    def OnIndexChanged(self, emitter,idx):
        if emitter!=self:
            pass

    def OnDraw(self,event):
        pass
        
    def OnSize(self,event):
        x,y=self.GetClientSize() ## event.Size()
        if x*y==0:  ## on application startup, we will receive a bunch of size events which we should ignore
            return
        #self.gpxcanvas.resize(x,y)
        self.gpxcanvas.SetSize(*self.GetClientSize())
        self.gpxfig.set_size_inches(float(x)/self.gpxfig.get_dpi(),float(y)/self.gpxfig.get_dpi())
        self.Plot()

    def OnLeftMouseDown(self,event):
        if event.button==1:
            if event.dblclick:
                try:
                    event.guiEvent.GetEventObject().ReleaseMouse()
                except:
                    pass
                self.OnLeftMouseDblClick(event)

    def OnLeftMouseDblClick(self,event):
        (dummy,self.grid,\
        dummy,self.thetasrc,self.radiussrc,self.dotsize,self.enveloppe,self.binsize,self.linewidth,self.linecolor,self.convert)=\
            WxQuery("Graph Settings",\
                [('wxnotebook','Axes',None,None,None),
                 ('wxcheck','Show Grid',None,self.grid,'bool'),
                 ('wxnotebook','Polar plot',None,None,None),
                 ('wxcombo','Theta','|'.join(self.gpx.columns),self.thetasrc,'str'),
                 ('wxcombo','Radius','|'.join(self.gpx.columns),self.radiussrc,'str'),
                 ('wxentry','Dot size',None,self.dotsize,'float'),
                 #('wxcombo','Enveloppe','None|max|mean|median|10% highest',self.enveloppe,'str'),
                 ('wxchecklist','Enveloppe','max|mean|median|10% highest',self.enveloppe,'str'),     #typ_=str. you can also provide the indexes that should be checked by default
                 ('wxhscale','Bin size (deg)','1|30|1|5',self.binsize,'int'),
                 ('wxentry','Line width',None,self.linewidth,'float'),
                 ('wxcolor','Line Color',None,self.linecolor,'float'),
                 ('wxcheck','Convert to radians',None,self.convert,'bool')
                ])
        self.Plot()

    def OnMouseWheel(self,event):
        scale_factor = 1.2 if event.button=='down' else (1.0/1.2)
        rmin,rmax=self.ax.get_ylim()
        self.ax.set_ylim(rmin*scale_factor, rmax*scale_factor)
        self.gpxcanvas.draw()

    def OnLeftMouseUp(self,event):
        pass

    def OnMouseMotion(self,event):
        pass

    def OnMouseEnter(self,event):
        pass

    def OnMouseLeave(self,event):
        pass

class Plugin(PolarPlotPlugin):
    def __init__(self, *args, **kwargs):
       PolarPlotPlugin.__init__(self, *args, **kwargs)

    def GetName(self):
        return "Polar"
