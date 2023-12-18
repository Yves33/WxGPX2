#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import numpy as np
KMH=3.6        ## converts m/s to km/h kmh=ms*KMH
MPH=2.23694    ## converts m/s to miles/h
KNOTS=1.94384  ## converts m/s to knots
RAD=np.pi/180  ## converts degrees to RAD

def vmg(speed,heading,tgt=0):
    '''
    computes the VMG (velocity made good)
    parametes:
    - speed boat speed in whatever unit
    - heading: boat heading North is 0, East is 90, South is 180 West is 270
    - tgt: direction of taget to reach. (e.g direction the wind is coming from)
    '''
    return speed*np.cos(heading-tgt)

def apparentwind(bs,bc,ws,wc):
    '''
    computes apparent wind direction and speed
    - bs : boat speed
    - boat angle: the boat direction. expects radians
    - ws: the wind speed. same units as boat speed
    - wa: wind angle. the angle the wind is aiming at
	apparent wind is relative to boat!! In order to get the true direction of apparent wind, use (ba+awa)%(2*np.pi)
    '''
    twa=(bc-wc)  ## true wind angle
    awa=np.arctan((np.sin(twa)*ws)/(bs+np.cos(twa)*ws))
    aws=np.sqrt((np.sin(twa)*ws)**2+(bs+np.cos(twa)*ws)**2)
    return aws,awa
    
def avgangles(a):
    '''
    returns the average of angles
    '''
    return np.arctan2( np.sum(np.sin(a))/len(a), np.sum(np.cos(a))/len(a))

def awvmg(gpx,ws=20,wa=70*RAD):
	'''
	computes apparetn wind and vmg relative to wind. modifies the dataframe by adding the columns
	- awa : apparent wind angle, relative to boat (degrees)
	- awaaa : apparent wind absolute angle (degrees)
	- aws:apparent wind speed
	- vmg:velocity made good 
	'''
	s,a=apparentwind(np.convolve(gpx.speed,np.ones(5)/5,mode='same')*KNOTS,
					np.convolve(gpx.heading,np.ones(5)/5,mode='same')*RAD,
					ws,
					wa)
	gpx['awar']=a/RAD
	gpx['awaa']=(a/RAD+gpx['heading'])%360
	gpx['aws']=s
	gpx['vmg']=vmg(np.convolve(gpx.speed,np.ones(5)/5,mode='same')*KNOTS,
					np.convolve(gpx.heading*RAD,np.ones(5)/5,mode='same')*RAD,
					wa)
   
        
