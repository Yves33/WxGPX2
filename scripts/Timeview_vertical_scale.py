#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

def __scriptmain__():
    ylo1,yhi1=timeview.ax1.get_ylim()
    ylo2,yhi2=timeview.ax2.get_ylim()
    ylo1,yhi1,ylo2,yhi2=WxQuery("Vertical scales",	\
                        [('wxentry','Left axis bottom',None,ylo1,'float'),
                         ('wxentry','Left axis top',None,yhi1,'float'),
                         ('wxentry','Right axis bottom',None,ylo2,'float'),
                         ('wxentry','Right axis top',None,yhi2,'float')
                        ])
    timeview.ax1.set_ylim(bottom=ylo1,top=yhi1)
    timeview.ax2.set_ylim(bottom=ylo2,top=yhi2)
    timeview.gpxcanvas.draw()
    
## in order to properly return from scripts using wxquery, we need to enclose everything in a function
__scriptmain__()
