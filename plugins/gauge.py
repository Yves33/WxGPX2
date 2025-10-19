#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

## system imports
from matplotlib.ticker import MaxNLocator
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle,Polygon,Circle,CirclePolygon
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import numpy as np
import wx
import colorsys

import msgwrap
from wxquery import WxQuery

DEG2RAD=np.pi/180
RAD2DEG=180/np.pi

'''
@dataclass
class aes: controls the aesthetics of our Gauge
    frame_offset=0.1
    frame_height=0.5
    frame_bottom=2.0
    frame_linewidth=0
    frame_edgecolor="#BBBBBB"
    frame_color=["#BBBBBB"]
    frame_align="edge"  

    bar_height=0.3 
    bar_bottom=2.0
    bar_linewidth=3.0
    bar_edgecolor="#FFFFFF"
    bar_align='edge'

    lbl_offset=2.5
    lbl_rotate=True
    lbl_fontsize=12
    lbl_fontweight="bold"
    
    needle_centerradius=0.3
    needle_color="#000000"
    needle_width=0.01
    needle_length=1.8
    gauge_start=(0,1.8)
    gauge_height=0.2
    gauge_color="#FF0000"
    gauge_edgecolor="#FFFFFF"
'''

class mplgauge:
    def __init__(self,value,
                 mini=0,
                 maxi=100,
                 theta0=270/180*np.pi,theta1=0.0,
                 c0=0.35,
                 c1=0.0,
                 segments=8,
                 annotations=["0","25","50","75","100"],
                 needle=True,
                 progress=True,
                 ax=None,
                 fmtstring="{:.03f}",
                 direction=-1
         ):
        
        self.needle=needle
        self.progress=progress
        self.fmtstring=fmtstring
        self.mini,self.maxi=mini,maxi
        self.ax=ax
        self.thetaspan=theta0-theta1
        self.origin=theta0
       
        self.patches=[]

        colors=[colorsys.hsv_to_rgb(h,1.0,1.0) for h in np.linspace(c0,c1,segments)]
        xvalues=np.linspace(0,self.thetaspan,segments+1)
        wvalues=(np.ediff1d(xvalues))
        if not ax:
            fig=Figure()
            ax = fig.add_subplot(projection="polar")

        ## set origin and rotate counter-clockwise
        ax.set_theta_offset(self.origin)
        ax.set_theta_direction(direction)
        
        ## plot frame
        ax.bar(0-0.1,                    ## ->frame_offset
            width=self.thetaspan+2*0.1,  ##
            height=0.8,                  ## ->frame_height
            bottom=2.0,                  ## ->frame_bottom
            linewidth=0,                 ## ->frame_ecolor
            edgecolor="#BBBBBB",         ## ->frame_edgecolor
            color=["#BBBBBB"],           ## ->frame_color
            align="edge"                # # ->frame_align
            )
        ## colored gauge
        ax.bar(x=xvalues[:-1],           ## controls the start/ of each slice
            width=wvalues,               ## controls the width or each slice
            height=0.4,                  ## ->bar_height 
            bottom=2.0,                  ## ->bar_bottom
            linewidth=3,                 ## ->bar_linewidth
            edgecolor="white",           ## ->bar_edgecolor
            color=colors,
            align="edge"                 ## ->bar_align
            )
        ## annotations
        for loc, val in zip(np.linspace(0,self.thetaspan,len(annotations)), annotations):
            ax.text(loc,
                    3.2,                                    ##->lbl_offset
                    str(val),
                    rotation=-90+(self.origin-loc)*RAD2DEG, ##->lbl_rotate 0,1
                    fontsize=12,                            ##->lbl_fontsize
                    fontweight="bold",                      ##->lbl_fontweight
                    ha="center",va='center',
                    clip_on=False) 

        ax.set_axis_off()
        ax.set_rmin(0)
        ax.set_rorigin(0)
        self.circlepatch=self.ax.add_patch(Polygon(np.array([[2*r/np.pi,0.3] for r in range(40)]), ## ->needle_centerraius
                                                   color='k',                                      ## ->needle_color
                                                   closed=True))
        ## prepare needle, gauge and text, but let them invisible
        self.needlepatch,self.textpatch, self.gaugepatch=None,None,None
        if self.needle:
            self.needlepatch=self.ax.add_patch(Polygon([(1.57,0.01),(-1.57,0.01),(0,1.8)],         ## ->needle_width,needle_length
                                                   color='k',                                      ## ->needle_color
                                                   closed=True))
        if self.fmtstring!='':
            self.textpatch=self.ax.text(-np.pi*3/2+self.origin, 1.5, "test", fontsize=12)
        if self.progress:
            self.gaugepatch=self.ax.add_patch(Rectangle((0,1.8),                                   ## ->gauge_start
                                          height=0.01,                                              ## ->gauge_height
                                          width=self.thetaspan*0,
                                          color='#FF0000',                                         ##->gauge_color
                                          edgecolor="white"                                        ##->gauge_edgecolor
                                          ))
        self.showhide(False)

    def showhide(self,show):
        self.needlepatch.set_visible(show)
        self.gaugepatch.set_visible(show)
        self.textpatch.set_visible(show)
        
    def update(self,value):
        scaledvalue=(value-self.mini)/(self.maxi-self.mini)
        a=self.thetaspan*scaledvalue
        if not self.needlepatch is None:
            self.needlepatch.set(xy=np.array([[a-1.57,0.2],[a+1.57,0.2],[a,1.8]]))
            self.ax.draw_artist(self.needlepatch)
        if not self.textpatch is None:
            self.textpatch.set_text(self.fmtstring.format(value))
            self.ax.draw_artist(self.textpatch)
        if not self.gaugepatch is None:
            self.gaugepatch.set_width(self.thetaspan*scaledvalue)
            self.ax.draw_artist(self.gaugepatch)

class GaugePlugin(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.MapPanel = kwargs.pop('MapPanel', None)
        self.TimePanel = kwargs.pop('TimePanel', None)
        self.cfg = kwargs.pop('cfg', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.gpx=None
        self.idx=0
        self.xsrc='speed'
        self.startangle=220
        self.stopangle=0
        self.segments=8
        self.labels='0%|50%|100%'
        self.mini=0
        self.maxi=0
        self.auto=True
        self.gauge=None

        self.gpxfig = Figure() ## the trick is to create a figure large enough at the beginning
        self.ax = self.gpxfig.add_subplot(projection="polar")
        self.gpxcanvas=FigureCanvas(self,-1,self.gpxfig)
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
        if self.gauge is None:
            self.ax.cla()
            if not self.gpx is None and self.xsrc in self.gpx.columns:
                if self.mini==self.maxi:
                    self.auto=True
                if self.auto:
                    ticks=MaxNLocator(nbins=6).tick_values(self.gpx[self.xsrc].unit.scaled.min(),
                                                                    self.gpx[self.xsrc].unit.scaled.max())
                    self.mini=ticks[0]
                    self.maxi=ticks[-1]
                    self.segments=len(ticks)-1
                    self.labels='|'.join([str(x) for x in ticks])
                self.gauge=mplgauge(value=0,
                    mini=self.mini,
                    maxi=self.maxi,
                    theta0=self.startangle*DEG2RAD,
                    theta1=self.stopangle*DEG2RAD,
                    segments=self.segments,
                    annotations=self.labels.split('|'),
                    c0=0.666,
                    c1=0.0,
                    fmtstring="{:.03f} "+f"{self.gpx[self.xsrc].unit.sym}",
                    ax=self.ax)
                self.gpxfig.subplots_adjust(right=0.8,left=0.2,top=0.8,bottom=0.2)
                self.gpxcanvas.draw()
                self.background = self.gpxcanvas.copy_from_bbox(self.ax.bbox)
                self.gauge.showhide(True)
        else:
            self.gpxcanvas.restore_region(self.background)
            self.gauge.update(self.gpx[self.xsrc].unit.scaled[self.idx])
            self.gpxcanvas.blit(self.ax.bbox)
            #self.gpxcanvas.draw()

    def AttachGpx(self,data):
        self.gpx=data
        self.idx=0
        self.gauge=None
        self.Plot()

    def DetachGpx(self):
        self.gpx=None
        self.gauge=None

    def OnSelectionChanged(self,emitter):
        if emitter!=self:
            self.gauge=None
            self.Plot()

    def OnDataChanged(self,emitter):
        if emitter!=self:
            self.idx=0
            self.gauge=None
            self.Plot()

    def OnIndexChanged(self, emitter,idx):
        if emitter!=self:
            self.idx=idx
            self.Plot()

    def OnDraw(self,event):
        pass
        
    def OnSize(self,event):
        x,y=self.GetClientSize() ## event.Size()
        if x*y==0:  ## on application startup, we will receive a bunch of size events which we should ignore
            return
        #self.gpxcanvas.resize(x,y)
        self.gpxcanvas.SetSize(*self.GetClientSize())
        self.gpxfig.set_size_inches(float(x)/self.gpxfig.get_dpi(),float(y)/self.gpxfig.get_dpi())
        if self.gauge:
            self.gauge.showhide(False)
            self.gpxcanvas.draw()
            self.background = self.gpxcanvas.copy_from_bbox(self.ax.bbox)
            self.gauge.showhide(True)

    def OnLeftMouseDown(self,event):
        if event.button==1:
            if event.dblclick:
                try:
                    event.guiEvent.GetEventObject().ReleaseMouse()
                except:
                    pass
                self.OnLeftMouseDblClick(event)

    def OnLeftMouseDblClick(self,event):
        (dummy,self.xsrc,\
         self.startangle,self.stopangle,self.segments,\
         self.mini,self.maxi,self.labels,self.auto)=\
            WxQuery("Graph Settings",\
                [('wxnotebook','Gauge',None,None,None),
                 ('wxcombo','Angle','|'.join(self.gpx.columns),self.xsrc,'str'),
                 ('wxentry','Start angle',None,self.startangle,'int'),
                 ('wxentry','Stop angle',None,self.stopangle,'int'),
                 ('wxspin','Segments','1|256|1',self.segments,'int'),
                 ('wxentry','Mini',None,self.mini,'float'),
                 ('wxentry','Maxi',None,self.maxi,'float'),
                 ('wxentry','Labels',None,self.labels,'str'),
                 ('wxcheck','Autoscale',None,self.auto,'bool')
                ])
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

class Plugin(GaugePlugin):
    def __init__(self, *args, **kwargs):
       GaugePlugin.__init__(self, *args, **kwargs)

    def GetName(self):
        return "Gauge"
