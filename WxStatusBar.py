#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import wx
import wx.aui
import wx.adv
from wxquery import WxQuery

class StatusBarPanel(wx.StatusBar):
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent)
        self.SetFieldsCount(1)
        self.SetStatusWidths([-1])
        self.SetStatusText("")
        self.Bind(wx.EVT_LEFT_DCLICK,self.OnLeftDoubleClick)
        self.statusstring=f"Index %idx% | Speed (kts): %speed%"
        self.replacelist=[]
        
    def OnIndexChanged(self, emitter,idx):
        if emitter!=self:
            s=self.statusstring
            for k in self.replacelist:
                s=s.replace(f"%{k}%",str(self.gpx[k].unit.scaled[idx]))
            self.SetStatusText(s, 0)

    def OnSelectionChanged(self,emitter):
        if emitter!=self:
            pass

    def OnDataChanged(self,emitter):
        if emitter!=self:
            pass
    
    def OnLeftDoubleClick(self,event):
        self.statusstring,=WxQuery("Enter text to display",
            [('wxentry','Text to display in status bar',None,self.statusstring,'str')
            ] )
        self.replacelist=[s for s in self.statusstring.split('%') if s in self.gpx.columns]
        
    def AttachGpx(self,gpx):
        self.gpx=gpx
        self.replacelist=[s for s in self.statusstring.split('%') if s in self.gpx.columns]
        self.OnIndexChanged(None,0)

    def DetachGpx(self):
        self.gpx=None
        self.SetStatusText("",0)
