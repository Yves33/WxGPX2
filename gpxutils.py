#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import sys
sys.path.insert(0,"./modules")
from fitparse import FitFile  ## could also use https://pypi.org/project/fit-tool/, which can also save data!
import pandas as pd
import numpy as np
from collections import Counter

def resample(gpx,dt=None,force=False):
    ## whoops! panda has already a resample function
    # df=df.set_index('time')\
    #     .resample(rule='f{int(df.time).mode()}s',origin=df.time[0])\
    #     .interpolate('linear')\
    #     .reset_index()

    gpx.drop_duplicates(subset=['time'],inplace=True)
    deltas=np.ediff1d(  (gpx.time-gpx.time.iloc[0]).dt.total_seconds()  )
    if len(set(deltas))>1 or force:
        if dt is None:
            #si=int(Counter(deltas).most_common(1)[0][0])
            si=int(np.round(min(deltas)))
            si=f'{si}s'
        else:
            si=dt
        gpx.set_index('time',drop=True,inplace=True)
        newindex=pd.date_range(start=gpx.index[0],end=gpx.index[len(gpx)-1],freq=si)
        #print(f"There are {len(newindex)-len(dt)} missing points out of {len(newindex)}")
        gpx=gpx.reindex(newindex)
        try:
            gpx=gpx.interpolate(method='cubic')
        except:
            gpx=gpx.interpolate(method='linear')
        gpx['time']=gpx.index
        gpx.reset_index(drop=True,inplace=True)
    return gpx

def parsefitfile(filename):
    a = FitFile(filename)
    a.parse()
    series={}
    messages=[]
    for r in a.get_messages(name='record'):
        # for some strange reason, I sometimes have duplicated fields...
        d={}
        for f in r.fields:
            d[f.name]=f.value
        ## works only with a very regular fit file. but on suunto, some records may be incomplete!
        #for f,v in d.items():
        #    if f not in series.keys(): 
        #        series[f]=[]
        #    series[f].append(v)
        ## safer to just save all dicts!
        messages.append(d)

    #assert( len( set([len(s) for s in series.values()]))==1 )
    #df=pd.DataFrame(series)
    df=pd.DataFrame.from_records(messages,index='timestamp')\
        .reset_index()\
        .interpolate()\
        .bfill()
    ## tidy up all this!
    df['lat']=df.position_lat/11930464.71
    df['lon']=df.position_long/11930464.71
    df['speed']=df.speed/1000
    df['time']=df.timestamp
    df['idx']=df.index
    df['ok']=True
    df.drop(['position_lat','position_long','timestamp'],axis=1,inplace=True)
    return df

def parsegpxfile(filename,trkname=None):
    from xml.dom import minidom
    import datetime

    doc=minidom.parse(filename)
    doc.normalize()
    gpx = doc.documentElement
    tracks={}
    for e,trk in enumerate(gpx.getElementsByTagName('trk')):
        try:
            name = f'track_{e}'#trk.getElementsByTagName('name')[0].firstChild.data
        except:
            name=f'track_{e}'
        tracks[name] = []
        for trkseg in trk.getElementsByTagName('trkseg'):
            for trkpt in trkseg.getElementsByTagName('trkpt'):
                mytrkpt={}
                mytrkpt['lat'] = float(trkpt.getAttribute('lat'))
                mytrkpt['lon'] = float(trkpt.getAttribute('lon'))
                rfc3339 = trkpt.getElementsByTagName('time')[0].firstChild.data
                try: ## according to specification time is not required (https://www.topografix.com/gpx_manual.asp#trk)
                    mytrkpt['time'] = datetime.datetime.strptime(rfc3339, '%Y-%m-%dT%H:%M:%S.%fZ')
                except ValueError:
                    mytrkpt['time'] = datetime.datetime.strptime(rfc3339, '%Y-%m-%dT%H:%M:%SZ')
                for node in trkpt.childNodes:
                    try:
                        if node.tagName not in ['time','extensions']:
                            try:
                                mytrkpt[node.tagName]=float(node.firstChild.data)
                            except:
                                mytrkpt[node.tagName]=node.firstChild.data
                    except:
                        pass
                extensions = trkpt.getElementsByTagName('extensions')
                if len(extensions):
                    trkPtExtensions = extensions[0].getElementsByTagName('gpxtpx:TrackPointExtension')
                    for trkPtExtension in trkPtExtensions:
                        for child in trkPtExtension.childNodes:
                            try:
                                mytrkpt[child.tagName]=float(child.firstChild.data)
                            except:
                                pass
                tracks[name].append(mytrkpt)
    if trkname is None:
        trkname=list(tracks.keys())[0]
    return pd.DataFrame(tracks[trkname])

gpx_optional='ele|time|magvar|geoidheight|name|cmt|desc|src|link|sym|type|sat|hdop|vdop|pdop|ageofdgpsdata|dgpsid'.split('|')
gpx_extensions={'gpxtpx':'atemp|wtemp|depth|hr|cad|speed|course|bearing'.split('|'),
               'gpxdata':'hr|cadence|temp|distance|sensor'.split('|'),
               'gpxother':'pwr|lap|sealevelpressure|verticalspeed'.split('|')
            }
gpx_discard='lat|lon|deltaxy|heading|hv_speed|hv_pace|awaa|awar|aws|upwind|uwa|vmg|deltat|seconds|ok|idx'.split('|')
## some gpx/fit files may present weird extensions names. the following mappings will be applied
## in most cases, they are applied on file opening
gpx_extensions_mappings={'Power':'pwr',
                        'PowerInWatts':'pwr',
                        'Distance':'distance',
                        'temp':'atemp',
                        'cadence':'cad',
                        'heartrate':'hr',
                        'Temperature':'atemp'
                        }
def savegpxfile(df,filename,fields=None,indices=None,name=''):
        # see http://www.topografix.com/gpx_manual.asp to get a full list of allowed optional info for trkpt
        # http://www.topografix.com/GPX/1/1
        # http://www.topografix.com/GPX/1/1/gpx.xsd
        # http://www.garmin.com/xmlschemas/GpxExtensions/v3
        # http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd
        # http://www.garmin.com/xmlschemas/TrackPointExtension/v1
        # http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd
        # <trkpt lat="43.963912" lon="4.594150">
        # <ele>-7.8</ele>
        # <time>2013-10-25T18:10:05Z</time>
        # <extensions><gpxtpx:TrackPointExtension>
        # <gpxtpx:hr>255</gpxtpx:hr>
        # <gpxtpx:atemp>288.15</gpxtpx:atemp>
        # </gpxtpx:TrackPointExtension></extensions>
        # </trkpt>
        if fields is None:
            fields=list(df.columns)
        if indices is None:
            indices=range(0,len(df))
        ## apply field translation and discard unwanted fields
        fields=[gpx_extensions_mappings.get(f) if gpx_extensions_mappings.get(f) else f for f in fields]
        fields=[f for f in fields if f not in gpx_discard and f not in ['lat','lon']]
        #optional='name|desc|url|urlname|time|course|speed|ele|magvar|geoidheight|cmt|src|sym|type|fix|sat|hdop|vdop|pdop|ageofdgpsdata|dgpsid'.split('|')
        #extensions='hr|pwr|power|distance|cad|atemp|wtemp|cal'.split(|')
        #discard='deltaxy|heading|hv_speed|hv_pace|awaa|awar|aws|upwind|vmg|deltat|seconds|ok|idx'.split('|')
        # remove fields which are automatically generated when a file is opened, as well as lat and lon which are properties and not elements
        header = '\n'.join([f'<?xml version="1.0" encoding="UTF-8"?>',
                            f'<gpx version="1.0"\n\tcreator="wxgpgpsport" xmlns="http://www.topografix.com/GPX/1/0" xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">',
                            f'<trk><name>{name}</name>',
                            f'<trkseg>'
                            ])
        footer=f'</trkseg>\n</trk>\n</gpx>'
        gpxfile=open(filename,'w')
        gpxfile.write(header)
        for idx in indices:
            gpxfile.write('<trkpt lat="{}" lon="{}">\n'.format(df['lat'][idx],df['lon'][idx]))
            # two passes are required, first for optional params, 
            # then for extra params that should be treated as an extension
            # optional parameters
            for field in fields:
                if field=='time':
                    gpxfile.write('<time>{}</time>\n'.format( df['time'][idx].strftime("%Y-%m-%dT%H:%M:%SZ") ))
                elif field in gpx_optional:
                    gpxfile.write('<{}>{}</{}>\n'.format(field,df[field][idx],field))
            # extensions
            if len (set(fields)-set(gpx_optional))>0:
                gpxfile.write('<extensions>\n<gpxtpx:TrackPointExtension>\n')
                for field in fields:
                    if field not in gpx_optional:
                        gpxfile.write('<{}>{}</{}>\n'.format('gpxtpx:'+field,df[field][idx],'gpxtpx:'+field))
                gpxfile.write('</gpxtpx:TrackPointExtension>\n</extensions>\n')
            gpxfile.write('</trkpt>\n')
        gpxfile.write(footer)
        gpxfile.close()

def duration(timestamps):
    '''computes duration between two consecutive timestamps'''
    #d=timestamps-np.roll(timestamps,1)
    #d[0]=np.nan#d[0]*0
    return pd.Series(np.append(np.ediff1d(timestamps),np.nan),name='duration')

def hv_distance(lat,lon,tgt=None):
    '''computes haversine distance 
    - between two consecutive points if tgt is None
    - or to a target point (lat,lon)
    '''
    lat2=lat * np.pi / 180.0
    lon2=lon * np.pi / 180.0
    if tgt is None:
        lat1=np.roll(lat,-1) * np.pi / 180.0
        lon1=np.roll(lon,-1) * np.pi / 180.0
        lat1[-1]=np.nan#lat1[1]
        lon1[-1]=np.nan#lon1[1]
    else:
        lat1=tgt[0]* np.pi / 180.0
        lon1=tgt[1]* np.pi / 180.0
    # haversine formula #### Same, but atan2 named arctan2 in numpy
    dlon = (lon2 - lon1)
    dlat = (lat2 - lat1)
    a = (np.sin(dlat/2))**2 + np.cos(lat1) * np.cos(lat2) * (np.sin(dlon/2.0))**2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0-a))
    #if tgt is None:
    #    c[0]=0.0
    return 6371000 * c

def heading(lat,lon,tgt=None):
    '''computes haversine heading
    - between two consecutive points if tgt is None
    - or to a target point (lat,lon)
    '''
    d=np.zeros_like(lat)
    lat2=lat * np.pi / 180.0
    lon2=lon * np.pi / 180.0
    if tgt is None:
        lat1=np.roll(lat,-1) * np.pi / 180.0
        lon1=np.roll(lon,-1) * np.pi / 180.0
        lat1[-1]=np.nan#lat1[1]
        lon1[-1]=np.nan#lon1[1]
    else:
        lat1=tgt[0]* np.pi / 180.0
        lon1=tgt[1]* np.pi / 180.0
    # vectorized haversine formula
    dlon = (lon2 - lon1)
    #dlat = (lat2 - lat1)
    b=np.arctan2(np.sin(dlon)*np.cos(lat2),np.cos(lat1)*np.sin(lat2)-np.sin(lat1)*np.cos(lat2)*np.cos(dlon))
    #bd=b*180/np.pi
    return np.mod((360+b*180/np.pi),360)

def hv_pace(dxy,dt,dist,ahead=True):
    d=np.cumsum(dxy)
    t=np.cumsum(dt)
    r=[]
    if ahead:
        for i in range (len(d)-1):
            idx=np.searchsorted(d,d[i]+dist)
            try:
                if idx<len(d):
                    r.append((t[idx]-t[i])/dist)
                else:
                    r.append(np.nan)
            except IndexError:
                pass
        r=pd.Series(r).ffill()
    else:
        first=np.searchsorted(d,dist)
        for i in range (first,len(d)):
            idx=np.searchsorted(d,d[i]-dist)
            try:
                if idx==0:
                    r.append(np.nan)
                else:
                    r.append((t[i]-t[idx])/dist)
            except IndexError:
                pass
        r=pd.Series(r).bfill()
    return r

if __name__=='__main__':
    #gpx=parsefitfile("data/windsurf.fit")
    #gpx['speed']=gpx.ball_speed
    #savegpxfile(gpx,"data/windsurf.gpx")
    gpx=parsegpxfile("data/windsurf.gpx")
    #print(duration(gpx.time).astype(int)/1e9)
    #print(heading(gpx.lat,gpx.lon))
    #print(gpx.time-np.roll(gpx.time,1))
    #print(hv_distance(gpx.lat,gpx.lon)/(duration(gpx.time).astype(int)//1e9))
    #print(min(hv_pace(hv_distance(gpx.lat,gpx.lon),
    #              duration(gpx.time).astype(int)//1e9,
    #              dist=500,
    #              ahead=False)))
