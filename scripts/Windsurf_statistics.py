#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

### calculate best points
import datetime
import numpy as np
import gpxutils

selectetion_saved=gpx.ok.copy()                                                                # save selection, as we will modify it
KNOTS=1.94384
#todo: push all these measurments in an array! and copy to clipboard
#date|hour|distance|duration|avg speed|duration (>10kts)|distance (>10kts)|avg speed (>10kts)|best 1s|best 10s|best 100|best 500
date=gpx.time[0].strftime("%Y %m %d")
time=gpx.time[0].strftime("%H %M %S")

sel=gpx.ok.copy()
avg_speed_kts=gpx.speed[sel].mean()*KNOTS
total_distance_m=np.sum(gpx.deltaxy[sel])
total_duration_hms=str(datetime.timedelta(seconds=np.sum(gpx.deltat[sel])))

sel=gpx.ok.copy() & (gpx.speed*KNOTS>10)
avg_speed_above_kts=gpx.speed[sel].mean()*KNOTS
total_distance_above_m=np.sum(gpx.deltaxy[sel])
total_duration_above_hms=str(datetime.timedelta(seconds=np.sum(gpx.deltat[sel])))

max_speed_knots=gpx.speed[gpx.ok].max()*KNOTS

summary=[str(x) for x in [date,time,\
                        avg_speed_kts,total_distance_m,total_duration_hms,\
                        avg_speed_above_kts,total_distance_above_m,total_duration_above_hms,\
                        max_speed_knots,\
                        np.max(np.convolve(gpx.speed,np.ones(10)/10,mode='same')*KNOTS),
                        np.min(gpxutils.hv_pace(gpx.deltaxy,gpx.deltat,500))*500
                        ]
                    ]                
labels=["Date","Time",\
                "Avg Speed (kts)","Distance (m)","Duration (s)",\
                "Avg speed(>10kts)","Distance (>10kts)","Duration (>10kts)",\
                "VMax (kts)",\
                "Best 10s (kts)","Best 500m (s)"]
## horizontal printing
#print('\t'.join(labels))
#print('\t'.join(summary))

## vertical printing
for label,value in zip(labels,summary):
    print(f"{label:<20}:{value}")


    
