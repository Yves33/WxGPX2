#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import numpy as np
import matplotlib.pyplot as plt
units={'m/s':1,'km/h':3.6,'mph':2.23694,'kts':1.94384, 's.i':1}

def __scriptmain__():
    try:
        dst,debug,speedkey=WxQuery("Alpha",	\
                        [('wxcombo','Window length (m)','250|500|1000','250','int'),
                            #('wxhscale','Smooth (points)','0|30|1','0','int'),
                            #('wxcombo','Max missing points','1s|2s|5s|10s|30s','2s','str'),
                            ('wxcheck','Show graph',None,False,'bool'),
                            ('wxcombo','Key for speed','|'.join(gpx.columns),'speed','str')
                            ])
    except:
        return
    usym=gpx[speedkey].unit.sym
    uscale=units[usym]
    _selection=gpx[gpx.ok].copy()                                           ## keep only selected points and make a copy of data
    cheading=_selection.heading
    #if conv>=1:
    #    cheading=np.convolve(cheading,np.ones(conv)/conv,mode='same')    ## smooth data
    cheading=np.cos((cheading+np.mean(cheading))*np.pi/180)#[5:-5]          ## heading variations (eliminate first and last points to avoid border effetcs
    #cheading=np.convolve(cheadings,np.ones(conv)/conv,mode='same')    ## smooth data
    turns=(np.diff(np.sign(cheading)) != 0)*1                              ## determine sign change in tacks
    turns=np.where(turns!=0)[0]                                            ## get index of turns
    if debug:
        plt.plot(_selection.time,cheading)
        plt.vlines(_selection.time.iloc[turns],ymin=min(cheading),ymax=max(cheading),colors=['r'])
        plt.plot(_selection.time,_selection.speed,color='0.5')
    for e,t in enumerate(turns):                                        ## for each jibe
        ## extract points located in half distance window  enclosing jibe. obviously adjust numeric values
        jibe=_selection.iloc[np.where(np.abs(_selection.distance-_selection.distance.iloc[t])<dst//2)]
        #if(np.diff(jibe.time)>=pd.Timedelta(gaps)).any():
        #    continue
        if debug:
            plt.plot(jibe.time,jibe.speed)
        alpha=np.sum(jibe.deltaxy)/np.sum(jibe.deltat)  ## average speed over all path
        vmin=np.min(jibe[speedkey])
        print(f"jibe {e:3} ({_selection['time'].iloc[t].strftime('%H:%M:%S')}): alpha{dst} ({usym}): {alpha*uscale:>6.3f}, vmin ({usym}): {vmin*uscale:>6.3f}")
    if debug:
        plt.show()

## in order to properly return from scripts using wxquery, we need to enclose everything in a function
__scriptmain__()