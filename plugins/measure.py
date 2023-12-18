#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-#

import wx
import numpy as np
import msgwrap

class MeasurePlugin(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.MapPanel = kwargs.pop('MapPanel', None)
        self.TimePanel = kwargs.pop('TimePanel', None)
        self.cfg = kwargs.pop('cfg', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.gpx=None
        self.theta=[]
        self.xy=[]
        ##
        self.text=wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY,size=(-1,1200))
        self.text.SetEditable(False)
        self.text.SetValue("\n"*125)
        self.Plot()
        ## add an event handler to map, so thta we get warned when  there's been a click in map
        self.MapPanel.Bind(wx.EVT_LEFT_DOWN,self.OnMouseDown)
        self.MapPanel.Bind(wx.EVT_RIGHT_DOWN,self.OnMouseDown)
        #self.Bind(wx.EVT_SIZE,self.OnSize)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.text,0,wx.EXPAND)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

        msgwrap.register(self.OnIndexChanged, "INDEX_CHANGED")
        msgwrap.register(self.OnSelectionChanged, "SELECTION_CHANGED")
        msgwrap.register(self.OnDataChanged, "DATA_CHANGED")
        
        self.OnSize(self.GetSize())


    def Plot(self):
        ## compute all distances and headings
        layer=self.MapPanel.map.layers['measure']
        self.xy=[]
        self.theta=[]
        if len(layer.lat)>1:
            for e in range(len(layer.lat)-1):
                from pilmap import Haversine
                d,c=Haversine(layer.lat[e],layer.lon[e],layer.lat[e+1],layer.lon[e+1])
                self.xy.append(d)
                self.theta.append(c)
        ## build text buffer
        buffer=''
        buffer+='Map:\n'
        buffer+='====\n'
        buffer+=f'Map width: {self.MapPanel.map.width*self.MapPanel.map.pixelscale:.02f} m\n'
        buffer+=f'Map height: {self.MapPanel.map.height*self.MapPanel.map.pixelscale:.02f} m\n\n'
        buffer+='Path:\n'
        buffer+='=====\n'
        buffer+=f'Total length: {np.sum(self.xy):.02f} m\n\n'
        for e,(xy,theta) in enumerate(zip(self.xy,self.theta)):
            buffer+=f'+ Segment {e+1}: distance {xy:.02f} m  heading :{theta:.02f} deg\n'
        self.text.SetValue(buffer)

    def AttachGpx(self,data):
        pass

    def DetachGpx(self):
        self.gpx=None

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
        pass

    def OnMouseDown(self,event):
        ## we canot control callback order. this callback may be called before the map layers handle the mouse click
        ## the solution is to use wx.CallAfter
        wx.CallAfter(self.Plot)
        event.Skip()
            

    def OnLeftMouseDblClick(self,event):
        pass

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

class Plugin(MeasurePlugin):
    def __init__(self, *args, **kwargs):
       MeasurePlugin.__init__(self, *args, **kwargs)

    def GetName(self):
        return "Measure"
