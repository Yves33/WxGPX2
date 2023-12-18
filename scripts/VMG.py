#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from libsailutils import *

def __scriptmain__():
    try:
        (ws,wa,bs,ba)=query("Apparent wind and VMG calculation",	\
                        [('wxentry','wind speed (same units as boat)',None,25,'float'),\
                        ('wxentry','wind direction (deg)',None,75,'float','Direction the wind is pointing to'),\
                        ('wxcombo','boat speed','|'.join(gpx.columns),'speed','str'),
                        ('wxcombo','boat angle','|'.join(gpx.columns),'heading','str'),\
                        ])
    except:
        return

    s,a=apparentwind(np.convolve(gpx[bs],np.ones(5)/5,mode='same')*KNOTS,
                    np.convolve(gpx[ba],np.ones(5)/5,mode='same')*RAD,
                    ws,
                    wa*RAD)
    wunits=attrs_save(gpx) ## adding /deleting columns destroys the unit information!
    gpx['awar']=a/RAD
    gpx['awaa']=(a/RAD+gpx['heading'])%360
    gpx['aws']=s

    _upwind=((gpx[ba]-(wa))-180)%360
    _vmg=gpx[bs]*np.abs(np.cos(_upwind*RAD))
    ## smooth data
    gpx['uwa']=_upwind ##np.convolve(_upwind, np.ones(5)/5,mode='same')
    gpx['vmg']=_vmg ##np.convolve(_vmg, np.ones(5)/5,mode='same')

    attrs_load(gpx,wunits)

    gpx['awar'].unit.use('deg')
    gpx['awaa'].unit.use('deg')
    gpx['aws'].unit.use('kts')
    gpx['uwa'].unit.use('deg')
    gpx['vmg'].unit.use('kts')
    ## we could directly set the graphs
    #app.frame.plugins["polarplot"].thetasrc='uwa'
    #app.frame.plugins["polarplot"].radiusrc='vmg'
    #app.frame.plugins["polarplot"].Plot()
    sync()
        
__scriptmain__()
