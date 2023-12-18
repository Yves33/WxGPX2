#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import warnings
warnings.filterwarnings("ignore")
import wx
from units import *

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib.dates as dates
import matplotlib.patches as patches
import msgwrap
import numpy as np
import pandas as pd
import gpxutils
from flexpanzoom import PanZoomFactory
from wxquery import WxQuery

def _numeric(d):
    def isstamp(d):
        try:
            return (len(d)>0 and isinstance(d[0],pd.Timestamp)) or \
                    d.dtype=='datetime64[ns, UTC]' or \
                    d.dtype=='datetime64[ns]' or \
                    d.dtype=='<M8[ns]'
        except:
            return False

    return dates.date2num(d) if isstamp(d) else d

defaultlineprops={'linewidth':1,\
                'marker':'.',\
                'markersize':0,\
                'color':'#990000',\
                'smooth':1,
                'fill':False,
                'fillalpha':0.2,
                'autoscale':True}  


class WxLineScatterWidget(wx.Panel):
    def __init__(self, *args, **kwargs):
        kwargs['style'] = kwargs.setdefault('style', wx.NO_FULL_REPAINT_ON_RESIZE) | wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Panel.__init__(self, *args, **kwargs)
        self.plot1=None
        self.plot2=None
        self.xaxis=None
        self.lineprops1=defaultlineprops.copy()
        self.lineprops1.update({'color':'#990000','fill':True})
        self.lineprops2=defaultlineprops.copy()
        self.lineprops2.update({'color':'#009900','fill':True})
        self.autoy1=True
        self.autoy2=True
        self.press=False
        self.cursor=None
        self.span=None
        self.selstart=None
        self.selstop=None
        self.enablecursor=True
        self.enablespan=True
        self.cursorcolor='#FF0000'
        self.cursorwidth=1
        self.autoscale=False
        self.reportindex=True

        self.gpxfig = Figure(figsize=(1.5,1))
        self.ax1 = self.gpxfig.add_subplot(1,1,1)           # create a grid of 1 row, 1 col and put a subplot in the first cell of this grid
        self.ax2=self.ax1.twinx()
        
        ## canvas and events
        #self.pz=PanZoomFactory()
        self.gpxcanvas=FigureCanvas(self,-1,self.gpxfig)
        self.gpxcanvas.SetMinSize((75,50))     ##required due to bug in wx.Backend!
        self.gpxcanvas.SetMaxSize((2000,2000)) 
        ## in order to use the wxPanZoom factory, a proper canvas has to be created before!
        ## factory can then be created using either canvas or figure
        ## one can switch from figure to canvas using figure.canvas and canvas.figure
        self.pz=PanZoomFactory(self.gpxfig,
                                 #rightclickpopup=True,
                                 zoomstr="\uf010 \uf00e",
                                 zoomstrfont=FontProperties(fname=r"./modules/fa/fontawesome/Font Awesome 6 Free-Solid-900.otf"),
                                 zoomstrsize=12,
                                 )
    
        ## chain
        self.gpxcanvas.mpl_connect('button_press_event', self.OnLeftMouseDown)
        self.gpxcanvas.mpl_connect('button_release_event', self.OnLeftMouseUp)
        self.gpxcanvas.mpl_connect('motion_notify_event', self.OnMouseMotion)
        self.gpxcanvas.mpl_connect('resize_event', self.OnSize)
        self.gpxcanvas.mpl_connect('draw_event', self.OnDraw)
        
        ## wxPython events not required!
        #self.Bind(wx.EVT_RIGHT_DOWN,self.OnRightMouseDown)
        #self.Bind(wx.EVT_SIZE,self.OnSize)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.gpxcanvas, 1, wx.LEFT|wx.TOP|wx.GROW|wx.EXPAND)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        color=wx.Colour(255,255,255)
        self.gpxfig.set_facecolor((1,1,1))
        self.gpxfig.set_edgecolor((1,1,1))
        self.gpxfig.set_edgecolor((0.0, 0.0, 0.0))
        self.gpxcanvas.SetBackgroundColour(wx.Colour(255,255,255))
        
		# create right now the popup menu
        self.select_menu = wx.Menu()
        for text in ["Disable selected",\
                            "Enable selected",\
                            "Delete selected",\
                            "Disable non selected",\
                            "Enable non selected",\
                            "Delete non selected",\
                            "Toggle points",\
                            "Enable all"
                            ]:
            item = self.select_menu.Append(-1,text)
            self.Bind(wx.EVT_MENU, self.OnPopup, item)

    def OnIndexChanged(self,emitter,idx):
        if emitter!=self:
            self.cursor.set_xdata([self.ax1.get_lines()[0].get_data()[0][idx]])
            self.Draw(True)

    def OnSelectionChanged(self,emitter):
        if emitter!=self:
            self.update_axis(self.ax1,self.plot1,self.lineprops1,xaxis=None)
            self.update_axis(self.ax2,self.plot2,self.lineprops2,xaxis=None)
            self.Draw(False)

    def OnDataChanged(self,emitter):
        if emitter!=self:
            if not self.gpx is None:
                self.update_axis(self.ax1,self.plot1,self.lineprops1,xaxis=None)
                self.update_axis(self.ax2,self.plot2,self.lineprops2,xaxis=None)
                self.Draw(False)

    def OnAppMessage(self,emitter,data):
        if emitter!=self:
            if data['msg']=='replay':
                self.reportindex=not data['value']

    def format_x_axis(self):
        if isinstance(self.ax1.get_lines()[0].get_data()[0][0],pd.Timestamp):
            self.ax1.xaxis.set_major_formatter(dates.DateFormatter("%H:%M:%S"))
            self.ax1.set_xlabel(self.xaxis+' (HH:MM:SS)')
        else:
            self.ax1.set_xlabel(self.xaxis+' ('+self.gpx[self.xaxis].unit.sym+')')
            self.ax1.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())

    def get_selection(self):
        if not self.gpx is None and\
            self.span.get_visible() and\
            self.selstart<self.selstop:
            return (self.selstart,self.selstop)
        else:
            return (None,None)

    def update_axis(self,ax,plot,lineprops,xaxis=None):
        if plot in self.gpx.columns:
            smooth=lineprops['smooth']
            if smooth>1:
                ydata=(1.0)*np.convolve(self.gpx[plot].unit.scaled, np.ones((smooth,))/smooth)[(smooth-1):] ## to be scaled
            else:
                ydata=self.gpx[plot].unit.scaled.copy()                                                     ## to be scaled
            ydata[~self.gpx.ok]=np.nan
            #remove fill_between collection
            for coll in ax.collections:
                try:
                    ax.collections.remove(coll)
                except:
                    coll.remove()
            if xaxis is None:
                xdata=ax.get_lines()[0].get_data()[0]
            else:## todo xaxis has changed. make sure that x axis is monotonically increasing
                xdata=self.gpx[xaxis].unit.scaled
            ax.get_lines()[0].set_data(xdata,ydata)
            if not xaxis is None or self.autoscale:
                ax.set_xlim(min(xdata),max(xdata))
            if lineprops['fill']:
                ax.fill_between(xdata,0,ydata,facecolor=lineprops['color'], alpha=0.2)
            ax.get_lines()[0].set_color(lineprops['color'])
            ax.tick_params(axis='y', colors=lineprops['color'])
            ax.yaxis.label.set_color(lineprops['color'])
            ax.get_lines()[0].set_linewidth(lineprops['linewidth'])
            ax.get_lines()[0].set_marker(lineprops['marker'])
            ax.get_lines()[0].set_markersize(lineprops['markersize'])
            ax.set_ylabel(plot+' ('+self.gpx[plot].unit.sym+')')
            if lineprops['autoscale']:
                ax.set_ylim(min(ydata),max(ydata))
            self.format_x_axis()
            ax.set_visible(True)
        else:
            ax.set_visible(False)
        self.cursor.set_color(self.cursorcolor)
        self.cursor.set_linewidth(self.cursorwidth)
        self.gpxcanvas.draw()
        self.Draw(True)
           
    def AttachGpx(self,data=None):
        if not data is None:
            self.gpx=data
        self.xaxis='time'
        self.plot1='speed'
        self.plot2=None
        self.ax1.plot(self.gpx[self.xaxis].unit.scaled,self.gpx[self.plot1].unit.scaled,picker=5)          ## to be u_scaled
        self.ax1.set_ylim(self.gpx[self.plot1].unit.scaled.min(),self.gpx[self.plot1].unit.scaled.max())   ## to be u_scaled
        self.ax1.set_xlim(self.gpx[self.xaxis].unit.scaled.min(),self.gpx[self.xaxis].unit.scaled.max())
        self.ax2.plot(self.gpx[self.xaxis].unit.scaled,np.zeros(len(self.gpx)),picker=5)       ## to be u_scaled
        self.ax2.set_visible(False)
        self.ax1.set_xlabel(self.xaxis)
        self.ax1.set_ylabel(self.plot1)
        self.ax2.set_ylabel('')
        self.ax2.yaxis.set_label_position("right")
        self.ax2.yaxis.tick_right()
        self.xaxis=self.xaxis
        self.plot1=self.plot1
        self.plot2=None
        if self.enablecursor==True:
            self.cursor=self.ax1.axvline(x=self.gpx[self.xaxis].mean(),
                                         color='r',
                                         linewidth=1,
                                         animated=True)
        if self.enablespan==True:
            self.span=patches.Rectangle( (self.ax1.get_xlim()[0],0), 0,200, color='k',alpha=0.3,animated=True)
            self.ax1.add_patch(self.span)
            self.span.set_visible(False)
        self.update_axis(self.ax1,self.plot1,self.lineprops1,xaxis=None)
        self.update_axis(self.ax2,'None',self.lineprops2,xaxis=None)

    def DetachGpx(self):
        self.gpx=None
        self.plot1=None
        self.plot2=None
        self.autoy1=True
        self.autoy2=True
        self.fill1=True
        self.fill2=True
        self.xaxis=''
        self.press=False
        if self.cursor!=None:
            self.cursor.remove()
            self.cursor=None
        if self.span!=None:
            self.span.remove()
            self.span=None
        self.ax1.cla()
        self.ax2.cla()
        self.gpxcanvas.draw()
        self.Draw(False)
    
    def OnDraw(self,event):
        self.background = self.gpxcanvas.copy_from_bbox(self.ax1.bbox)
        self.Draw(False)

    def Draw(self,blit):
        if blit:
            self.gpxcanvas.restore_region(self.background)
        if self.span!=None and self.span.get_visible():
            self.ax1.draw_artist(self.span)
        if self.cursor!=None:
            self.ax1.draw_artist(self.cursor)
        if blit:
            self.gpxcanvas.blit()
        
    def OnSize(self,event):
        x,y=self.GetClientSize()
        self.gpxcanvas.resize(x,y)
        self.gpxfig.set_size_inches(float(x)/self.gpxfig.get_dpi(),float(y)/self.gpxfig.get_dpi())
        ## we want bottom clip to be 0.3 when y<150 and 0.1 when y>350
        frac=np.clip( (y-150)/(350-150),0.0,1.0)
        self.gpxfig.subplots_adjust(right=0.9,left=0.1,bottom=0.3-0.2*frac)
        self.gpxcanvas.draw()
        self.Draw(False)
        
    def OnLeftMouseDblClick(self,event):
        (tab,\
        xaxis,self.cursorcolor,self.cursorwidth,self.autoscale,\
        tab,\
        self.plot1,self.lineprops1['smooth'],self.lineprops1['color'],self.lineprops1['linewidth'],\
        self.lineprops1['marker'],self.lineprops1['markersize'],self.lineprops1['fill'],self.lineprops1['autoscale'],\
        tab,\
        self.plot2,self.lineprops2['smooth'],self.lineprops2['color'],self.lineprops2['linewidth'],\
        self.lineprops2['marker'],self.lineprops2['markersize'],self.lineprops2['fill'],self.lineprops2['autoscale'])=\
            WxQuery("Graph Settings",
                [('wxnotebook','X Axis',None,None,None),
                 ('wxcombo','X axis','time|seconds|idx|distance',self.xaxis,'str'),
                 ('wxcolor','Cursor color',None,self.cursorcolor,'str'),
                 ('wxspin','Cursor width','0|6|1',self.cursorwidth,'int'),
                 ('wxcheck','Auto scale',None,self.autoscale,'bool'),

                 ('wxnotebook','Y1 Axis',None,None,None),
                 ('wxcombo','Channel 1','none|'+'|'.join(self.gpx.columns),self.plot1,'str'),
                 ('wxhscale','Smooth','0|12|1|1',self.lineprops1['smooth'],'int'),
                 ('wxcolor','Color',None,self.lineprops1['color'],'str'),
                 ('wxspin','Line width','0|12|1',self.lineprops1['linewidth'],'int'),
                 ('wxcombo','Marker','.|o|+|x|^|4|s|*|D',self.lineprops1['marker'],'str'),
                 ('wxspin','Marker size','0|12|1',self.lineprops1['markersize'],'int'),
                 ('wxcheck','Fill area',None,self.lineprops1['fill'],'bool'),
                 ('wxcheck','Auto scale',None,self.lineprops1['autoscale'],'bool'),

                 ('wxnotebook','Y2 Axis',None,None,None),
                 ('wxcombo','Channel 2','none|'+'|'.join(self.gpx.columns),self.plot2,'str'),
                 ('wxhscale','Smooth','0|12|1|1',self.lineprops1['smooth'],'int'),
                 ('wxcolor','Color',None,self.lineprops2['color'],'str'),
                 ('wxspin','Line width','0|12|1',self.lineprops2['linewidth'],'int'),
                 ('wxcombo','Marker','.|o|+|x|^|4|s|*|D',self.lineprops2['marker'],'str'),
                 ('wxspin','Marker size','0|12|1',self.lineprops2['markersize'],'int'),
                 ('wxcheck','Fill area',None,self.lineprops2['fill'],'bool'),
                 ('wxcheck','Auto scale',None,self.lineprops2['autoscale'],'bool'),
                ])
        if self.xaxis!=xaxis:   #time ax have changed... don't bother and set to full x range
            self.xaxis=xaxis
            self.update_axis(self.ax1,self.plot1,self.lineprops1,xaxis=xaxis)
            self.update_axis(self.ax2,self.plot2,self.lineprops2,xaxis=xaxis)
        else:
            self.update_axis(self.ax1,self.plot1,self.lineprops1)
            self.update_axis(self.ax2,self.plot2,self.lineprops2)
        self.autoscale=False
                   
    def OnLeftMouseDown(self,event):
        #where=self.get_axis(event,self.axis_width)
        #if hasattr(event, 'guiEvent') and int(event.guiEvent.type)==5:
        #calling direcly the dialog may freeze on unix (linux-osX systems) under wx backend
        #workaround   is to release mouse
        #see http://stackoverflow.com/questions/16815695/modal-dialog-freezes-the-whole-application
        #event.guiEvent.GetEventObject().ReleaseMouse() for pick_event
        if event.button==1:
            if event.dblclick:
                try:
                    event.guiEvent.GetEventObject().ReleaseMouse()
                except:
                    pass
                self.OnLeftMouseDblClick(event)
                return
            if event.inaxes and self.span!=None:
                self.span.set_visible(True)
                (self.x0,self.y0)=(event.xdata,event.ydata)
                self.selstart=self.x0
                self.selstop=self.x0
                self.span.set_bounds([event.xdata,
                                  self.ax1.get_ylim()[0],
                                  0,
                                  self.ax1.get_ylim()[1]-self.ax1.get_ylim()[0] ])
                self.press=True

        elif event.button==3 and event.inaxes:
            self.OnRightMouseDown(event)

    def OnLeftMouseUp(self,event):
        if event.inaxes and event.button==1 and self.span!=None and self.press:
            idx1=np.searchsorted(_numeric(self.ax1.get_lines()[0].get_data()[0]),self.x0)
            idx2=np.searchsorted(_numeric(self.ax1.get_lines()[0].get_data()[0]),event.xdata)
            self.selstart=min(idx1,idx2)
            self.selstop=max(idx1,idx2)
            if self.selstart==self.selstop or self.selstart is None:
                self.span.set_visible(False)
            self.press=False
    
    def OnRightMouseDown(self,event):
        #may be necessary in some OSes
        event.guiEvent.GetEventObject().ReleaseMouse()
        disabled= self.selstart==self.selstop or self.selstart is None
        for item in ["Disable selected","Enable selected","Delete selected",\
                "Disable non selected","Enable non selected","Delete non selected",\
                "Toggle points"]:
            self.select_menu.Enable(self.select_menu.FindItem(item),not disabled)
        # on some OS (and depending on wxPython/wxWidgets version, calling
        # wx.PopupMenu will fail unless it is called after matplotlib handler has returned
        # for some magic reason, we do not need to specify wx.Point(event.x, event.y) in parameterss
        #self.PopupMenu(self.select_menus)
        wx.CallAfter(self.PopupMenu,self.select_menu)
            
    def OnMouseMotion(self,event):
        if event.inaxes and self.press:
            self.span.set_bounds(self.x0,\
                                self.ax1.get_ylim()[0],\
                                event.xdata-self.x0,\
                                self.ax1.get_ylim()[1]-self.ax1.get_ylim()[0])
            self.Draw(True)
        elif event.inaxes and self.cursor!=None and self.reportindex:
            xvalues=_numeric(self.ax1.get_lines()[0].get_data()[0])
            xvalues[~self.gpx.ok]=np.inf ## mask out invalid
            idx=np.abs(xvalues-event.xdata).argmin()
            self.cursor.set_xdata([xvalues[idx]])
            msgwrap.message('INDEX_CHANGED',emitter=self,idx=idx)
            self.Draw(True)

    def OnMouseEnter(self,event):
        self.SetFocus()                 # stupid bug in wxSplitterWindow, mouse wheel is always send to the same panel in wxSplittedWIndow
        
    def OnMouseLeave(self,event):
        wx.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    def OnPopup(self, event):
        item = self.select_menu.FindItemById(event.GetId())
        text = item.GetItemLabelText()
        if text=="Disable selected":
            self.gpx['ok'][self.selstart:self.selstop]=False
            xaxis=None
            msgwrap.message("SELECTION_CHANGED",emitter=self)
        if text=="Enable selected":
            self.gpx['ok'][self.selstart:self.selstop]=True
            xaxis=None
            msgwrap.message("SELECTION_CHANGED",emitter=self)
        if text=="Disable non selected":
            self.gpx['ok'][:self.selstart]=False
            self.gpx['ok'][self.selstop:]=False
            xaxis=None
            msgwrap.message("SELECTION_CHANGED",emitter=self)
        if text=="Enable non selected":
            self.gpx['ok'][:self.selstart]=True
            self.gpx['ok'][self.selstop:]=True
            xaxis=None
            msgwrap.message("SELECTION_CHANGED",emitter=self)
        if text=="Delete selected":
            if wx.MessageDialog(None, "Delete Points...?",\
                                'Are you sure you want to delete these points',\
                                wx.YES_NO | wx.ICON_QUESTION).ShowModal()==wx.ID_YES:
                self.gpx.drop(self.gpx.index[range(max(0,self.selstart), min(self.selstop,len(self.gpx)))], inplace=True)
                self.selstart,self.selstop=None,None
                self.idx=0
                xaxis=self.xaxis  ## force updating x values
                self.span.set_visible(False)
                self.gpx.reset_index(inplace=True)
                ## need to replot
                self.ax1.cla()
                self.ax2.cla()
                self.AttachGpx(None)
                msgwrap.message("DATA_CHANGED",emitter=self)
        if text=="Delete non selected":
            if wx.MessageDialog(None, "Delete Points...?",\
                                'Are you sure you want to delete these points',\
                                wx.YES_NO | wx.ICON_QUESTION).ShowModal()==wx.ID_YES:
                self.gpx.drop(self.gpx.index[ list(range(0,self.selstart))+list(range(self.selstop,len(self.gpx)))
                                            ], inplace=True)
                xaxis=self.xaxis  ## force updating x values
                self.selstart,self.selstop=None,None
                self.idx=0
                self.span.set_visible(False)
                self.gpx.reset_index(inplace=True)
                self.ax1.cla()
                self.ax2.cla()
                self.AttachGpx(None)
                msgwrap.message("DATA_CHANGED",emitter=self)
        if text=="Toggle points":
            self.gpx['ok'][:]=~self.gpx['ok']
            xaxis=None
            msgwrap.message("SELECTION_CHANGED",emitter=self)
        if  text=="Enable all":
            self.gpx['ok'][:]=True
            xaxis=None
            msgwrap.message("SELECTION_CHANGED",emitter=self)
            
        self.update_axis(self.ax1,self.plot1, self.lineprops1,xaxis)
        self.update_axis(self.ax2,self.plot2, self.lineprops2,xaxis)
        #msgwrap.message("SELECTION_CHANGED",emitter=self)

    
class WxTimePanel(WxLineScatterWidget):
    def __init__(self, *args, **kwargs):
        WxLineScatterWidget.__init__(self, *args, **kwargs)


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
            self.TimePanel = WxTimePanel(self)
            track=gpxutils.parsefitfile("data/windsurf.fit")
            self.TimePanel.AttachGpx(track)
            self.TimePanel.OnSize(None)    
            self.Show()

    class DemoApp(wx.App):
        def OnInit(self):
            frame = TestFrame()
            self.SetTopWindow(frame)
            return True

    app = DemoApp(0)
    app.MainLoop()
    exit(0)

