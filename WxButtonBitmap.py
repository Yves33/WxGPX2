import wx
from io import BytesIO
import base64

class GenButtonBitmap(wx.Control):
    def __init__(self, parent, id=wx.ID_ANY, bitmapon=wx.NullBitmap, bitmapoff=wx.NullBitmap, buttontype='toggle', pos=wx.DefaultPosition, size=wx.DefaultSize, initial=0, style=wx.BORDER_NONE, name="OnOffButton"):
        """
        Default class constructor.

        @param parent:  Parent window. Must not be None.
        @param id:      identifier. A value of -1 indicates a default value.
        @param pos:     Position. If the position (-1, -1) is specified
                        then a default position is chosen.
        @param size:    If the default size (-1, -1) is specified then the image size is chosen.
        @param initial: Initial value 0 False or 1 True.
        @param style:   border style.
        @param name:    Widget name.
        """

        wx.Control.__init__(self, parent, id, pos=pos, size=size, style=style, name=name)
        self.parent = parent
        self._initial = initial
        self._frozen_value = initial
        self._pos = pos
        self._size = wx.Size(size)
        self._name = name
        self._id = id
        self.SetSize(self._size)
        self.buttontype=buttontype
        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        if not bitmapon:
            bitmapon=wx.Bitmap(20,20)
        if not bitmapoff:
            bitmapoff=wx.Bitmap(20,20)
        if isinstance(bitmapon,bytes):
            bitmapon=wx.Bitmap(wx.Image(BytesIO(base64.b64decode(bitmapon))))
        if isinstance(bitmapoff,bytes):
            bitmapoff=wx.Bitmap(wx.Image(BytesIO(base64.b64decode(bitmapoff))))
        self._bitmaps = {
            "On": self.SetImageSize(bitmapon),
            "Off": self.SetImageSize(bitmapoff),
            }
        self._bitmaps["OnDisabled"] = self.DisableImage(self._bitmaps["On"])
        self._bitmaps["OffDisabled"] = self.DisableImage(self._bitmaps["Off"])
        if self._initial > 1:
            self._initial = 1
        if self._initial < 0:
            self._initial = 0
        self._value = initial
        self._enabled = True
        self.InitUI()

    def InitUI(self):
        self.img = wx.StaticBitmap(self, -1, bitmap=wx.Bitmap(self.GetBitmap()))
        self.Bind(wx.EVT_SIZE, self.OnSize)
        if self.buttontype=='toggle':
            self.img.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        else:
            self.img.Bind(wx.EVT_LEFT_DOWN, self.OnDown)
            self.img.Bind(wx.EVT_LEFT_UP, self.OnUp)
        self.Show()

    def OnSize(self, event):
        self._size = self.DoGetBestSize()
        self.Refresh()
        
    def OnUp(self, e):
        if not self._enabled:
            return
        self._value = not self._value
        self.img.SetBitmap(self.GetBitmap())
        wx.PostEvent(self.GetEventHandler(), wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId()))
        self.Refresh()
        
    def OnDown(self, e):
        if not self._enabled:
            return
        self._value = not self._value
        self.img.SetBitmap(self.GetBitmap())
        self.Refresh()
        
    def OnClick(self, e):
        if not self._enabled:
            return
        self._value = not self._value
        self.img.SetBitmap(self.GetBitmap())
        if self.buttontype!='toggle':
            wx.PostEvent(self.GetEventHandler(), wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId()))
        else:
            btnEvent = wx.CommandEvent(wx.EVT_TOGGLEBUTTON.typeId, self.GetId())
            btnEvent.EventObject = self
            btnEvent.SetInt(self._value)
            wx.PostEvent(self.GetEventHandler(), btnEvent)
        self.Refresh()

    def GetValue(self):
        return self._value

    def SetValue(self, value):
        self._value = value
        self.img.SetBitmap(self.GetBitmap())
        self.Refresh()

    def Disable(self, value=True):
        self.Enable(not value)

    def Enable(self, value=True):
        self._enabled = value
        if value and self.IsEnabled(): # If value = current state do nothing
            return
        if not value and not self.IsEnabled():
            return
        wx.Control.Enable(self, value)
        bmp = self.GetBitmap()
        self.img.SetBitmap(bmp)
        tp = self.GetToolTip()
        self.Refresh()

    def DisableImage(self, bmp):
        bmp = bmp.ConvertToDisabled()
        return bmp

    def SetToolTip(self, tip):
        wx.Control.SetToolTip(self, tip)
        self.Refresh()

    def GetToolTip(self):
        tp = wx.Control.GetToolTip(self)
        if not tp:
            tp = ''
        else:
            tp = tp.GetTip()
        return tp

    def IsEnabled(self):
        return wx.Control.IsEnabled(self)

    def DoGetBestSize(self):
        bitmap = self.GetBitmap()
        # Retrieve the bitmap dimensions.
        bitmapWidth, bitmapHeight = bitmap.GetWidth(), bitmap.GetHeight()
        best = wx.Size(bitmapWidth, bitmapHeight)
        self.SetSize(best)
        self.CacheBestSize(best)
        return best

    def SetForegroundColour(self, colour):
        wx.Control.SetForegroundColour(self, colour)
        self.InitializeColours()
        self.Refresh()

    def SetBackgroundColour(self, colour):
        wx.Control.SetBackgroundColour(self, colour)
        self.Refresh()

    def SetImageSize(self, bmp):
        bmp = wx.Bitmap(bmp)
        imgsize = bmp.GetSize()
        imgh = imgsize[1]
        imgw = imgsize[0]
        w = self._size[0]
        h = self._size[1]
        if w <= 0:
            w = imgw
        if h <= 0:
            h = imgh
        img = bmp.ConvertToImage()
        img = img.Scale(w,h,quality=wx.IMAGE_QUALITY_HIGH)
        bmp = img.ConvertToBitmap()
        return bmp

    def GetBitmap(self):
        if not self.IsEnabled():
            if not self._value:
                return self._bitmaps["OffDisabled"]
            else:
                return self._bitmaps["OnDisabled"]
        if not self._value:
            return self._bitmaps["Off"]
        else:
            return self._bitmaps["On"]

    def SetBitmapOn(self, bitmap):
        self._bitmaps["On"] = self.SetImageSize(bitmap)
        self._bitmaps["OnDisabled"] = self.DisableImage(self._bitmaps["On"])
        self.img.SetBitmap(self.GetBitmap())
        self.Refresh()

    def SetBitmapOff(self, bitmap):
        self._bitmaps["Off"] = self.SetImageSize(bitmap)
        self._bitmaps["OffDisabled"] = self.DisableImage(self._bitmaps["Off"])
        self.img.SetBitmap(self.GetBitmap())
        self.Refresh()

class WxButtonBitmap(GenButtonBitmap):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs,buttontype='button')
        
class WxToggleButtonBitmap(GenButtonBitmap):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs,buttontype='toggle')


if __name__ == '__main__':

    class MyFrame(wx.Frame):

        def __init__(self, parent):

            wx.Frame.__init__(self, parent, -1, "Toggle Button Bitmap Demo", size=(-1, 680))

            panel = wx.Panel(self, -1, size=(400, 500))
            panel.SetBackgroundColour('#f0ffff') # Azure
            sizer = wx.BoxSizer(wx.VERTICAL)
            self.onoff = WxToggleButtonBitmap(panel, -1, bitmapon="G1.png", bitmapoff="G2.png", size=(200,200), initial=0)
            self.onoff1 = WxToggleButtonBitmap(panel, -1, bitmapon="G1.png", bitmapoff="G2.png", size=(40,40), initial=1)
            self.txt = wx.TextCtrl(panel, -1, "Off", size=(50,30))
            self.onoff2 = WxToggleButtonBitmap(panel, -1, bitmapon="G3.png", bitmapoff="G4.png", size=(40,20), initial=1)
            self.onoff3 = WxToggleButtonBitmap(panel, -1, bitmapon="G3.png", bitmapoff="G4.png", initial=0)
            self.Bind(wx.EVT_TOGGLEBUTTON, self.OnOff, id=self.onoff.GetId())
            sizer.Add(self.onoff, 0, wx.ALL, 20)
            sizer.Add(self.txt, 0, wx.LEFT, 90)
            sizer.Add(self.onoff1, 0, wx.ALL, 20)
            sizer.Add(self.onoff2, 0, wx.ALL, 20)
            sizer.Add(self.onoff3, 0, wx.ALL, 20)
            panel.SetSizer(sizer)
            self.onoff2.SetToolTip("Button 2")
            self.onoff2.Enable(False)
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.Toggle)
            self.timer.Start(5000)


        def Toggle(self, event):
            self.onoff2.Enable(not self.onoff2.IsEnabled())

        def OnOff(self, event):
            print("Event on/off click")
            if event.GetValue():
                self.txt.SetValue("On")
            else:
                self.txt.SetValue("Off")
            event.Skip()

        def SwOn(self, event):
            obj = event.GetEventObject()
            print(obj.Name + "Event On")

        def SwOff(self, event):
            obj = event.GetEventObject()
            print(obj.Name + "Event Off")

    app = wx.App()
    frame = MyFrame(None)
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
