#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import warnings
warnings.filterwarnings("ignore")
import colorsys
import json
import wx
import wx.lib.newevent
from PIL import ImageDraw,ImageFont
import pandas as pd,numpy as np
import gpxutils
from WxButtonBitmap import *
import msgwrap
from itertools import cycle
from pilmap import *
from wxquery import WxQuery

## base64 definition of up/down icons. generated using faicon
ICN_add_up=b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAA1ElEQVR4nGP8//8/AzqQW/QZU5AI8CiOlxFdjBHZAnINxmcRE7UNRzeLidqGo1vCREghpYBRduEnqrseGZDkgxn2nAzT7DhJsoCFFMUq/EwMf0j0L83jYOhbgDMOZthzMijwodovzwvh7/DlRhG/9/EfQ9ah76RZwMzEwMCCVrIwMjAw/GfAFGfCKIGQ9JCSD/b4cTP8+c/A4LH5K7FahkEkD1wqwgbuf/7H8PcfaRbQvrDDVs1RCzyK42WkTyTTwhcwM5nQBahpOAMDWqsCBqjZbAEAXwtF2+17F1YAAAAASUVORK5CYII='
ICN_add_down=b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAvUlEQVR4nNWWMRKDIBBFd5k0cJRtoefqcABKvMqWpCKjgAoRk/F1fJn/ZT4omFKCEu99LXZgrcVSw3XAt8ZHQWK2eeklZpuXIeJs4lXQOTf97dcMrYCIgIiGAl4jk5VS0NrWR9zewfMDdjsgIpBSbrQ81lpvdGaGZVnGAhAREKtPy+dZL7sBMcZKM8ZASglCCN0Bzy/5f7uoBTMPn+ShgFbxZ4jWb24W1lr8Tcl3rCJ7ilKYaQ5Q3CoyM68tb4qPRZ9x1OWqAAAAAElFTkSuQmCC'
ICN_remove_up=b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAj0lEQVR4nGP8//8/AzqQW/QZU5AI8CiOlxFdjBHZAnINxmcRE7UNRzeLidqGo1vCREghpYBRduEnqrseGdDcB6MWDLwFLLgkZthzMijwEWf/vY//GLIOfSfNAmYmBgYWjJIFO2DCo240H4xaQAULsFVz1AKP4ngZ6RNEtPAFzEwmdAFqGs7AgNaqgAFqNlsACPgzLoyW9VUAAAAASUVORK5CYII='
ICN_remove_down=b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAj0lEQVR4nO2WSwrAIAwF86Qbr+IlcnU9hF7FpV0JJf1aYwulbxllxiioKKWQTAhhXbwQZoasYSm4Cz4SGW24ZBltuJSYs4m9gfdeffXLDO/gF7wvmPYGnHNkrb0EyTlTSqlNAICA1dXSnF1BjLEbTvSFQ/4F54KtZ04rzIxntmhEF5VpZEETTiR+FTWa35YZmtcyag2wyBQAAAAASUVORK5CYII='
ICN_distance_up=b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAABnUlEQVR4nK2WvUoDQRRGzwxRMRZiCPkj1qIIYoJ2GiHBOi9gZyvWahobwdLOUmwsk0cwaKMgVoKiYGdMpSkSiMaMxSQkuzsbJ5Lb7J27335n5s6wu0IphSdKGUPRIvJl4S4JB+C/xgNAcuTmLi85cnMXJGC8KSREVnVevQF8+EJCZKWjuzXqhCque6tzWzC/rfOHU3i+MAMsdNJTAQjG+vK42dxSZ27R4xmIAKDg6dwfYKEzA5qf8FrU+VfNH2ChcwJkAFL7kMjoHKDdgrdLuDsC9TOcDvcehBYhme091DVL5iC0MLwO9ykam/Lf1HoFWvXhdLhb9F2H2ksHLUG1zSb9uj+05mMqJKQLZnNTpAv6GSuAkJA+0D22jWQWUntGiLNFQmphMqfHq4f2kNlN3ab7Y0e7nICJGQgv9caJDXsAQHgZxqeh+dGbs+ddFIzD2glMRqGUsTPOl6FRhesdfe0Lb9MaFbja9QgHho+5XoFS5u9BMAaNdztAMGqeUL7sc7bA3hwGrlZ2SfZultHxlO7CKM3B/VfRjRH+tvwC+KmbudBc5poAAAAASUVORK5CYII='
ICN_distance_down=b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAABeUlEQVR4nK2Wv86CMBTFTxuCTGJIqJuJkw2Tb9BXhzfAjcmEGCdXEhvE9BtMiZb242q4E1xOz69/Lm2ZMQZuVFU1TRJCKcXcHHsH/Gr8H4gvbe568aXNXQgPCbIsQ5Zls0ZzOlaW5aT3u90O+/0eAHA+n3G5XLyNKTrvCJIk8T7/oot8ybZtwTmHMQZt2wYBFJ0X8Hg8cL1eAQDDMAQBFN0HgDEGKSXyPAdjr1I2xuB2u6FpGth/hqoDnDVI0xRCiLGRNRNCYL1ef60DnCqKoii4WPf7Hc/n8yvdZIqGYUDXdWOPfPuUq5vTesvUzjE1pJQf0zULkFJCCEEGCCFwOBy83yZl+m5eFAUZst1uAQBN04QBcRxjs9mM73mekwHAq7riOEbf935A3/eo6xrH4xGr1QpVVZGMlVLQWuN0On2YA5410Fqjrmtorck9t+a+NswY4z0PkiQhQ0JapRQLngffjiAU3JLIbsSwntxNLGkOOLcKG0teW/4AzwrQuCZLMZYAAAAASUVORK5CYII='
ICN_star_up=b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAACH0lEQVR4nK2WT0wTQRTGf7vdytYaW1jUCP6JRKhKgJN60XIgHowXwtGDcoPEYPTgWePFoyaNXj158SCcNTEpTfyDiYkSo6LWAxGp0baQAK1S1sNrg91tt7PYL3mZzZv3vm/mzczOaLZt48LUYA2nAoaTmtOlVQlsldhDSG86uYNL90WuG2I+RPRGcVXoGBTzAc2ejKuXJn4PsGH6knKK4nyBaAzaesvfPZCfU0pTL1HXCCynxbpGlNPUBLZFYN8QpCfh6xR0DolPAdUlMrbD3lPQ0lq2qLThTij9hvnHEndsDOJ3YeUbFHNQzJfbHCxMQ6lQR2B9FYI7oHccNB1+zMDaT1j6Arn3m4mvb0HrUREPtcOBs2BvwNs7VeRuAYD0I1hdhOPXAQ1mEyL8L76nxIwwnLgJ62vw6gZkXrjoaq/B4jNIXYbIYTidALPdHRPaBfEE7DwEqYma5PUFAPIfITkGod0Qu+DuPzIKLRYkx2HpU10a711UyIIRkvoDaAExEJ9hQjHrSeF90KIx0IOQfQfWAAxcBWx4cxt+zULAhEj35gB8C1h9sPFHSrT/jCysbcu6zD+RPqvvPwX0oPwinl+DzIz495yE/ivSZ/XD54dbFIj0wIf7MPdARltB5iU8vQjd5+HgOU8KudFq3QcBE8w2WFnwJCDcIZvBccAAGE5q9WdQKjQmh4YxekWpMZNPlDl1p6OZ5OB8VVTQxGfLX9AatB7aVIOwAAAAAElFTkSuQmCC'
ICN_star_down=b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAACLklEQVR4nK2WQWvyQBRFz0zM2GJiQIxUpITSdmM35hfkr9e9NEJBKHVRaO1C0kAbpTYlYxcfSjU2xn69m4GX9+6ZvJlkRiyXS7bV7/fzwRIKgkBsx8R3wG+Ni0Dyr823veQh5kIIhMh1oRAi9yV+l+u6uK57SAni+vq6dGt83wcgDMPSgErZRNu2qdfrAFiWxWw2K1VXukWdTof5fM58PqfT6ZQtKwcwTRPXdZlMJjw/P9NqtTBNsxRgo0WGYdBsNjFNE6XUejw+PkZrzXQ6BeDs7Azf93l/fydNUz4/P9djFEVkWbYbkGUZlUqF8/NzAOI4Jk1TZrMZSZKsC+/u7rBtG6UUSilOTk5YLpeMx+MN8xwAYDKZsFgs6Ha7CCF2FkVRRBRFGIbB1dUVWZYxGo2I4zjXop1r8PLywnA4pFar0ev1UErlcqrVKr7vU6vVGA6HO81/BAAkSUIYhlSrVTzPyz33PA+lFDc3N4VbtnAXfXx8YBgGSZIAm7+KJEkwDIM0TYssij8027aRUvL29objOFxeXgJwf3/P6+srUkosy1pP4GCA4zhorfE8j1arRRRFAPR6PabTKVprHMf5P4CUEtu2ub29XS9ko9Hg4uICKSWO4/D09PQ7gGVZPDw88Pj4iNZ6HY/jmMFgwOnpKe12u8ji34m26zyQUqKUYrFYFBocHR2RpunGBFYKgkD8+AZa673mwN4cuSLtdTpQK0+5HfhLc9i6Vaz0l9eWL2zx/cxv6B+5AAAAAElFTkSuQmCC'
ICN_favorite_up=b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAACUElEQVR4nK2Wy2tTQRTGfzcvo21TWluDDwpiQyN1IS2mAUvtwpW46Easgqgr9W8QV8UKbtqNSqsIKi5E1AqtQnFhdqILXzV9SAwJKrRqtUaNpDHj4jTE+0zUfDBw7zlnvm/mm7kzV1NKYcLYLotgBeiLacaQphP4V2IHIVfVyQ1crqqTG0Q8tgVrgtC4DXz18Hkall5DIb8yLA/Uh6BhK+SW4NMUZOctaTR1p0c/es0FbYeh7RBo7lI8k4bHp+S5awBqW0q5Qh7mrsHsVVAFHZ15Blv2QfgILMYhcQN+LkLTdggdgN4RqVG/YPoSfHwG/rXQ2g/ho7CcgcQthxm4fbBnHL6lIXa8ZAmIHT3nAQWxE/BltpRzeaF3FGo2wMReKCyXUjq5QCu4V0FqQk8Osg6T+2GyX08OQpi6B24/BDY7WOStNTmmQ3bBOQ/grdO96meQSQIKmjrKExnR3CELnEk6CGQ/wMITWL8TGsKVkze2QzAK849kU9gKADwfEv87T4qn5eBZLbWFHLwYNqXNAt/fQ/yi7PPooOwsO7h90DUINRth6gL8MH9sZgGAxE1pzZ0QGZBtaOrphchp8X7uOiTHLKmsBQBenoP0ffE2ekZvl9svsWAEknchPmpLYy+AgqdnITUO63ZA9xD4AtK6hyX25rasmQPMZ5EV2o9B6CBkUoAGdS0wcxlmrpTtan+a/olXI5D7KkJKyahtPDdCbrRK74NNu0Hl4d3Disrpi2mVzaCItw/+qhyKi2xxWf83VjhdxkA1ycH4V1FEFX9bfgNPF8LZjIhP0AAAAABJRU5ErkJggg=='
ICN_favorite_down=b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAACZUlEQVR4nK2WS0/qQBiGn5laoxWbtiaurIJuSCpefwB/XZeudONCQSqmFOKFpFAvXOKczQGlF8VzfHcz883zznxzFUopkjo9PU1XzqFqtSqSdeKzwb+CvzKSvw1PsuRvw5MmC3kBS0tLmKaJruv0ej3iOGaSTiEEhUIB0zQZjUZEUcRgMMjkiJOTk9Toi8Uim5ubCPGxZi8vL1xeXgLgeR6GYUzblFI0m02azWbKIDWDjY0Ntra26PV6BEHAcDjEsixc1+Xo6Gga5/s+URSxuLiI67oUi0XG4zGtVivfQEpJqVQijmMuLi6mKYmiiG63y+HhIQDn5+f0+/1pv8fHR46PjymVSoRhyOedOWNQKBSQUtJut0mej36/z9nZGUAq30opOp0OOzs7rKysEMdxtsHCQu6aZ4KzpOv6TFl+Ljw/PwNg2/a3oKQsy5phZBoMBgO63S5ra2usrq7ODTdNE8dxeHp6Yjgc5hsA1Ot1lFKUy2U0TfsWrmka5XKZ9/d36vV6qj1l8Pr6iu/7GIaB53lImQr56Cwlu7u7LC8v02g0eHt7+94AIAgCgiDAtm08z5s5cBMJIfA8D8uyuLu7IwzD7EHkje7m5oZOp4PjOFQqlZl0aZpGpVLBcRzCMMT3/fxZ5rYAV1dXtNttbNtmb28PXdfRdZ39/X1s26bValGr1b5C5F92E11fXzMej3Fdl4ODAwAMw+D29jbz7vmxAUCj0WA0GrG9vQ1ArVbLzXlSQik193uwvr6OUoqHh4e54NVqVcw1g4nu7+9/Eg78XeSsx/p/NWHKZMVvwiHxq5joN78tfwA1NA0hsdJJywAAAABJRU5ErkJggg=='

(DownloadImageEvent, EVT_DOWNLOAD_IMAGE) = wx.lib.newevent.NewEvent()

#(CurChangedEvent,EVT_CURRENT_CHANGED) = wx.lib.newevent.NewEvent()   ## emitted when currently selected point changes
#(SelChangedEvent,EVT_SELECTION_CHANGED) = wx.lib.newevent.NewEvent() ## emitted when current selection changes
#(DataChangedEvent,EVT_DATA_CHANGED) = wx.lib.newevent.NewEvent()     ## emitted when current data changes

class PdPathLayer(MapLayer):
    def __init__(self,parent,gpx=None,
                 latkey='lat',lonkey='lon',colorkey='speed',headingkey="heading",
                 colorscale=[],linewidth=1,joint='curve',dotsize=0.0,
                 tracker=[(0,2),(-4,4),(0,-5),(4,4)], trackercolor=(0,0,255),
                 followmouse=False):
        super().__init__(parent)
        self.linewidth=linewidth
        self.joint=joint
        self.dotsize=dotsize
        self.tracker=tracker
        self.trackercolor=trackercolor
        self.latkey=latkey
        self.lonkey=lonkey
        self.headingkey=headingkey
        self.colorkey=colorkey
        ##for vector data only
        self.anglekey=None
        self.normkey=None
        self.scale=0
        self.followmouse=followmouse

        self.x,self.y=None,None
        if len(colorscale):
            self.colorscale=colorscale
        else:
            self.colorscale=[tuple(int(t*255) for t in colorsys.hsv_to_rgb(h,1.0,1.0)) for h in np.linspace(240/360,0,256)]
        if not gpx is None:
            self.attach_gpx(gpx)
        else:
            self.gpx=None

    @property
    def lat(self):
        return self.gpx[self.latkey]
    
    @property
    def lon(self):
        return self.gpx[self.lonkey]
    
    @property
    def angle(self):
        return self.gpx[self.anglekey]
    
    @property
    def norm(self):
        return self.gpx[self.normkey]
    
    @property
    def heading(self):
        return self.gpx[self.headingkey]

    def attach_gpx(self,gpx):
        try:
            if all([k in gpx.columns for k in [self.latkey,self.lonkey,'ok']]):
                self.gpx=gpx
                self.idx=0
        except:
            pass
        
    def draw(self):
        if self.visible and len(self.lat)>0 and len(self.lon)>0:
            try:
                colorkey=self.gpx[self.colorkey].copy() ## otherwise attrs are lost
                mini=np.min(colorkey[self.gpx.ok])
                maxi=np.max(colorkey[self.gpx.ok])
                norm=(colorkey-mini) / (maxi-mini)
                norm=np.clip(norm,0,1)
                #mini=np.min(self.gpx[self.gpx.ok][self.colorkey])
                #maxi=np.max(self.gpx[self.gpx.ok][self.colorkey])
                #norm=(self.gpx[self.colorkey]-mini) / (maxi-mini)
                #norm=np.clip(norm,0,1)
                colors=pd.Series([self.colorscale[int(c*255)] for c in norm])
            except:
                try:
                    if self.colorkey.startswith("#") and len(self.colorkey)==7:
                        colors=[tuple(int(self.colorkey[i:i+2], 16) for i in (1, 3, 5))]
                    else:
                        colors=[(255,0,0)]
                except:
                    colors=[(255,0,0)]

            pen=ImageDraw.Draw(self.parent.fg)
            xy=pd.Series(zip(*self.parent.geotoscreen_v(self.lat,self.lon)))
            colorcycler=cycle(colors) ## cyclers cannot be reset in python
            x1,y1=xy[0]
            for e,(x2,y2) in enumerate(xy[1:]):
                color=next(colorcycler)
                if self.gpx['ok'][e]:
                    pen.line([(x1,y1),(x2,y2)],
                            fill=color, 
                            width=self.linewidth, 
                            joint=self.joint)
                x1,y1=x2,y2
            if self.dotsize:
                hw=self.dotsize//2
                colorcycler=cycle(colors)
                for e,(x,y) in enumerate(xy):
                    color=next(colorcycler)
                    if self.gpx['ok'][e]:
                        pen.ellipse([x-hw,y-hw,x+hw,y+hw],
                                    fill=color)
        
    def animate(self):
        def translate(p,h,v):
            return [(x+h,y+v) for x,y in p]
        def scale(p,h,v):
            return [(x*h,y*v) for x,y in p]
        def rotate(p,theta):
            return [(x*np.cos(theta)-y*np.sin(theta), x*np.sin(theta)+y*np.cos(theta)) for x,y in p]
            
        if not self.visible:
            return
        pen=ImageDraw.Draw(self.parent.topmost)
        if len(self.gpx.lat)>0 :
            x,y=self.parent.geotoscreen(self.lat[self.idx],self.lon[self.idx])
            theta=self.heading[self.idx]*np.pi/180
            pen.polygon(translate(scale(rotate(self.tracker,
                                                theta),
                                        2,2),
                                  x,y),
                        fill=self.trackercolor)
            if self.anglekey and self.normkey and self.scale:
                a=self.angle[self.idx]*np.pi/180
                n=self.norm[self.idx]*self.scale/self.normmax ## scale=max_wanted_length_in_pixels/max(key)
                pen.line([x,y,x+n*np.sin(a),y-n*np.cos(a)],fill=(255,0,0),width=3)

                        
    def onmousemove(self,x,y):
        if not self.followmouse:
            return
        self.x,self.y=x,y
        lat,lon=self.parent.screentogeo(self.x,self.y)
        #self.idx=np.argmin(gpxutils.hv_distance(self.gpx.lat,self.gpx.lon,tgt=(lat,lon)))
        ## fast square euclidean approximation. we only look for minimum!
        #distances=(self.lat-lat)**2+(self.lon-lon)**2
        distances=np.abs(self.lat-lat)+np.abs(self.lon-lon) ## l1 distance is usfficient to find minimum
        #distances=gpxutils.hv_distance(self.lat,self.lon,tgt=(lat,lon))
        distances[~self.gpx.ok]=np.nan
        self.idx=np.nanargmin(distances)
            
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
        #del dc # need to get rid of the MemoryDC before Update() is called.
        #self.Refresh(eraseBackground=False)
        self.Update()
            
class WxMapPanel(BufferedPanel):
    def __init__(self, *args, **kwargs):
        ##
        self.useragent=kwargs.pop("useragent","Mozilla/5.0 (X11; Fedora; Linux) Gecko/20100101 Firefox/63.0")
        self.services=kwargs.pop('services',{MAPSRC[3][0]:MAPSRC[3]})
        self.service=kwargs.pop('service',list(self.services.keys())[0] )
        provider=ThreadedGeoTileProvider(self.services[self.service],
                                     useragent=self.useragent,
                                     cachedir=kwargs.pop('cachedir',None),
                                     numthreads=kwargs.pop('numthreads',5),
                                     notifyfunc=lambda x,y:wx.PostEvent(self,DownloadImageEvent(downloaded_tile=(x,y)))                          
                                     )

        self.map=GeoTileMap(provider=provider,tripplebuffered=True)
        self.x,self.y=-1,-1
        self.wxbg=wx.Bitmap(20,20)
        BufferedPanel.__init__(self, *args, **kwargs)
        yoffset=28
        ## map buttons
        self.btn1 = WxButtonBitmap(self, -1, bitmapon=ICN_add_up, bitmapoff=ICN_add_down, size=(24,24),pos=(24,yoffset), initial=0)
        self.btn1.Bind(wx.EVT_BUTTON, self.ZoomIn  )
        self.btn2 = WxButtonBitmap(self, -1, bitmapon=ICN_remove_up, bitmapoff=ICN_remove_down, size=(24,24),pos=(24,yoffset*2), initial=0)
        self.btn2.Bind(wx.EVT_BUTTON, self.ZoomOut )
        self.tools={}
        self.tools['measure'] = WxToggleButtonBitmap(self, -1, bitmapon=ICN_distance_up, bitmapoff=ICN_distance_down, name='measure',size=(24,24),pos=(24,yoffset*3), initial=0)
        self.tools['measure'].Bind(wx.EVT_TOGGLEBUTTON, self.OnTool)
        self.tools['gates'] = WxToggleButtonBitmap(self, -1, bitmapon=ICN_star_up, bitmapoff=ICN_star_down, name='gates',size=(24,24),pos=(24,yoffset*4), initial=0)
        self.tools['gates'].Bind(wx.EVT_TOGGLEBUTTON, self.OnTool)
        #self.tools['other'] = WxToggleButtonBitmap(self, -1, bitmapon=ICN_favorite_up, bitmapoff=ICN_favorite_down, name='other',size=(24,24),pos=(24,yoffset*5), initial=0)
        #self.tools['other'].Bind(wx.EVT_TOGGLEBUTTON, self.OnTool)
        ## map popup menu
        self.rightclickmenu=wx.Menu()
        self.mapsrcmenu=wx.Menu()
        self.layermenu = wx.Menu()
        self.actionmenu = wx.Menu()
        for text in ["Add layer","Delete layer..."]:
            item = self.layermenu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.OnLayerPopupMenu,item)
        for text in self.services.keys():
            item = self.mapsrcmenu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.OnMapsrcPopupMenu,item)
        for text in ["Force refresh","Prefetch","Clear cache"]:
            item = self.actionmenu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.OnActionPopupMenu,item)
        self.rightclickmenu.AppendMenu(-1, "Layers", self.layermenu)
        self.rightclickmenu.AppendMenu(-1, "Map source", self.mapsrcmenu)
        self.rightclickmenu.AppendMenu(-1, "Actions", self.actionmenu)
        self.dragging=False
        self.reportindex=True
        self.Bind(wx.EVT_MOTION,self.OnMotion)
        self.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftMouseDown)
        self.Bind(wx.EVT_LEFT_UP,self.OnLeftMouseUp)
        self.Bind(wx.EVT_RIGHT_DOWN,self.OnRightMouseDown)
        self.Bind(wx.EVT_LEFT_DCLICK,self.OnLeftDoubleClick)
        self.Bind(EVT_DOWNLOAD_IMAGE,self.OnNewTile)

    def Draw(self, dc):
        ## optionnaly draw a few things to self._wxbuffer
        #pen=wx.MemoryDC(self._wxbuffer)
        #pen.DrawEllipse(self.x,self.y,45,75)
        pass
    
    def OnIndexChanged(self,emitter,idx):
        ## normally, we would skip these events, but extra track layers need to be informed!
        for name,layer in self.map.layers.items():
            if name.startswith('track'):
                layer.idx=idx
        self.map.update()
        self.UpdateDrawing()
        self.Refresh(eraseBackground=False)

    def OnSelectionChanged(self,emitter):
        if emitter!=self:
            self.map.update()
            self.UpdateDrawing()
            self.Refresh(eraseBackground=False)

    def OnDataChanged(self,emitter):
        if emitter!=self:
            for name,layer in self.map.layers.items():
                layer.idx=0
            self.map.update()
            self.UpdateDrawing()
            self.Refresh(eraseBackground=False)

    def OnAppMessage(self,emitter,data):
        if emitter!=self:
            if data['msg']=='replay':
                self.reportindex=not data['value']
                
    def OnActionPopupMenu(self,event):
        item = self.actionmenu.FindItemById(event.GetId()).GetItemLabelText()
        if item=="Force refresh":
            self.map.update(force=True)
            self.UpdateDrawing()
        elif item=="Prefetch":
            self.map.prefetch(zinc=2,fake=False)
        elif item=="Clear cache":
            self.map.provider.clearcache()

    def OnMapsrcPopupMenu(self,event):
        self.service = self.mapsrcmenu.FindItemById(event.GetId()).GetItemLabelText()
        self.map.provider.map_src=self.services[self.service]
        self.map.provider.gettile.cache_clear()
        self.map.update()
        self.UpdateDrawing()
        self.Refresh(eraseBackground=True)

    def OnLayerPopupMenu(self,event):
        if not "track1" in self.map.layers.keys():
            wx.MessageBox('No opened file.\n Please open file before trying to add layers', 'Info', wx.OK | wx.ICON_INFORMATION)
            return
        item = self.layermenu.FindItemById(event.GetId()).GetItemLabelText()
        if item=="Add layer":
            cnt=len([k for k in self.map.layers.keys() if k.startswith("track")])
            self.map.layers[f"track{cnt+1}"]=PdPathLayer(self.map,self.map.layers["track1"].gpx, linewidth=2, dotsize=0.0)
            self._tunelayer(f"track{cnt+1}")
            self.map.update()
            self.UpdateDrawing()
        elif item=="Delete layer...":
            options=[k for k in self.map.layers.keys() if k.startswith("track") and k!="track1"]
            if len(options):
                tracklabel,=WxQuery("Choose layer to delete",
                    [('wxcombo','Layer','|'.join(options),"track2",'str')])
                if tracklabel:
                    del self.map.layers[tracklabel]
                    self.map.update()
                    self.UpdateDrawing()
            else:
                wx.MessageBox('No track to delete.\n At least one track must be present.', 'Info', wx.OK | wx.ICON_INFORMATION)
        
    def OnTool(self,event):
        ## disable companion buttons
        _name=event.GetEventObject()._name
        if event.IsChecked():
            for name,tool in self.tools.items():
                if name!=_name:
                    tool.SetValue(0)
        ## activate/deactivate layers accordingly
        for name in self.map.layers:
            try:
                self.map.layers[name].active=self.tools[name]._value
            except:
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
            self.UpdateDrawing()
            self.Refresh(eraseBackground=False)
        else:
            if self.reportindex:
                for name,layer in self.map.layers.items():
                    layer.onmousemove(event.GetX(),event.GetY())
                    if name=='track1':
                        msgwrap.message('INDEX_CHANGED',emitter=self,idx=self.map.layers['track1'].idx)
            self.UpdateDrawing()

    def OnLeftMouseUp(self,event):
        self.dragging=False
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        event.Skip()

    def OnLeftMouseDown(self,event):
        for layer in self.map.layers.values():
            layer.onmousedown(event.GetX(),event.GetY(),1)
        self.dragging=True
        self.x_dragori=event.GetX()
        self.y_dragori=event.GetY()
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.map.update() ## should check wether layer mousedown should trigger redraw!
        self.UpdateDrawing()
        self.Refresh(eraseBackground=False)
        event.Skip() ## enable other event handlers to fire
    
    def OnRightMouseDown(self,event):
        for layer in self.map.layers.values():
            layer.onmousedown(event.GetX(),event.GetY(),3)
        ## if there is no active layer, popup menu
        if not any([l.active for l in self.map.layers.values()]):
            self.PopupMenu(self.rightclickmenu)
        self.map.update(tile=(-1,-1)) ## should check wether layer mousedown should trigger redraw!
        self.UpdateDrawing()
        self.Refresh(eraseBackground=False)
        event.Skip()

    def _tunelayer(self,tgtlayer="track1"):
        if tgtlayer in list(self.map.layers.keys()):
                l=self.map.layers[tgtlayer]
                (l.latkey,l.lonkey,l.headingkey,l.colorkey,l.linewidth,l.trackercolor,\
                 l.anglekey,l.normkey,l.scale)=WxQuery("Options for track",
                    [('wxcombo','Latitude key','|'.join(l.gpx.columns),l.latkey,'str'),\
                     ('wxcombo','Longitude key','|'.join(l.gpx.columns),l.lonkey,'str'),\
                     ('wxcombo','Heading key','|'.join(l.gpx.columns),l.headingkey,'str'),\
                     ('wxcombo','Color key','|'.join(l.gpx.columns),l.colorkey,'str'),\
                     ('wxspin','Line width','1|10|1',l.linewidth,'int'),
                     ('wxcolor','Tracker color',None,l.trackercolor,'int'),
                     ('wxcombo','Vector angle key','|'.join(l.gpx.columns),l.anglekey,'str'),\
                     ('wxcombo','Vector norm key','|'.join(l.gpx.columns),l.normkey,'str'),\
                     ('wxhscale','Vector scale (pixels)','0|70|1|1',l.scale,'int'),
                    ])
                l.anglekey=l.anglekey if l.anglekey in l.gpx.columns else None
                l.normkey =l.normkey  if l.normkey  in l.gpx.columns else None
                l.normmax =np.max(l.norm)  if l.normkey  in l.gpx.columns else 1.0
                self.map.update() ## should check wether layer mousedown should trigger redraw!
                self.UpdateDrawing()
    
    def OnLeftDoubleClick(self,event):
        if not any([l.active for l in self.map.layers.values()]):
            try:
                layers=[layer for layer in self.map.layers.keys() if layer.startswith("track")]
                if len(layers):
                    (tgtlayer,)=WxQuery("Choose layer to tune",
                             [('wxcombo','Layer','|'.join(layers),layers[0],'str')]
                        )
                else:
                    return
            except:
                return
            self._tunelayer(tgtlayer)

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
        self.Refresh(eraseBackground=False)
        event.Skip() ## enable other event handlers to fire
        
    def UpdateDrawing(self):
        self._wxbuffer=wx.Bitmap.FromBuffer(self.map.width,self.map.height, self.map.image.tobytes())
        super().UpdateDrawing()

    def AttachGpx(self,gpx):
        self.map.layers["track1"]=PdPathLayer(self.map,gpx, linewidth=2, dotsize=0.0,followmouse=True)
        self.map.enclose(min(gpx.lat),min(gpx.lon),max(gpx.lat),max(gpx.lon))
        #self.map.lookat(np.mean(gpx.lat),np.mean(gpx.lon),zoom=12)
        self.map.update()
        self.UpdateDrawing()
        self.Refresh()

    def DetachGpx(self):
        ## maps may have several track layer.
        ## this enables to follow several tracks at the same time with same timestamps
        ## a utility is provided to combine several files while preserving or resetting timestamps
        if 1:
            keys=list(self.map.layers.keys())
            for k in keys:
                if k.startswith('track'):
                    self.map.layers[k].gpx=None
                    del self.map.layers[k]
        else:
            pass
        self.map.update()
        self.UpdateDrawing()
        self.Refresh()

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
            services=json.loads(open("wxgpx_settings.json").read())["mapsrc"]
            self.MapPanel = WxMapPanel(self,services=services)
            self.MapPanel.map.layers['scalebar']=GeoScaleLayer(self.MapPanel.map)
            self.MapPanel.map.layers['measure']=GeoWaypointLayer(self.MapPanel.map,
                                                                           [],[],
                                                                           [(255,255,255)],
                                                                           linewidth=3,
                                                                           dotsize=10
                                                                           )
            track=gpxutils.parsefitfile("data/windsurf.fit")
            #self.MapPanel.map.layers['track1']=PdPathLayer(self.MapPanel.map,track, linewidth=2, dotsize=0.0)
            #self.MapPanel.map.lookat(np.mean(track.lat),np.mean(track.lon),zoom=12)
            #self.MapPanel.UpdateDrawing()
            self.MapPanel.AttachGpx(track)
                
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
