#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

## system imports
import wx
import wx.grid
import numpy as np
from units import attrs_save,attrs_load
from wxquery import WxQuery
import msgwrap

rowshift=0

class WxGpxTable(wx.grid.GridTableBase):
    def __init__(self,gpx):
        wx.grid.GridTableBase.__init__(self)
        self.gpx=gpx
        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()
        
    def GetColLabelValue(self, col):
        return self.gpx.columns[col]

    def GetNumberRows(self):
        return len(self.gpx)

    def GetNumberCols(self):
        return len(self.gpx.columns)

    def GetValue(self, row, col):
        try:
            if self.gpx.dtypes[col]==np.dtype('bool'):
                return "1" if self.gpx[self.gpx.columns[col]].iloc[row-rowshift] else ""
            return self.gpx[self.gpx.columns[col]].unit.scaled.iloc[row-rowshift]
        except:
            return None
    
    def GetTypeName(self, row, col):
        try:
            if col>=len(self.gpx.columns):
                raise IndexError
            if self.gpx.dtypes[col]==np.dtype('bool'):
                return wx.grid.GRID_VALUE_BOOL
            elif self.gpx.dtypes[col]==np.dtype('float'):
                return wx.grid.GRID_VALUE_FLOAT
            elif self.gpx.dtypes[col]==np.dtype('int'):
                return wx.grid.GRID_VALUE_NUMBER
            else: # should check for np.datetime64?
                return wx.grid.GRID_VALUE_STRING
        except IndexError:
            return None
        
    def SetValue(self, row,col,value):
        if "u_scale" in self.gpx[self.gpx.columns[col]].attrs.keys():
             _scale=self.gpx[self.gpx.columns[col]].attrs["u_scale"]
        else:
            _scale=1
        try:
            if self.gpx.dtypes[col]==np.dtype('bool'):
                self.gpx[self.gpx.columns[col]].iloc[row-rowshift]=bool(value)
            elif self.gpx[self.gpx.columns[col]].dtype==np.dtype('float'):
                self.gpx[self.gpx.columns[col]].iloc[row-rowshift]=float(value)/_scale
            elif self.gpx[self.gpx.columns[col]].dtype==np.dtype('int'):
                self.gpx[self.gpx.columns[col]].iloc[row-rowshift]=int(value)
            else:
                self.gpx[self.gpx.columns[col]].iloc[row-rowshift]=str(value)
        except:
            print("couldn't set value!")
        
    def IsEmptyCell(self, row, col):
        return col>=len(self.gpx.columns) or self.gpx[self.gpx.columns[col]] is None
                
class WxGpxGrid(wx.grid.Grid):
    def __init__(self,parent):
        wx.grid.Grid.__init__(self, parent, wx.NewId())
        self.parent=parent
        self.gpxtable=None
        self.SetTable(None)
        self.SetDefaultCellFont(wx.Font(10,wx.FONTFAMILY_DEFAULT,wx.NORMAL,wx.FONTWEIGHT_NORMAL,False))
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnCellChange)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL,self.OnCellSelected)
        self.Bind(wx.grid.EVT_GRID_EDITOR_CREATED, self.OnEditorCreated)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,self.OnLeftMouseDown)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnGridRightMouseDown)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightMouseDown)

    def OnCellSelected(self,evt):
        if self.gpxtable.GetTypeName(1,evt.Col)==wx.grid.GRID_VALUE_BOOL:
            wx.CallAfter(self.EnableCellEditControl)
            msgwrap.message("DATA_CHANGED",emitter=self.parent)
        evt.Skip()

    def OnEditorCreated(self,evt):
        if self.gpxtable.GetTypeName(1,evt.Col)==wx.grid.GRID_VALUE_BOOL:
            self.cb = evt.Control
        evt.Skip()

    def AttachGpx(self,gpx):
        self.gpxtable=WxGpxTable(gpx)
        self.SetTable(self.gpxtable)
        self.SetDefaultCellOverflow(False)
        for col,name in enumerate(self.gpxtable.gpx.columns):
            if gpx[name].dtype==np.dtype('bool'):
                self.SetColFormatBool(col)
                attr = wx.grid.GridCellAttr()
                attr.SetEditor(wx.grid.GridCellBoolEditor())
                attr.SetRenderer(wx.grid.GridCellBoolRenderer())
                self.SetColAttr(col,attr)
                self.SetColSize(col,5)
            else:
                if name!='time':
                    self.SetColFormatFloat(col,2,4)
        
    def DetachGpx(self):
        self.SetTable(None)
        if self.gpxtable:
            self.gpxtable.gpx=None
        self.gpxtable=None
        self.ForceRefresh()
        
    def OnCellChange(self,event):
        ## sel or data?
        msgwrap.message("DATA_CHANGED",emitter=self.parent)
        event.Skip()
    
    def OnLeftMouseDown(self,event):
        row=event.GetRow()
        col=event.GetCol()
        if self.gpxtable.gpx.dtypes[col]==np.dtype('bool'):
            self.gpxtable.SetValue(row,col,not self.gpxtable.GetValue(row,col))
            self.ForceRefresh()
            event.Skip()
            #don't propagate event!
        else:
            event.Skip()
    
    def OnGridRightMouseDown(self,event):
        row,col=event.GetRow(),event.GetCol()
        if not hasattr(self,"copy_menu"):
            self.copy_menu = wx.Menu()
            item = self.copy_menu.Append(-1, "Copy")
            self.Bind(wx.EVT_MENU, self.OnGridPopup, item)
        self.PopupMenu(self.copy_menu)
    
    def OnGridPopup(self, event):
        item = self.copy_menu.FindItemById(event.GetId())
        text = item.GetText()
        if text=='Copy':
            self.OnCopy()
        else:
            pass
        
    def OnLabelRightMouseDown(self,event):
        row = event.GetRow()
        col = event.GetCol()
        if row==-1:
            if self.GetSelectedCols()==[]:
                return
            if not hasattr(self,"col_menu"):
                self.col_menu = wx.Menu()
                for text in ["Delete column","Append column","Sort ascending", "Sort descending"]:
                    item = self.col_menu.Append(-1, text)
                    self.Bind(wx.EVT_MENU, self.OnColPopup, item)
            self.PopupMenu(self.col_menu)
        elif col==-1:
            if self.GetSelectedRows()==[]:
                return
            if not hasattr(self,"row_menu"):
                self.row_menu = wx.Menu()
                for text in ["Enable selected","Disable selected","Enable non selected", "Disable non selected","Toggle points","Enable all"]:
                    item = self.row_menu.Append(-1, text)
                    self.Bind(wx.EVT_MENU, self.OnRowPopup, item)
            self.PopupMenu(self.row_menu)
        
    def OnColPopup(self, event):
        item = self.col_menu.FindItemById(event.GetId())
        text = item.GetItemLabelText()
        key=self.gpxtable.gpx.columns[self.GetSelectedCols()[0]]
        if text=="Delete column":
            dlg = wx.MessageDialog(None, "Destroy col \" %s \"" % key,"Confirm",wx.OK|wx.CANCEL|wx.ICON_WARNING)
            if dlg.ShowModal()==wx.ID_OK:
                self.gpxtable.gpx.drop(columns=[key], inplace=True)
                msgwrap.message("DATA_CHANGED",emitter=self.parent)
            dlg.Destroy()
        elif text=="Append column":
            (name,)=WxQuery("New column",[("wxentry","Column name",None,"buffer",'str')])
            self.gpxtable.gpx[name]=0.0
            msgwrap.message("DATA_CHANGED",emitter=self.parent)
        elif text=="Sort ascending":
            attrs=attrs_save(self.gpxtable.gpx)
            #self.gpxtable.gpx.unit.save()
            self.gpxtable.gpx.sort_values(by=key,inplace=True,ascending=True)
            attrs_load(self.gpxtable.gpx,attrs)
            #self.gpxtable.gpx.unit.restore()
            msgwrap.message("DATA_CHANGED",emitter=self.parent)
        elif text=="Sort descending":
            attrs=attrs_save(self.gpxtable.gpx)
            #self.gpxtable.gpx.unit.save()
            self.gpxtable.gpx.sort_values(by=key,inplace=True,ascending=False)
            attrs_load(self.gpxtable.gpx,attrs)
            #self.gpxtable.gpx.unit.restore()
            msgwrap.message("DATA_CHANGED",emitter=self.parent)
        self.ForceRefresh()

    def OnRowPopup(self,event):
        item = self.row_menu.FindItemById(event.GetId())
        text = item.GetItemLabelText()
        if text=='Enable selected':
            self.gpxtable.gpx['ok'].iloc[self.GetSelectedRows()]=True
        if text=='Disable selected':
            self.gpxtable.gpx['ok'].iloc[self.GetSelectedRows()]=False
        if text=='Enable non selected':
            ns=list(set(range(len(self.gpxtable.gpx)))-set(self.GetSelectedRows()))
            self.gpxtable.gpx['ok'].iloc[ns]=True
        if text=='Disable non selected':
            ns=list(set(range(len(self.gpxtable.gpx)))-set(self.GetSelectedRows()))
            self.gpxtable.gpx['ok'].iloc[ns]=False
        if text=='Toggle points':
            self.gpxtable.gpx['ok']=np.invert(self.gpxtable.gpx['ok'])
        if text=='Enable all':
            self.gpxtable.gpx['ok']=True
        self.ForceRefresh()
        msgwrap.message("SELECTION_CHANGED",emitter=self.parent)
        
    def OnCopy(self):
        if self.GetSelectionBlockTopLeft() == []:
            rows = 1
            cols = 1
            iscell = True
        else:
            rows = self.GetSelectionBlockBottomRight()[0][0] - self.GetSelectionBlockTopLeft()[0][0] + 1
            cols = self.GetSelectionBlockBottomRight()[0][1] - self.GetSelectionBlockTopLeft()[0][1] + 1
            iscell = False
        data = ''
        for r in range(rows):
            for c in range(cols):
                if iscell:
                    data += str(self.GetCellValue(self.GetGridCursorRow() + r, self.GetGridCursorCol() + c))
                else:
                    data += str(self.GetCellValue(self.GetSelectionBlockTopLeft()[0][0] + r, self.GetSelectionBlockTopLeft()[0][1] + c))
                if c < cols - 1:
                    data += '\t'
            data += '\n'
        clipboard = wx.TextDataObject()
        clipboard.SetText(data)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(clipboard)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Error")
            
class Table(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.mapwidget = kwargs.pop('MapPanel', None)
        self.timewidget = kwargs.pop('TimePanel', None)
        self.cfg = kwargs.pop('cfg', None)
        wx.Panel.__init__(self,*args, **kwargs)
        self.id=wx.NewId()
        self.gpxgrid=WxGpxGrid(self)
        #standard events
        #self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftMouseDown)
        #self.Bind(wx.EVT_LEFT_UP,self.OnLeftMouseUp)
        #self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftMouseDblClick)
        #self.Bind(wx.EVT_MOTION,self.OnMouseMotion)
        #self.Bind(wx.EVT_ENTER_WINDOW,self.OnMouseEnter)
        #self.Bind(wx.EVT_LEAVE_WINDOW,self.OnMouseLeave)
        #self.Bind(wx.EVT_RIGHT_DOWN,self.OnRightMouseDown)
        #self.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        #self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_SIZE,self.OnSize)
        #self.Bind(wx.EVT_ERASE_BACKGROUND,self.OnErase)
        #custom events
        msgwrap.register(self.OnIndexChanged, "INDEX_CHANGED")
        msgwrap.register(self.OnSelectionChanged, "SELECTION_CHANGED")
        msgwrap.register(self.OnDataChanged, "DATA_CHANGED")
               
    def AttachGpx(self,gpx):
        self.gpxgrid.AttachGpx(gpx)
        self.gpx=gpx ## make sure that all plugins have a gpx attribute

        
    def DetachGpx(self):
        self.gpxgrid.DetachGpx()
        self.gpx=None
        
    def OnIndexChanged(self,emitter,idx):
        if emitter!=self:
            pass

    def OnSelectionChanged(self,emitter):
        if emitter!=self:
            self.gpxgrid.ForceRefresh()
        
    def OnDataChanged(self,emitter):
        if emitter!=self:
            # check if a new column or line has changed.
            if not self.gpx is None:
                if ((self.gpxgrid.gpxtable._rows==self.gpxgrid.gpxtable.GetNumberRows())\
                    and(self.gpxgrid.gpxtable._cols==self.gpxgrid.gpxtable.GetNumberCols())):
                    self.gpxgrid.ForceRefresh()
                else:
                    tmpgpx=self.gpxgrid.gpxtable.gpx
                    self.gpxgrid.DetachGpx()
                    self.gpxgrid.AttachGpx(tmpgpx)
                    self.gpxgrid.ForceRefresh()
            
            
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
        self.gpxgrid.SetSize(self.GetSize())
        
    def OnErase(self,event):pass
       
class Plugin(Table):
    def __init__(self, *args, **kwargs):
       Table.__init__(self, *args, **kwargs)  
    
    def GetName(self):
        return "Table"
