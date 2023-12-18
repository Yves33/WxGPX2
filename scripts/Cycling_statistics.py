#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

### calculate best points
import datetime
import numpy as np
import gpxutils

selectetion_saved=gpx.ok.copy()                                                                # save selection, as we will modify it
KMH=3.6
#todo: push all these measurments in an array! and copy to clipboard
#date|hour|distance|duration|avg speed|duration (>10kts)|distance (>10kts)|avg speed (>10kts)|best 1s|best 10s|best 100|best 500
date=gpx.time[0].strftime("%Y %m %d")
time=gpx.time[0].strftime("%H %M %S")

sel=gpx.ok.copy()
avg_speed_kmh=gpx.speed[sel].mean()*KMH
total_distance_m=np.sum(gpx.deltaxy[sel])
total_duration_hms=str(datetime.timedelta(seconds=np.sum(gpx.deltat[sel])))

sel=gpx.ok.copy() & (gpx.speed*KMH>10)
avg_speed_above_kmh=gpx.speed[sel].mean()*KMH
total_distance_above_m=np.sum(gpx.deltaxy[sel])
total_duration_above_hms=str(datetime.timedelta(seconds=np.sum(gpx.deltat[sel])))

max_speed_kmh=gpx.speed[gpx.ok].max()*KMH

summary=[str(x) for x in [date,time,\
                        avg_speed_kmh,total_distance_m,total_duration_hms,\
                        avg_speed_above_kmh,total_distance_above_m,total_duration_above_hms,\
                        max_speed_kmh,\
                        np.max(np.convolve(gpx.speed,np.ones(10)/10,mode='same')*KMH),
                        np.min(gpxutils.hv_pace(gpx.deltaxy,gpx.deltat,1000))*1000
                        ]
                    ]                
labels=["Date","Time",\
                "Avg Speed (kmh)","Distance (m)","Duration (hh:mm:ss)",\
                "Avg speed(>10kmh)","Distance (>10kmh)","Duration (>10kmh)",\
                "VMax (kmh)",\
                "Best 10s (kmh)","Best 1000m (s)"]
## horizontal printing
#print('\t'.join(labels))
#print('\t'.join(summary))

## vertical printing
for label,value in zip(labels,summary):
    print(f"{label:<20}:{value}")


    
