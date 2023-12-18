#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

## system imports

import wx
import wx.grid
import numpy as np
import msgwrap
import ast
import pickle
import os
import gpxutils
from wxquery import WxQuery

# small utilities functions for line intesection
def ccw(A,B,C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

# Return true if line segments AB and CD intersect
def intersect(A,B,C,D):
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

class SimpleGrid(wx.grid.Grid):
    def __init__(self, parent):
        wx.grid.Grid.__init__(self, parent, -1)
        self.CreateGrid(10, 1)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnCellRightClick)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClick)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.ascend=False
        self.data=[]
        self.headers=[]
        self.SetRowLabelSize(32)
    
    def OnSize(self,event):
        for col in range(7):
            if (event.Size[0]-32.0)/(7.0)>0:
                self.SetColSize(col, int((event.Size[0]-32.0)/(7.0)))
        self.Centre( wx.HORIZONTAL )
        
    def SetHeaders(self,headers):
        self.headers=headers
        while self.GetNumberCols()<len(headers):
            self.AppendCols(1)
        for c in range(0,len(headers)):
            self.SetColLabelValue(c, headers[c])
        self.AutoSize()

    def SetData(self,data):
        self.data=data
        self.ClearGrid()
        while self.GetNumberRows()<len(data):
            self.AppendRows(1)
        for r in range(0,len(data)):
            for c in range (0, len(data[r])):
                self.SetCellValue(r, c, str(data[r][c]))
        self.AutoSize()
        
    def OnLabelRightClick(self,event):
        if event.GetCol()>=0:
            col=event.GetCol()
            data=sorted(self.data, key=lambda k:(k[col]), reverse=self.ascend)
            self.SetData(data)
            self.ascend= not self.ascend
        
    def OnCellRightClick(self,event):
        menu = wx.Menu()
        item = wx.MenuItem(menu, wx.NewId(),"Copy Table")
        self.Bind(wx.EVT_MENU, self.CopyAll, item)
        menu.AppendItem(item)
        self.PopupMenu(menu)
        menu.Destroy()

    def CopyAll(self,event):
        buffer=""
        buffer+="\t".join(self.headers)+"\n"
        for r in range(0,len(self.data)):
            buffer+="\t".join(map(str,self.data[r]))+"\n"
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(wx.TextDataObject(buffer))
        wx.TheClipboard.Close()
        
class WaypointsPlugin(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.MapPanel = kwargs.pop('MapPanel', None)
        self.TimePanel = kwargs.pop('TimePanel', None)
        self.cfg = kwargs.pop('cfg', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.gpx=None
        self.gates=[]
        self.disableoutside=False
        self.latkey='lat'
        self.lonkey='lon'
        self.speedkey='speed'


        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.hsizer= wx.BoxSizer(wx.HORIZONTAL)
        self.analysebutton=wx.Button(self,-1,"Analyse")
        self.loadbutton=wx.Button(self,-1,"Load gates...")
        self.savebutton=wx.Button(self,-1,"Save gates...")
        self.resultsgrid=SimpleGrid(self)
        self.resultsgrid.SetHeaders(['lap','start','stop','duration','distance','avg speed','top speed'])
        self.hsizer.Add(self.savebutton,0,wx.TOP|wx.LEFT|wx.EXPAND)
        self.hsizer.Add(self.loadbutton,0,wx.TOP|wx.LEFT|wx.EXPAND)
        self.hsizer.Add(self.analysebutton,0,wx.TOP|wx.RIGHT|wx.EXPAND)
        self.sizer.Add(self.hsizer,0,wx.TOP|wx.CENTER|wx.EXPAND)
        self.sizer.Add(wx.StaticText(self,wx.NewId(),"Results (m, s,user):"),0,wx.TOP)
        self.sizer.Add(self.resultsgrid,0,wx.TOP|wx.ALL|wx.CENTER|wx.EXPAND)
        self.MapPanel.Bind(wx.EVT_LEFT_DOWN,self.OnMouseDown)
        self.MapPanel.Bind(wx.EVT_RIGHT_DOWN,self.OnMouseDown)
        self.analysebutton.Bind(wx.EVT_BUTTON, self.OnAnalyseButton)
        self.loadbutton.Bind(wx.EVT_BUTTON, self.OnLoadButton)
        self.savebutton.Bind(wx.EVT_BUTTON, self.OnSaveButton)

        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

        msgwrap.register(self.OnIndexChanged, "INDEX_CHANGED")
        msgwrap.register(self.OnSelectionChanged, "SELECTION_CHANGED")
        msgwrap.register(self.OnDataChanged, "DATA_CHANGED")

    def GetGates(self):
        layer=self.MapPanel.map.layers['gates']
        points=2*( len(layer.lat)//2)
        self.gates=[(n,n+1) for n in range(0,points,2)]

    def OnLoadButton(self,event):
        dialog = wx.FileDialog(None, "Choose File name and destination", os.getcwd(),"", "pickle file|*.pkl", wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            gates=pickle.load(open(dialog.GetPath(), "rb"))
            self.MapPanel.map.layers["gates"].lat,self.MapPanel.map.layers["gates"].lon=map(list,zip(*gates))
            self.MapPanel.map.update()
            self.MapPanel.UpdateDrawing()
            self.GetGates()

    def OnSaveButton(self,event):
        dialog = wx.FileDialog(None, "Choose file to load gates", os.getcwd(), "", "pickle file|*.pkl", wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            gates=list(zip(self.MapPanel.map.layers["gates"].lat,self.MapPanel.map.layers["gates"].lon))
            pickle.dump(gates, open(dialog.GetPath(), "wb"))

    def OnAnalyseButton(self,event):
        gatestr=(','.join([str(g[0]//2) for g in self.gates]))
        self.latkey,self.lonkey,self.speedkey,gatestr,self.disableoutside=WxQuery("Waypoint options",
                                            [('wxcombo','Key for latitude','|'.join(self.gpx.columns),'lat','str'),
                                            ('wxcombo','Key for longtude','|'.join(self.gpx.columns),'lon','str'),
                                            ('wxcombo','Key for speed','|'.join(self.gpx.columns),'speed','str'),
                                            ('wxentry','Comma separated list of gates',None,gatestr,'str'),
                                            ('wxcheck','Disable invalid points',None,self.disableoutside,'bool')]
                                            )
        self.gates=[(2*int(i),(2*int(i)+1)) for i in gatestr.split(',')]
        print(self.gates)
        self.Analyse()
        
    def Analyse(self):
        if not self.gpx is None and len(self.gates)>0:
            lat=self.MapPanel.map.layers['gates'].lat
            lon=self.MapPanel.map.layers['gates'].lon
            sect_door=[]
            sect_idx=[]
            segments=[]
            for p in range(1,len(self.gpx)):
                for gate in self.gates:
                    d1=lat[gate[0]],lon[gate[0]]
                    d2=lat[gate[1]],lon[gate[1]]
                    p1=(self.gpx[self.latkey][p-1],self.gpx[self.lonkey][p-1])
                    p2=(self.gpx[self.latkey][p],self.gpx[self.lonkey][p])
                    if intersect(p1,p2,d1,d2) or intersect(p1,p2,d2,d1) or intersect(p2,p1,d2,d1) or intersect(p2,p1,d2,d1):
                        sect_door.append(gate)
                        sect_idx.append(p)
                        break ##skip remaining doors
            for d in range(0,len(sect_door)):
                ngates=len(self.gates)
                if sect_door[d:d+ngates]==self.gates:
                    ## skip segments if some points are disabled. Don't event understand my code!
                    if np.all( self.gpx['ok'][sect_idx[d]-1:sect_idx[d+ngates-1]] ):
                        segments.append((sect_idx[d]-1,sect_idx[d+ngates-1]))
            if self.disableoutside :
                self.gpx['ok']=False
                for s in segments:
                    self.gpx['ok'][s[0]:s[1]]=True
                msgwrap.message("SELECTION_CHANGED",emitter=self)
            data=[]
            lap=0
            for s in segments:
                lap+=1
                #['lap','start','stop','duration','distance','avg speed','top speed']
                dxy=gpxutils.hv_distance(self.gpx[self.latkey],self.gpx[self.lonkey])
                try:
                    speedscale=gpx[self.speedkey].attrs["u_scale"]
                except:
                    speedscale=1.0
                data.append([lap,\
                            #self.gpx['time'][s[0]][11:19],
                            #self.gpx['time'][s[1]][11:19],
                            self.gpx['time'][s[0]].strftime('%H:%M:%S.%f'),
                            self.gpx['time'][s[1]].strftime('%H:%M:%S.%f'),
                            np.sum(self.gpx['deltat'][s[0]:s[1]]), 
                            #np.sum(self.gpx['deltaxy'][s[0]:s[1]]),
                            np.sum(dxy[s[0]:s[1]]),
                            #np.sum(self.gpx['deltaxy'][s[0]:s[1]])/np.sum(self.gpx['deltat'][s[0]:s[1]]),
                            speedscale*np.sum(dxy[s[0]:s[1]])/np.sum(self.gpx['deltat'][s[0]:s[1]]),
                            self.gpx[self.speedkey].unit.scaled[s[0]:s[1]].max()])
            self.resultsgrid.SetData(data)
            w,h=self.GetSize()
            self.SetSize((w+1,h))
            self.SetSize((w,h))

    def AttachGpx(self,data):
        self.gpx=data

    def DetachGpx(self):
        self.gpx=None

    def OnSelectionChanged(self,emitter):
        if emitter!=self:
            pass

    def OnDataChanged(self,emitter):
        if emitter!=self:
            pass

    def OnIndexChanged(self, emitter,idx):
        if emitter!=self:
            pass

    def OnDraw(self,event):
        pass
        
    def OnSize(self,event):
        pass

    def OnMouseDown(self,event):
        wx.CallAfter(self.GetGates)
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

class Plugin(WaypointsPlugin):
    def __init__(self, *args, **kwargs):
       WaypointsPlugin.__init__(self, *args, **kwargs)

    def GetName(self):
        return "Waypoints"
