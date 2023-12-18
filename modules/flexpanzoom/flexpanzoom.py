#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import math
import matplotlib
from matplotlib.backend_tools import Cursors

def ptinrect(l,t,r,b,x,y):
    return (min(l,r) < x <max(l,r)) and (min(b,t)<y<max(b,t))

class PanZoomFactory: 
    def __init__(self,figure,
                 tolerance=20,
                 clip=(1.2,1.2),
                 scales={"down":1.2,"up":1/1.2,"DOWN":2.0,"UP":1/2.0},
                 polaropts={'nodragradius':True,
                        'fixedlowbounds':True},
                 rightclickpopup=False,
                 zoomstr='>< | <>',
                 zoomstrfont=None,
                 zoomstrsize=6):
        '''
        PAN and Zoom factory designed for mouse:
        + mouse wheel in axis -> zoomn in, zoom out specified axis
        + mouse button 1 drag in axis -> pan specified axis
        + mouse button 3 drag in axis -> zoom in , zoom at specified axis
        + mouse button 3 clicked in axis -> popup zoomin zoomout
        
        The tool works also for polar plots, although the behaviour may seem less predictable.
        + mouse wheel in polar graph:zoom in, zoom out (high value only by default)

        Parameters
        ----------
        tolerance : int
            the minimal size in pixels of the region surrounding axis where mouse clicks will be handled.
            zoomer tries to determine the size of the axis,
        clip : tuple(float,float)
            the minimal zoom factors (use 1.0,1.0 to fit to data, negative values ( e.g -1.0,-1.0) to disable
        scales: dict
            zoom factors for mouse wheel or mouse clicks on zommin/zoomout popup
        polaropts : dict 
            specifies behavior on polarplot. currently accepts the following keys:
            - nodragradius: bool enable/disable left click pan on radius (modifies both high and low boundaries)
            - fixedlowbounds : bool enable/disable modifying low radius value with mouse wheel.the default is to modify only the high bounds.
        rightclickpopup : boolean
            whether to use the right click popup or not (otherwise right+drag will zoom)
        zoomstr : string
            the string to display in popup. any click in left/right part of popup induce zoomout/zoomin
        zoomstrfont : matplotlib.FontProperties
            the font used to display popup. may be an icon font (fa)
        zoomstrsize : int
            the size of the font
        '''
        self.figure=figure
        self.canvas=figure.canvas
        self.zoompatch=None
        self.dragaxis=None
        self.scales=scales
        self.tolerance=tolerance
        self.clip=clip
        self.rightclickpopup=rightclickpopup
        self.zoomstr=zoomstr
        self.zoomstrfont=zoomstrfont
        self.zoomstrsize=zoomstrsize
        self.polaropts=polaropts
        if self.rightclickpopup:
            self.canvas.mpl_connect('button_press_event', self.OnMouseDownRclick)
        else:
            self.canvas.mpl_connect('button_press_event', self.OnMouseDown)
        self.canvas.mpl_connect('button_release_event', self.OnMouseUp)
        self.canvas.mpl_connect('motion_notify_event', self.OnMouseMotion)
        self.canvas.mpl_connect('scroll_event', self.OnMouseWheel)

    def OnMouseDown(self,event):
        ax,where=self._get_axis(event,self.tolerance)
        if ax and where:
            if isinstance(ax, matplotlib.projections.polar.PolarAxes):self.OnMouseDownPolar(event,ax,where)
            else:self.OnMouseDownCartesian(event,ax,where)

    def OnMouseUp(self,event):
        ax,where=self._get_axis(event,self.tolerance)
        if ax and where:
            if isinstance(ax, matplotlib.projections.polar.PolarAxes):self.OnMouseUpPolar(event,ax,where)
            else:self.OnMouseUpCartesian(event,ax,where)
    
    def OnMouseMotion(self,event):
        ax,where=self._get_axis(event,self.tolerance)
        if ax and where:
            if isinstance(ax, matplotlib.projections.polar.PolarAxes):self.OnMouseMotionPolar(event,ax,where)
            else:self.OnMouseMotionCartesian(event,ax,where)

    def OnMouseDownRclick(self,event):
        ax,where=self._get_axis(event,self.tolerance)
        if ax and where:
            if isinstance(ax, matplotlib.projections.polar.PolarAxes):self.OnMouseDownPolar(event,ax,where)
            else:self.OnMouseDownCartesianRclick(event,ax,where)

    def OnMouseWheel(self,event):
        ax,where=self._get_axis(event,self.tolerance)
        if ax and where:
            if isinstance(ax, matplotlib.projections.polar.PolarAxes):self.OnMouseWheelPolar(event,ax,where)
            else:self.OnMouseWheelCartesian(event,ax,where)

    def _get_axis(self,event,tolerance):
        for ax in self.figure.axes:
            if isinstance(ax, matplotlib.projections.polar.PolarAxes):
                where=self._get_axis_polar(event,ax,tolerance)
            else:
                where=self._get_axis_cartesian(event,ax,tolerance)
            if not where is None:
                return ax, where
        return None,None
    
    def _get_axis_polar(self,event,ax,tolerance):   
        theta,radius=ax.transData.inverted().transform((event.x,event.y))
        bbox = ax.get_window_extent().transformed(self.figure.dpi_scale_trans.inverted())
        l=bbox.bounds[0]*self.figure.dpi
        b=bbox.bounds[1]*self.figure.dpi
        r=l+bbox.bounds[2]*self.figure.dpi
        t=b+bbox.bounds[3]*self.figure.dpi
        if ptinrect(l-tolerance,t+tolerance,r+tolerance,b-tolerance,event.x,event.y):
            if not event.xdata is None and not event.ydata is None:
                ## much more complex than that for polar... let's just return the value
                event.xdata=theta
                event.ydata=radius
                return 'radius'
            else:
                event.xdata=theta
                event.ydata=radius
                return 'theta'
             
    def _get_axis_cartesian(self,event,ax,tolerance):
        bbox = ax.get_window_extent().transformed(self.figure.dpi_scale_trans.inverted())
        l=bbox.bounds[0]*self.figure.dpi
        b=bbox.bounds[1]*self.figure.dpi
        r=l+bbox.bounds[2]*self.figure.dpi
        t=b+bbox.bounds[3]*self.figure.dpi
        ## convert screen coordinates to graph coordinates
        xlo=ax.get_xlim()[0]
        xhi=ax.get_xlim()[1]
        event.xdata=(event.x-l)/(r-l)*(xhi-xlo)+xlo
        try:
            ytickparams=ax.yaxis.get_tick_params()
            xtickparams=ax.xaxis.get_tick_params()
        except:
            #_xtickp=ax.xaxis._translate_tick_params(ax.xaxis._major_tick_kw)
            #_ytickp=ax.yaxis._translate_tick_params(ax.yaxis._major_tick_kw)
            _xtickp=ax.xaxis._major_tick_kw
            _ytickp=ax.yaxis._major_tick_kw
            ytickparams={'left':_xtickp['tick1On'],'right':_xtickp['tick2On']}
            xtickparams={'left':_ytickp['tick1On'],'right':_ytickp['tick2On']}
        width=max(tolerance,ax.yaxis.get_tightbbox(None).width) if not ax.yaxis.get_tightbbox(None) is None else tolerance
        height=max(tolerance,ax.xaxis.get_tightbbox(None).height) if not ax.xaxis.get_tightbbox(None) is None else tolerance
        if ptinrect(l-width,t,l,b,event.x,event.y) and ytickparams['left']:
            ylo,yhi=ax.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return 'left'
        if ptinrect(r,t,r+width,b,event.x,event.y) and ytickparams['right']:
            ylo,yhi=ax.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return 'right'
        if ptinrect(l,t,r,t+height,event.x,event.y) and xtickparams['right']:
            ylo,yhi=ax.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return 'top'
        if ptinrect(l,b-height,r,b,event.x,event.y) and xtickparams['left']:
            ylo,yhi=ax.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return 'bottom'
        if ptinrect(l,t,r,b,event.x,event.y):
            ylo,yhi=ax.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo       
            return 'main'
        return None
    
    def OnMouseDownCartesian(self,event,ax,where):
        if  (event.button==1 or event.button==3) and where in ['bottom','top','left','right']:
            (self.x0,self.y0)=(event.xdata,event.ydata)
            self.dragaxis=where
            self.dragax=ax
            if event.button==1:
                self.figure.canvas.set_cursor(Cursors.MOVE)
            elif event.button==3 and where in ['top','bottom']:
                self.figure.canvas.set_cursor(Cursors.RESIZE_HORIZONTAL)
            elif event.button==3 and where in ['left','right']:
                self.figure.canvas.set_cursor(Cursors.RESIZE_VERTICAL)
            return
        
    def OnMouseDownPolar(self,event,ax,where):
        if  (event.button==1 or event.button==3) and where in ['theta','radius']:
            (self.x0,self.y0)=(event.xdata,event.ydata)
            if where=='theta':
                self.thetamin,self.thetamax=ax.get_xlim()
                self.thetaoffset=ax.get_theta_offset()
                self.pct=(event.xdata-ax.get_xlim()[0])/(ax.get_xlim()[1]-ax.get_xlim()[0])
                self.dragaxis=where
                self.dragax=ax
                if event.button==1:
                    if self.pct<0.2 or self.pct>0.8:
                        self.figure.canvas.set_cursor(Cursors.RESIZE_VERTICAL)
                    else:
                        self.figure.canvas.set_cursor(Cursors.MOVE)
            elif where=='radius':
                (self.x0,self.y0)=(event.xdata,event.ydata)
                self.dragaxis=where
                self.dragax=ax
                if event.button==1:
                    self.figure.canvas.set_cursor(Cursors.MOVE)
                elif event.button==3:
                    self.figure.canvas.set_cursor(Cursors.RESIZE_HORIZONTAL)

    def OnMouseDownCartesianRclick(self,event,ax,where):
        if self.zoompatch and event.button==1 and ax:
            bbox=ax.transData.inverted().transform(self.zoompatch.get_bbox_patch().get_window_extent())
            l,t,r,b=bbox.flatten()
            if ptinrect(l,t,l+(r-l)/2,b,event.xdata,event.ydata):
                self.stored_event.button="DOWN"
                self.OnMouseWheelCartesian(self.stored_event,ax,self.stored_where)
                event.button=None ## to further prevent event processing
                return
            elif ptinrect(l+(r-l)/2,t,r,b,event.xdata,event.ydata):
                self.stored_event.button="UP"
                self.OnMouseWheelCartesian(self.stored_event,ax,self.stored_where)
                event.button=None
                return
        
        ## if we are still there, we should delete zoompatch if it exists
        if self.zoompatch:
            self.zoompatch.remove()
            del self.zoompatch
            self.zoompatch=None
            self.canvas.draw()
            return

        if  (event.button==1) and where in ['bottom','top','left','right']:
            (self.x0,self.y0)=(event.xdata,event.ydata)
            self.dragaxis=where
            self.dragax=ax
            if event.button==1:
                self.figure.canvas.set_cursor(Cursors.MOVE)
            return

        elif event.button==3:
            if where in ['bottom','top']:
                xpixels,ypixels=ax.transData.transform((event.xdata,ax.get_ylim()[where=='top']))
                xfig,yfig=self.figure.dpi_scale_trans.inverted().transform((xpixels,ypixels))
                x=xfig/self.figure.get_size_inches()[0]
                y=yfig/self.figure.get_size_inches()[1]
                self.zoompatch=self.figure.text(x,y,
                                self.zoomstr, 
                                fontsize=self.zoomstrsize,
                                fontproperties=self.zoomstrfont,
                                horizontalalignment='center',
                                verticalalignment=where
                                )
                self.zoompatch.set_bbox(dict(facecolor='w', alpha=1.0, edgecolor='k'))
                self.stored_event=event
                self.stored_where=where
                self.canvas.draw()
            elif where in ['left','right']:
                xpixels,ypixels=ax.transData.transform((ax.get_xlim()[where=='right'],event.ydata))
                xfig,yfig=self.figure.dpi_scale_trans.inverted().transform((xpixels,ypixels))
                x=xfig/self.figure.get_size_inches()[0]
                y=yfig/self.figure.get_size_inches()[1]
                self.zoompatch=self.figure.text(x,y,
                                       self.zoomstr, 
                                       fontsize=self.zoomstrsize,
                                       fontproperties=self.zoomstrfont,
                                       horizontalalignment=where,
                                       verticalalignment='center',zorder=1e19)
                self.zoompatch.set_bbox(dict(facecolor='w', alpha=1.0, edgecolor='k'))
                self.stored_event=event
                self.stored_where=where
                self.canvas.draw()
    
    def OnMouseMotionCartesian(self,event,ax,where):
        if not ax:
            return
        if event.button==1:
            if self.dragaxis in ['bottom','top'] and event.xdata:
                dx = event.xdata - self.x0
                self.dragax.set_xlim(self.dragax.get_xlim()[0]-dx,self.dragax.get_xlim()[1]-dx)
                self.canvas.draw()
            elif self.dragaxis in ['left','right']and event.ydata:
                dy = event.ydata - self.y0
                self.dragax.set_ylim(self.dragax.get_ylim()[0]-dy,self.dragax.get_ylim()[1]-dy)
                self.canvas.draw()
        elif event.button==3 and not self.rightclickpopup:
            if self.dragaxis in ['bottom','top'] and event.xdata:
                dx = self.x0-event.xdata
                scale=self.scales['down'] if dx>0 else self.scales['up'] if dx<0 else 1.0
                xlo=self.x0+(self.dragax.get_xlim()[0]-self.x0)*scale
                xhi=self.x0+(self.dragax.get_xlim()[1]-self.x0)*scale
                xlo,xhi=self._clamp(xlo,xhi,self.clip[0],ax,axis='x')
                self.dragax.set_xlim(xlo,xhi)
                self.x0=event.xdata
                self.canvas.draw()
            if self.dragaxis in ['left','right'] and event.ydata:
                dy = self.y0-event.ydata
                scale=self.scales['down'] if dy>0 else self.scales['up'] if dy<0 else 1.0
                ylo=self.y0+(self.dragax.get_ylim()[0]-self.y0)*scale
                yhi=self.y0+(self.dragax.get_ylim()[1]-self.y0)*scale
                ylo,yhi=self._clamp(ylo,yhi,self.clip[1],ax,axis='y')
                self.dragax.set_ylim(ylo,yhi)
                self.y0=event.ydata
                self.canvas.draw()

    def OnMouseMotionPolar(self,event,ax,where):
        #pclamp=lambda x: max(min(x,2*np.pi),0)
        twopi=2*math.pi
        if not ax:
            return
        if event.button==1:
            if self.dragaxis=='theta' and event.xdata:
                return
            elif self.dragaxis=='radius' and event.ydata and not self.polaropts['nodragradius']:
                dy = event.ydata - self.y0
                self.dragax.set_ylim(self.dragax.get_ylim()[0]-dy,self.dragax.get_ylim()[1]-dy)
                self.canvas.draw()
        elif event.button==3 and self.dragaxis=='radius' and event.ydata:
            dy = self.y0-event.ydata
            scale=self.scales['down'] if dy>0 else self.scales['up'] if dy<0 else 1.0
            ylo=self.y0+(self.dragax.get_ylim()[0]-self.y0)*scale
            yhi=self.y0+(self.dragax.get_ylim()[1]-self.y0)*scale
            ylo,yhi=self._clamp(ylo,yhi,self.clip[1],ax,axis='y')
            if self.polaropts['fixedlowbounds']:
                self.dragax.set_ylim(self.dragax.get_ylim()[0],yhi)
            else:
                self.dragax.set_ylim(ylo,yhi)
            self.y0=event.ydata
            self.canvas.draw()

    def OnMouseUpCartesian(self,event,ax,where):
        self.dragaxis=None
        self.x0,self.y0=None,None
        self.figure.canvas.set_cursor(Cursors.POINTER)

    def OnMouseUpPolar(self,event,ax,where):
        self.dragaxis=None
        self.x0,self.y0=None,None
        self.figure.canvas.set_cursor(Cursors.POINTER)

    def _clamp(self,lo,hi,clip,ax,axis='x'):
        if clip<=0.0:
            return lo,hi
        try:
            if axis=='x':
                _lo=min([min(line._x) for line in ax.get_lines() ])
                _hi=max([max(line._x) for line in ax.get_lines() ])
            else:
                _lo=min([min(line._y) for line in ax.get_lines() ])
                _hi=max([max(line._y) for line in ax.get_lines() ])
            _max=(_lo+_hi)/2+(_hi-_lo)*clip/2
            _min=(_lo+_hi)/2-(_hi-_lo)*clip/2
            nxhi=min(hi,_max)
            nxlo=max(lo,_min)
            return nxlo,nxhi
        except:
            return lo,hi
    
    def OnMouseWheelCartesian(self,event,ax,where):
        scale_factor = self.scales[event.button]
        if where in ['bottom','top']:
            xlo,xhi=ax.get_xlim()
            nxhi=event.xdata+(scale_factor*(xhi-event.xdata))
            nxlo=event.xdata-(scale_factor*(event.xdata-xlo))
            nxlo,nxhi=self._clamp(nxlo,nxhi,self.clip[0],ax,axis='x')
            ax.set_xlim([nxlo,nxhi])
            self.canvas.draw()

        elif where in ['left','right']:
            ylo,yhi=ax.get_ylim()
            nyhi=event.ydata+(scale_factor*(yhi-event.ydata))
            nylo=event.ydata-(scale_factor*(event.ydata-ylo))
            nylo,nyhi=self._clamp(nylo,nyhi,self.clip[1],ax,axis='y')
            ax.set_ylim([nylo,nyhi])
            self.canvas.draw()

    def OnMouseWheelPolar(self,event,ax,where):
        scale_factor = self.scales[event.button]
        if where=='radius':
            ylo,yhi=ax.get_ylim()
            nyhi=event.ydata+(scale_factor*(yhi-event.ydata))
            nylo=event.ydata-(scale_factor*(event.ydata-ylo))
            nylo,nyhi=self._clamp(nylo,nyhi,self.clip[1],ax,axis='y')
            if self.polaropts['fixedlowbounds']:
                ax.set_ylim([ax.get_ylim()[0],nyhi])
            else:
                ax.set_ylim([nylo,nyhi])
        elif where=='theta':
            pass
        self.canvas.draw()

if __name__=='__main__':
    import matplotlib.pyplot as plt
    import numpy as np

    def demosimple():
        fig1 = plt.figure()
        plt.plot([0, 1, 3, 6, 7, 4, 2, 0])
        panzoomer = PanZoomFactory(fig1)
        plt.show()

    def demomultiple():
        x1 = np.linspace(0.0, 5.0)
        y1 = np.cos(2 * np.pi * x1) * np.exp(-x1)
        x2 = np.linspace(0.0, 2.0)
        y2 = np.cos(2 * np.pi * x2)
        fig= plt.figure()
        fig.suptitle('A table with multiple subplots')
        ax1 = fig.add_subplot(221)
        ax1.plot(x1, y1, 'o-')
        ax1.set_ylabel('Damped oscillation')
        ax1.set_title('First plot')
        ax2 = fig.add_subplot(223)
        ax2.plot(x2, y2, '.-')
        ax2.set_xlabel('time (s)')
        ax2.set_ylabel('Undamped')
        ax2.set_title('Second plot')

        ax3=fig.add_subplot(222,polar=True)
        r = 1+np.arange(0, 2, 0.01)
        theta = 2 * np.pi * r
        ax3.plot(theta, r)
        ax3.set_rticks([0.5, 1, 1.5, 2])  # Less radial ticks
        ax3.set_rlabel_position(-22.5)    # Move radial labels away from plotted line
        ax3.grid(True)
        ax3.set_title("A line plot on a polar axis", va='bottom')
        ax3.set_rmax(3.0)
        #ax3.set_rmin(1.0)
        #ax3.set_thetamin(0.0)
        #ax3.set_thetamax(120)
        #ax3.set_ylim(-3,3)
        #ax3.set_xlim(0,2*np.pi/3)

        panzoomer = PanZoomFactory(fig,rightclickpopup=True)
        fig.tight_layout()
        plt.show()

    demomultiple()

