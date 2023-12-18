#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import colorsys
import csv
import os
from statistics import mean
import wx
import wx.lib.newevent
from PIL import ImageDraw,ImageFont

from pilmap import *


(DownloadImageEvent, EVT_DOWNLOAD_IMAGE) = wx.lib.newevent.NewEvent()
            
class BufferedPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        kwargs['style'] = kwargs.setdefault('style', wx.NO_FULL_REPAINT_ON_RESIZE) | wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Window.__init__(self, *args, **kwargs)
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_SIZE,self.OnSize)
        self.OnSize(None)

    def Draw(self, dc):
        pass

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self, self._wxbuffer)

    def OnSize(self,event):
        if not hasattr(self, '_wxbuffer'):
            self._wxbuffer = wx.Bitmap(*self.ClientSize) ## useless, self._wxbuffer is overwritten in derived class
        self.UpdateDrawing()

    def UpdateDrawing(self):
        dc = wx.MemoryDC()
        dc.SelectObject(self._wxbuffer)
        self.Draw(dc)
        self.Refresh()
            
class WxMapPanel(BufferedPanel):
    def __init__(self, *args, **kwargs):
        USERAGENT="Mozilla/5.0 (X11; Fedora; Linux) Gecko/20100101 Firefox/63.0"
        provider=ThreadedGeoTileProvider(MAPSRC[3],
                                     useragent=USERAGENT,
                                     notifyfunc=lambda x,y:wx.PostEvent(self,DownloadImageEvent(downloaded_tile=(x,y)))                          
                                     )
        #provider.clearcache()
        self.map=GeoTileMap(provider=provider,tripplebuffered=True)
        self.x,self.y=-1,-1
        self.wxbg=wx.Bitmap(20,20)
        BufferedPanel.__init__(self, *args, **kwargs)
        self.dragging=False
        self.Bind(wx.EVT_MOTION,self.OnMotion)
        self.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftMouseDown)
        self.Bind(wx.EVT_LEFT_UP,self.OnLeftMouseUp)
        self.Bind(EVT_DOWNLOAD_IMAGE,self.OnNewTile)

    def Draw(self, dc):
        ## optionnaly draw a few things to self._wxbuffer
        #pen=wx.MemoryDC(self._wxbuffer)
        #pen.DrawEllipse(self.x,self.y,45,75)
        pass
        
    def OnNewTile(self,event):
        self.map.update(event.downloaded_tile)
        self.UpdateDrawing()

    def OnSize(self,event):
        if event:
            self.map.resize(event.Size[0],event.Size[1])
            self.map.update()
        BufferedPanel.OnSize(self,event)

    def OnMotion(self,event):
        if self.dragging:  ## event.Dragging is broken. or maybe linked to drag&drop?
            self.map.translate(event.GetX()-self.x_dragori,event.GetY()-self.y_dragori)
            self.map.update()
            self.x_dragori=event.GetX()
            self.y_dragori=event.GetY()
        else:
            for layer in self.map.layers.values():
                layer.onmousemove(event.GetX(),event.GetY())
        self.UpdateDrawing()

    def OnLeftMouseUp(self,event):
        self.dragging=False
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    def OnLeftMouseDown(self,event):
        for layer in self.map.layers.values():
            layer.onmousedown(event.GetX(),event.GetY(),1)
        self.dragging=True
        self.x_dragori=event.GetX()
        self.y_dragori=event.GetY()
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.map.update() ## should check wether layer mousedown should trigger redraw!
        self.UpdateDrawing()
    
    def OnRightMouseDown(self,event):
        for layer in self.map.layers.values():
            layer.onmousedown(event.GetX(),event.GetY(),3)
        self.map.update(tile=(-1,-1)) ## should check wether layer mousedown should trigger redraw!
        self.UpdateDrawing()
        
    def ZoomIn(self,e):
        self.map.zoomat(self.map.width//2,self.map.height//2,1)
        self.map.update()
        self.UpdateDrawing()
        
    def ZoomOut(self,e):
        self.map.zoomat(self.map.width//2,self.map.height//2,-1)
        self.map.update()
        self.UpdateDrawing()
        
    def OnMouseWheel(self,event):
        zoominc=1 if event.GetWheelRotation()>0 else -1
        self.map.zoomat(event.x,event.y,zoominc)
        self.map.update()
        self.UpdateDrawing()
        
    def UpdateDrawing(self):
        self._wxbuffer=wx.Bitmap.FromBuffer(self.map.width,self.map.height, self.map.image.tobytes())
        super().UpdateDrawing()

if __name__=='__main__':
    class TestFrame(wx.Frame):
        def __init__(self, parent=None):
            wx.Frame.__init__(self, parent,
                            size = (500,500),
                            title="MapWidgetTest",
                            style=wx.DEFAULT_FRAME_STYLE)

            ## Set up the MenuBar
            MenuBar = wx.MenuBar()
            file_menu = wx.Menu()
            item = file_menu.Append(wx.ID_EXIT, "&Exit")
            self.Bind(wx.EVT_MENU, lambda e:self.Close(True) or exit(0), item)
            MenuBar.Append(file_menu, "&File")
            self.SetMenuBar(MenuBar)

            self.MapPanel = WxMapPanel(self)
            self.MapPanel.map.layers['scalebar']=GeoScaleLayer(self.MapPanel.map)
            self.MapPanel.map.layers['measure']=GeoWaypointLayer(self.MapPanel.map,
                                                                           [],[],
                                                                           [(255,255,255)],
                                                                           linewidth=3,
                                                                           dotsize=10
                                                                           )
            lat=[]
            lon=[]
            speed=[]
            for e,l in enumerate(csv.reader(open(os.path.dirname(__file__)+"/windsurf.csv"))):
                if e:
                    speed.append(float(l[0]))
                    lat.append(float(l[1]))
                    lon.append(float(l[2]))
            mini=min(speed)
            maxi=max(speed)
            norm_speed=list(map(lambda x : (x-mini)/(maxi-mini),speed))
            colorscale=[tuple(int(t*255) for t in colorsys.hsv_to_rgb((h/255)*0.75,1.0,1.0)) for h in range(255,0,-1)]
            color=[colorscale[int(c*254)] for c in norm_speed]
            self.MapPanel.map.layers['track1']=GeoAnimPathLayer(self.MapPanel.map,lat,
                                                                           lon,
                                                                           color,
                                                                           linewidth=1,
                                                                           dotsize=0.0
                                                                           )
            self.MapPanel.map.lookat(mean(lat),mean(lon),zoom=12)
            self.MapPanel.UpdateDrawing()
                
            self.Show()

    class DemoApp(wx.App):
        def OnInit(self):
            frame = TestFrame()
            self.SetTopWindow(frame)
            return True

    ImageDraw.ImageDraw.font = ImageFont.truetype("/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",size=15)
    app = DemoApp(0)
    app.MainLoop()
    exit(0)
