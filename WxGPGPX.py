#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os,sys,pathlib
def thispath():   
    return pathlib.Path(sys.executable).parent if getattr(sys, 'frozen', False) else pathlib.Path(__file__).parent

if not getattr(sys, "frozen", False):
    import wx.py
    import wx.grid

sys.path.insert(0,str(thispath()/"modules"))
sys.path.insert(0, str(thispath()/"plugins"))
sys.path.insert(0, str(thispath()/"scripts"))

import warnings
warnings.filterwarnings("ignore")
import logging
import json
import pathlib
from itertools import cycle
import wx
import wx.aui 
import wx.adv
from PIL import ImageDraw,ImageFont
import pandas as pd
import numpy as np
import gpxutils
import msgwrap
from pilmap import *
from WxMapPanel import *
from WxTimePanel import *
from WxStatusBar import *
from WxButtonBitmap import *
import units as un

if __name__=='__main__':  
        
    class MainFrameDropTarget(wx.FileDropTarget):
        def __init__(self, window):
            wx.FileDropTarget.__init__(self)
            self.window = window

        def OnDropFiles(self, x, y, filenames):
            for filepath in filenames:
                #wx.GetApp().frame.OpenFile(filepath)
                frame=wx.GetApp().frame
                frame.AttachGpx(frame.OpenFile(filepath))
            return True
            
    class MainFrame(wx.Frame):
        def __init__(self, parent=None):
            wx.Frame.__init__(self, parent,
                            size = (1000,500),
                            title="WxGPX",
                            style=wx.DEFAULT_FRAME_STYLE)

            ## Set up the MenuBar
            self.InitMenus()
            ## parsing config with comments
            try:
                #self.cfg=json.loads(open(pathlib.Path.home()/".wxgpx_settings.json").read())
                with open(pathlib.Path.home()/".wxgpx_settings.json",'r') as f: 
                    self.cfg = json.loads('\n'.join(row for row in f if not row.lstrip().startswith("//")))
            except:
                #self.cfg=json.loads(open(thispath()/"wxgpx_settings.json").read())
                with open(thispath()/"wxgpx_settings.json",'r') as f: 
                    self.cfg = json.loads('\n'.join(row for row in f if not row.lstrip().startswith("//")))
                ## todo dump default configuration file
            hsplitter=wx.SplitterWindow(self,style=wx.SP_3D|wx.SP_3DSASH|wx.SP_BORDER|wx.SP_LIVE_UPDATE)
            vsplitter=wx.SplitterWindow(hsplitter,style=wx.SP_3D|wx.SP_3DSASH|wx.SP_BORDER|wx.SP_LIVE_UPDATE)
            hsplitter.SetSashGravity(0.666)
            vsplitter.SetSashGravity(0.500)
            self.TimePanel=WxTimePanel(hsplitter)
            self.PluginPanel=wx.aui.AuiNotebook(vsplitter,style=wx.aui.AUI_NB_DEFAULT_STYLE&~(wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB))
            self.MapPanel = WxMapPanel(vsplitter,services=self.cfg["mapview"]['services'],
                                       service=self.cfg["mapview"]['service'],
                                       useragent=self.cfg["mapview"]['useragent'],
                                       numthreads=self.cfg["mapview"]['numthreads'],
                                       cachedir=self.cfg["mapview"]['cachedir']
                                       )
            self.MapPanel.map.layers['scalebar']=GeoScaleLayer(self.MapPanel.map)
            self.MapPanel.map.layers['measure']=GeoWaypointLayer(self.MapPanel.map,
                                                                           [],[],
                                                                           [(255,255,255)],
                                                                           linewidth=3,
                                                                           dotsize=10
                                                                           )
            self.MapPanel.map.layers['gates']=GeoWaypointLayer(self.MapPanel.map,
                                                                           [],[],
                                                                           [(255,00,00)],
                                                                           linewidth=3,
                                                                           dotsize=10,
                                                                           dashed=True,
                                                                           numbers=True
                                                                           )
            filedroptarget=MainFrameDropTarget(self)
            self.MapPanel.SetDropTarget(filedroptarget)
            self.TimePanel.SetDropTarget(filedroptarget)
            self.InitPlugins()
            hsplitter.SplitHorizontally(vsplitter, self.TimePanel)
            vsplitter.SplitVertically(self.MapPanel, self.PluginPanel)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(hsplitter, 1, wx.EXPAND)
            self.SatusBar=StatusBarPanel(self)
            self.SetStatusBar(self.SatusBar)
            self.SetSizer(sizer)
            ## we define the following messages:
            # "INDEX_CHANGED"     param (idx) when mouse moves. Updates the cursor potition on map/graphs
            # "SELECTION_CHANGED" param ( - ) when the gpx.ok column has changed. refresh map and/or graphs
            # "DATA_CHANGED"      param ( - ) when data has changed (either deleted parts or user edited)
            # "APP_MESSAGE"       param ( {"msg":message type,...} ) any other usefull message
            msgwrap.register(self.MapPanel.OnIndexChanged,'INDEX_CHANGED')
            msgwrap.register(self.MapPanel.OnSelectionChanged,'SELECTION_CHANGED')
            msgwrap.register(self.MapPanel.OnDataChanged,'DATA_CHANGED')
            msgwrap.register(self.MapPanel.OnAppMessage,'APP_MESSAGE')
            msgwrap.register(self.TimePanel.OnIndexChanged,'INDEX_CHANGED')
            msgwrap.register(self.TimePanel.OnSelectionChanged,'SELECTION_CHANGED')
            msgwrap.register(self.TimePanel.OnDataChanged,'DATA_CHANGED')
            msgwrap.register(self.MapPanel.OnAppMessage,'APP_MESSAGE')
            msgwrap.register(self.SatusBar.OnIndexChanged,'INDEX_CHANGED')
            msgwrap.register(self.SatusBar.OnSelectionChanged,'SELECTION_CHANGED')
            msgwrap.register(self.SatusBar.OnDataChanged,'DATA_CHANGED')
            self.replaytimer=None
            self.Show()

        def InitPlugins(self):
            self.plugins={}
            pluginlist=[f for f in (thispath()/"plugins").glob('[!_]*.py')]
            for f in sorted(pluginlist):
                if not f.stem in self.cfg['general']['plugins']:
                    continue
                pluginargs={'appdir':thispath(),
                            'plugindir':thispath()/"plugins",
                            'scriptdir':thispath()/"scripts",
                            }
                pluginargs.update(self.cfg)
                self.plugins[f.stem] = __import__(f.stem).Plugin(self.PluginPanel,
                                                               MapPanel=self.MapPanel,
                                                               TimePanel=self.TimePanel,
                                                               cfg=pluginargs)
                self.PluginPanel.AddPage(self.plugins[f.stem],self.plugins[f.stem].GetName(),False)
                msgwrap.register(self.plugins[f.stem].OnIndexChanged,'INDEX_CHANGED')
                msgwrap.register(self.plugins[f.stem].OnSelectionChanged,'SELECTION_CHANGED')
                msgwrap.register(self.plugins[f.stem].OnDataChanged,'DATA_CHANGED')
            
        def InitMenus(self):
            menubar = wx.MenuBar()
            self.filemenu = wx.Menu()
            item = self.filemenu.Append(wx.ID_OPEN, "&Open\tCTRL+O")
            self.Bind(wx.EVT_MENU, self.OnOpenMenu, item)
            item = self.filemenu.Append(wx.ID_CLOSE, "&Close\tCTRL+W")
            self.Bind(wx.EVT_MENU, self.OnCloseMenu, item)
            item = self.filemenu.Append(wx.ID_SAVEAS, "&Save as...\tCTRL+S")
            self.Bind(wx.EVT_MENU, self.OnSaveMenu, item)
            item = self.filemenu.Append(wx.ID_EXIT, "Quit","Quit application")
            self.Bind(wx.EVT_MENU, lambda e:os._exit(0), item)
            menubar.Append(self.filemenu, "&File")
            self.editmenu = wx.Menu()
            item = self.editmenu.Append(wx.ID_UNDO, "&Undo\tCTRL+Z")
            item.Enable(False)
            item = self.editmenu.Append(wx.ID_REDO, "&Redo\tCTRL+SHIFT+Z")
            item.Enable(False)
            self.editmenu.AppendSeparator()
            item = self.editmenu.Append(wx.ID_CUT, "&Cut\tCTRL+X")
            item.Enable(False)
            item = self.editmenu.Append(wx.ID_COPY, "&Copy\tCTRL+C")
            item.Enable(False)
            item = self.editmenu.Append(wx.ID_PASTE, "&Paste\tCTRL+V")
            item.Enable(False)
            item = self.editmenu.Append(wx.ID_SELECTALL, "&Select All\tCTRL+A")
            item.Enable(False)
            menubar.Append(self.editmenu, "&Edit")
            self.gpxmenu = wx.Menu()
            item = self.gpxmenu.Append(wx.ID_ANY, "&Replay\tCTRL+R",kind=wx.ITEM_CHECK)
            self.Bind(wx.EVT_MENU, self.OnReplayMenu, item)
            item = self.gpxmenu.Append(wx.ID_ANY, "&Units\tCTRL+U")
            self.Bind(wx.EVT_MENU, self.OnUnitMenu, item)
            item.Enable(True)
            menubar.Append(self.gpxmenu, "&Gpx")
            self.SetMenuBar(menubar)

        def OnSaveMenu(self,event):
            wildcard = "GPX XML file (*.gpx)|*.gpx|"+\
                        "csv file (*.csv)|*.csv|"+\
                        "compressed csv file (*.csv.gz)|*.csv.gz|"+\
                        "tsv file (*.tsv)|*.tsv|"+\
                        "compressed tsv file (*.tsv.gz)|*.tsv.gz"
            dialog = wx.FileDialog(None, "Choose a file", os.getcwd(), "", wildcard, wx.FD_SAVE)
            if dialog.ShowModal() == wx.ID_OK:
                fname=pathlib.Path(dialog.GetPath())
                if fname.suffix.lower() in ['.csv','.csv.gz']:
                    columns=[c for c in self.gpx.columns if not c in 'deltaxy|heading|speed|awaa|awar|aws|upwind|uwa|vmg|deltat|seconds|ok|idx'.split('|')]
                    self.gpx.to_csv(fname,
                                    sep=",",
                                    columns=columns,
                                    date_format="%Y-%m-%dT%H:%M:%SZ")
                if fname.suffix.lower() in ['.tsv','.tsv.gz']:
                    columns=[c for c in self.gpx.columns if not c in 'deltaxy|heading|speed|awaa|awar|aws|upwind|uwa|vmg|deltat|seconds|ok|idx'.split('|')]
                    self.gpx.to_csv(fname,
                                    sep="\t",
                                    columns=columns,
                                    date_format="%Y-%m-%dT%H:%M:%SZ")
                if fname.suffix.lower()=='.gpx':
                    gpxutils.savegpxfile(self.gpx,str(fname))
                    
        def SaveFile(self,fname):
            fpath=pathlib.Path(fname)
            if fpath.suffix.lower() in ['.csv','.csv.gz']:
                self.gpx.drop(columns=['ok']).to_csv(fpath,sep=",",date_format="%Y-%m-%dT%H:%M:%SZ")
            if fpath.suffix.lower() in ['.tsv','.tsv.gz']:
                self.gpx.drop(columns=['ok']).to_csv(fpath,sep="\t",date_format="%Y-%m-%dT%H:%M:%SZ")
            if fpath.suffix.lower()=='.gpx':
                gpxutils.savegpxfile(self.gpx.drop(columns=['ok']),str(fpath))
            
        def OnOpenMenu(self,event):
            wildcard = "Any compatible file|*.fit;*.gpx;*.gpx;*.csv;*.csv.gz;*.tsz;*.tsv.gz|"+\
                        "Fit file (*.fit)|*.fit|"+\
                        "GPS Exchange (*.gpx,*.gpx.gz)|*.gpx;*gpx.gz|"+\
                        "csv file (*.csv)|*.csv|"+\
                        "compressed csv file (*.csv.gz)|*.csv.gz|"+\
                        "tsv file (*.tsv)|*.tsv|"+\
                        "compressed tsv file (*.tsv.gz)|*.tsv.gz|"+\
                        "Compressed Numpy Array (*.npz)|*.npz"
            dialog = wx.FileDialog(None, "Choose a file", os.getcwd(), "", wildcard, wx.FD_OPEN)
            if dialog.ShowModal() == wx.ID_OK:
                self.AttachGpx(self.OpenFile(dialog.GetPath()))

        def OpenFile(self,fname,resample='prompt',**kwargs): ## 'prompt','auto','skip','1s',2s'
            fpath=pathlib.Path(fname)
            if fpath.suffix.lower()=='.fit':
                gpx=gpxutils.parsefitfile(str(fpath))
            if fpath.suffix.lower()=='.gpx':
                gpx=gpxutils.parsegpxfile(str(fpath),**kwargs)
            elif fpath.suffix.lower() in ['.csv','.csv.gz']:
                try:
                    gpx=pd.read_csv(fpath,sep=',',
                                     parse_dates=['time'],
                                     date_format="%Y-%m-%dT%H:%M:%SZ")
                except:
                    gpx=pd.read_csv(fpath,sep=',',
                                     parse_dates=['time'],
                                     #date_format="%Y-%m-%dT%H:%M:%SZ"
                                     )

            elif fpath.suffix.lower() in ['.tsv','.tsv.gz']:
                try:
                    gpx=pd.read_csv(fpath,sep='\t',
                                     parse_dates=['time'],
                                     date_format="%Y-%m-%dT%H:%M:%SZ")
                except:
                    gpx=pd.read_csv(fpath,sep='\t',
                                     parse_dates=['time'],
                                     #date_format="%Y-%m-%dT%H:%M:%SZ"
                                     )
            try:
                ## in order to avoid conversions between pd.Timestamps, numpy datetimes, etc...
                gpx['time']=pd.to_datetime(gpx['time'],utc=True)
                ## asssert if resampling is required
                deltas=np.ediff1d(  (gpx.time-gpx.time.iloc[0]).dt.total_seconds().astype(int)  )
                if resample!='skip' and len(set(deltas))>1 or resample.endswith("s"):
                    if resample=='prompt':
                        if wx.MessageBox("There are missing points. This file needs to be resampled.\n",
                                                "Confirm",
                                                wx.YES_NO | wx.NO_DEFAULT)==wx.YES:
                            gpx=gpxutils.resample(gpx)
                    else:
                        dt=None if resample=='auto' else resample
                        force=False if resample=='auto' else True
                        gpx=gpxutils.resample(gpx,dt=dt,force=force)

                ## rename columns to discard 'gpxtpx:' and gpxdata: prefix in gpx files
                gpx.rename(columns={c:c.split(':')[-1] for c in gpx.columns if ':' in c},inplace=True)
                ## drop and/or rename unwanted fields
                gpx=gpx.rename(columns={k:v for k,v in self.cfg['general']['transtable'].items() if not v is None})
                gpx=gpx.drop(columns=[k for k,v in self.cfg['general']['transtable'].items() if v is None],errors='ignore')
                ## there are a few fields that are calculated if they could not be found
                if 'deltat' not in gpx.columns:
                    try:
                        gpx['deltat']=gpxutils.duration(gpx.time).apply(lambda x:x.total_seconds())
                    except:
                        gpx['deltat']=gpxutils.duration(gpx.time).apply(lambda x:pd.Timedelta(x).total_seconds())
                ## create some fields that will be required for calculations
                gpx['ok']=True
                gpx['idx']=range(len(gpx.lat))
                gpx['seconds']=np.cumsum(gpx.deltat)
                gpx['deltaxy']=gpxutils.hv_distance(gpx.lat,gpx.lon)
                if 'ele' in gpx.columns:
                    gpx['deltaz']=np.append(np.ediff1d(gpx.ele), np.nan)
                    gpx['ascspeed']=gpx.deltaz/gpx.deltat
                gpx['heading']=(gpxutils.heading(gpx.lat,gpx.lon)-180)%360
                gpx['distance']=np.cumsum(gpx['deltaxy'])
                if 'speed' not in gpx.columns:
                    logging.getLogger().info("Your file does not have any speed information.")
                    logging.getLogger().info("The calculated speed may be inaccurate. due to relative gps precision.")
                    logging.getLogger().info("It is recommanded to smooth your data using the shell plugin.")
                    logging.getLogger().info(">>> gpx['speed'[:]=np.convolve(gpx.speed,np.ones(3)/3,mode='same')")
                    gpx['speed']=gpx.deltaxy / gpx.deltat
                    ## some corrections are easy to implement
                gpx['speed'][gpx.speed<0]=0.0
                ## fill nan introduced by previous calculations. Theoretically, all nan should be on last point!
                #gpx.fillna(method='bfill',inplace=True) ## remove any nan introduced by previous calculations
                gpx.fillna(method='ffill',inplace=True) ## remove any nan introduced by previous calculations
                ## rearrange columns for table plugin
                order=[c for c in ['ok','idx','time','lat','lon','distance','seconds','speed','heading','ele','deltat','deltaxy','deltaz','ascspeed'] if c in gpx.columns]
                neworder=order+[c for c in gpx.columns if not c in order]
                gpx=gpx[neworder]
                ##attach units to gpx
                gpx.deltat.unit.use(un.s)
                gpx.seconds.unit.use(un.s)
                gpx.speed.unit.use(un.ms)
                gpx.deltaxy.unit.use(un.m)
                if 'ele' in gpx.columns:
                    gpx.ele.unit.use(un.m)
                    gpx.deltaz.unit.use(un.m)
                gpx.heading.unit.use(un.deg)
                gpx.lat.unit.use(un.deg)
                gpx.lon.unit.use(un.deg)
                gpx.distance.unit.use(un.m)
                ## see if there are some user defined units
                for k,v in self.cfg["general"]["units"].items():
                    if k in gpx.columns:
                        gpx[k].unit.use(v)
                return gpx
            except:
                logging.getLogger().critical("Something weird happened while trying to open file!")
                return None
                
        def AttachGpx(self,gpx):
            ## Detach
            for name,plugin in self.plugins.items():
                plugin.DetachGpx()
            self.TimePanel.DetachGpx()
            self.MapPanel.DetachGpx()
            self.StatusBar.DetachGpx()
            self.gpx=None
            if gpx is None:
                return
            ## Attach again
            self.gpx=gpx
            for name,plugin in self.plugins.items():
                plugin.AttachGpx(self.gpx) 
            self.TimePanel.AttachGpx(self.gpx)
            self.MapPanel.AttachGpx(self.gpx)
            self.StatusBar.AttachGpx(self.gpx)
            self.gpxmenu.Enable(self.gpxmenu.FindItem("Replay"),True)
            self.gpxmenu.Enable(self.gpxmenu.FindItem("Units"),True)

        def OnCloseMenu(self,event):
            for name,plugin in self.plugins.items():
                plugin.DetachGpx()
            self.TimePanel.DetachGpx()
            self.MapPanel.DetachGpx()
            self.StatusBar.DetachGpx()
            self.gpx=None
            self.gpxmenu.Enable(self.gpxmenu.FindItem("Replay"),False)
            self.gpxmenu.Enable(self.gpxmenu.FindItem("Units"),False)
            msgwrap.message("DATA_CHANGED",emitter=self)

        def OnReplayMenu(self,event):
            if not self.replaytimer:
                (speed,)=WxQuery("Replay speed: x",[("wxentry","Replay interval (ms)",None,"100",'int')])
                self.replayindices=cycle(np.where(self.gpx.ok)[0].tolist())
                self.replaytimer=wx.Timer(self)
                self.Bind(wx.EVT_TIMER,
                          lambda e:msgwrap.message("INDEX_CHANGED",emitter=self,idx=next(self.replayindices)),
                          self.replaytimer)
                self.replaytimer.Start(speed)
                msgwrap.message("APP_MESSAGE",emitter=self,data={'msg':'replay','value':True})
            else:
                self.replaytimer.Stop()
                self.replaytimer=None
                msgwrap.message("APP_MESSAGE",emitter=self,data={'msg':'replay','value':False})
            
        def OnUnitMenu(self,event):
            if not self.gpx is None:
                keys=[k for k in self.gpx.columns if k not in ['time', 'lat','lon','seconds','idx','ok']]
                res=WxQuery('Units',
                    [('wxcombo',f"{k}",'|'.join(un.unit_dict.keys()),self.gpx[k].unit.sym,'str') for k in keys]
                )
            for k,r in zip(keys,res):
                try:
                    self.gpx[k].unit.use(r)
                except:
                    pass
                msgwrap.message("DATA_CHANGED",emitter=self) 

    class GpxApp(wx.App):  
        def OnInit(self):
            self.frame = MainFrame()
            self.SetTopWindow(self.frame)
            return True

    import matplotlib.font_manager as fm
    font_path = fm.findfont('DejaVu Sans') ##unless you provide a valid font name, returns the DejaVuSans.ttf used by matplotlib
    ImageDraw.ImageDraw.font = ImageFont.truetype(font_path,size=15)
    app = GpxApp(0)
    app.MainLoop()
    exit(0)
