#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

## system imports
import os,sys,pathlib
import functools
import wx
from wx.py import shell

import msgwrap
from wxquery import WxQuery

class WxShell(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.MapPanel = kwargs.pop('MapPanel', None)
        self.TimePanel = kwargs.pop('TimePanel', None)
        self.cfg = kwargs.pop('cfg', None)
        wx.Panel.__init__(self, *args, **kwargs)
        sizer=wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.runbutton=wx.Button(self,0,"Run the script file below...")
        self.runbutton.Bind(wx.EVT_BUTTON, self.OnRunButtonClicked)
        sizer.Add(self.runbutton,0,wx.EXPAND)
        self.scriptcombo=wx.ComboBox(self,choices=['Browse file...'],value='Browse file...', style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.UpdateScripts, self.scriptcombo)
        sizer.Add(self.scriptcombo,0,wx.EXPAND)
        self.pyshell = shell.Shell(self, -1, introText='Python Shell')
        sizer.Add(self.pyshell,1,wx.EXPAND)
        self.gpx=None
        #standard events
        self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftMouseDown)
        self.Bind(wx.EVT_LEFT_UP,self.OnLeftMouseUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftMouseDblClick)
        self.Bind(wx.EVT_MOTION,self.OnMouseMotion)
        self.Bind(wx.EVT_ENTER_WINDOW,self.OnMouseEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW,self.OnMouseLeave)
        self.Bind(wx.EVT_RIGHT_DOWN,self.OnRightMouseDown)
        self.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        #self.Bind(wx.EVT_SIZE,self.OnSize)
        self.Bind(wx.EVT_ERASE_BACKGROUND,self.OnErase)
        #custom events
        msgwrap.register(self.OnIndexChanged, "INDEX_CHANGED")
        msgwrap.register(self.OnSelectionChanged, "SELECTION_CHANGED")
        msgwrap.register(self.OnDataChanged, "DATA_CHANGED")

        self.pyshell.interp.locals={}
        self.Link()

    def Link(self):
        self.pyshell.interp.locals['gpx']=self.gpx
        self.pyshell.interp.locals['mapview']=self.MapPanel
        self.pyshell.interp.locals['timeview']=self.TimePanel
        self.pyshell.interp.locals['app']=wx.GetApp()
        self.pyshell.interp.locals['sh']=self
        ## API to be reworked sync,synci,syncs, syncd==sync
        self.pyshell.interp.locals['msg']=functools.partial(msgwrap.message, emitter=self)
        self.pyshell.interp.locals['msgsel']=lambda :msgwrap.message("SELECTION_CHANGED", emitter=self)
        self.pyshell.interp.locals['msgdata']=lambda :msgwrap.message("DATA_CHANGED", emitter=self)
        self.pyshell.interp.locals['sync']=lambda :msgwrap.message("DATA_CHANGED", emitter=self)
        self.pyshell.interp.locals['msgidx']=lambda :msgwrap.message("INDEX_CHANGED", emitter=self)
        self.pyshell.interp.locals['appdir']=self.cfg['appdir']
        self.pyshell.interp.locals['scriptdir']=self.cfg['scriptdir']
        self.pyshell.interp.locals['plugindir']=self.cfg['plugindir']
        self.pyshell.interp.locals['query']=WxQuery
        self.pyshell.interp.locals['WxQuery']=WxQuery
        self.pyshell.interp.locals['selection']=self.TimePanel.get_selection
        self.pyshell.Execute('import numpy as np')
        self.pyshell.Execute('import pandas as pd')
        self.pyshell.Execute('from gpxutils import *')
        self.pyshell.Execute('from units import *')


    def UpdateScripts(self,event):
        sel=self.scriptcombo.GetValue()
        self.scriptcombo.Clear()
        for s in sorted([str(f.name) for f in self.cfg['scriptdir'].glob("[!_]*.py") if not str(f.stem).startswith('lib')])+["Browse file..."]:
            self.scriptcombo.Append(s)
        try:
            self.scriptcombo.SetValue(sel)
        except:
            pass

    def AttachGpx(self,data):
        self.gpx=data
        self.idx=0
        self.Link()

    def run(self,filename=None):
        if pathlib.Path(filename).is_file():
            self.pyshell.run("exec(open('{}').read())".format(filename))
            #self.pyshell.runfile(filename)
        elif (self.cfg['scriptdir']/filename).is_file():
            self.pyshell.run("exec(open('{}').read())".format(self.cfg['scriptdir']/filename))
            #self.pyshell.runfile(self.cfg['scriptdir']/filename)

    def copy(self,string):
        if not wx.TheClipboard.IsOpened():
            clipdata = wx.TextDataObject()
            clipdata.SetText(string)
            wx.TheClipboard.Open()
            wx.TheClipboard.SetData(clipdata)
            wx.TheClipboard.Close()

    def clear(self):
        self.pyshell.clear()

    def DetachGpx(self):
        self.gpx=None
        self.Link()

    def OnRunButtonClicked(self,event):
        if self.scriptcombo.GetValue()=='Browse file...':
            dialog = wx.FileDialog(None, "Choose a file", self.cfg['scriptdir'], "", "python file (*.py)|*.py", wx.FD_OPEN)
            if dialog.ShowModal() == wx.ID_OK:
                self.run(dialog.GetPath())
        else:
            self.run(self.cfg['scriptdir']/self.scriptcombo.GetValue())

    def OnSelectionChanged(self,emitter):
        if emitter!=self:
            pass

    def OnDataChanged(self,emitter):
        if emitter!=self:
            pass

    def OnIndexChanged(self, emitter, idx):
        if emitter!=self:
            pass

    def OnLeftMouseDown(self,event):pass
    def OnLeftMouseUp(self,event):pass
    def OnLeftMouseDblClick(self,event):pass
    def OnMouseMotion(self,event):pass
    def OnMouseEnter(self,event):pass
    def OnMouseLeave(self,event):pass
    def OnRightMouseDown(self,event):pass
    def OnMouseWheel(self,event):pass
    def OnPaint(self,event):pass
    def OnSize(self,event):
        self.pyshell.SetClientSize(self.GetClientSize())

    def OnErase(self,event):pass

class Plugin(WxShell):
    def __init__(self, *args, **kwargs):
       WxShell.__init__(self, *args, **kwargs)

    def GetName(self):
        return "Shell"
