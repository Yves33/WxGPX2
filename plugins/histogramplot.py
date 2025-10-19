#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

## system imports
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib.cm as cm
import numpy as np
import ast
import wx

import msgwrap
from wxquery import WxQuery
from flexpanzoom import PanZoomFactory

class HistogramPlotPlugin(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.MapPanel = kwargs.pop('MapPanel', None)
        self.TimePanel = kwargs.pop('TimePanel', None)
        self.cfg = kwargs.pop('cfg', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.gpx=None
        self.xsrc='speed'
        self.color='#0000FF'
        self.bins=20
        self.lo,self.hi=None,None
        self.grid=True
        self.kwargs={}

        self.gpxfig = Figure() ## the trick is to create a figure large enough at the beginning
        self.ax = self.gpxfig.add_subplot(111)
        self.gpxcanvas=FigureCanvas(self,-1,self.gpxfig)
        self.pz=PanZoomFactory(self.gpxfig, clip=(0.0,0.0))
        # canvas and events
        #self.gpxcanvas.mpl_connect('draw_event', self.OnDraw)
        #self.gpxcanvas.mpl_connect('scroll_event', self.OnMouseWheel)
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
        if not self.gpx is None and self.xsrc in self.gpx.columns:
            xdata=self.gpx[self.xsrc].unit.scaled[self.gpx.ok]
            self.lo=min(xdata) if self.lo==None else self.lo
            self.hi=max(xdata) if self.hi==None else self.hi
            hist, bins = np.histogram(xdata,self.bins)
            width = 0.7 * (bins[1] - bins[0])
            center = (bins[:-1] + bins[1:]) / 2
            self.ax.cla()
            self.ax.bar(center, hist, width=width,**self.kwargs,color=self.color)
            #self.ax.set_xlabel(self.xsrc+' ('+self.gpx[self.xsrc].unit.sym+')')
            self.ax.set_xlabel(self.gpx[self.xsrc].unit.legend)
            self.ax.set_ylabel('Occurence')
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
        self.xsrc='speed'

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
        dummy,self.xsrc,self.color,self.bins,extra)=\
            WxQuery("Graph Settings",\
                [('wxnotebook','Axes',None,None,None),
                 ('wxcheck','Show Grid',None,self.grid,'bool'),
                 ('wxnotebook','Histogram',None,None,None),
                 ('wxcombo','X','|'.join(self.gpx.columns),self.xsrc,'str'),
                 ('wxcolor','Color',None,self.color,'str'),
                 ('wxhscale','Bins','10|50|1|1',self.bins,'int'),
                 ('wxentry','Extra arguments',None,'{}','str')
                ])
        self.kwargs.update(ast.literal_eval(extra))
        self.Plot()

    def OnMouseWheel(self,event):
        pass

    def OnLeftMouseUp(self,event):
        pass

    def OnMouseMotion(self,event):
        pass

    def OnMouseEnter(self,event):
        pass

    def OnMouseLeave(self,event):
        pass

class Plugin(HistogramPlotPlugin):
    def __init__(self, *args, **kwargs):
       HistogramPlotPlugin.__init__(self, *args, **kwargs)

    def GetName(self):
        return "Histogram"
