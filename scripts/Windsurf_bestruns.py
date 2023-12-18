#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

### calculate best runs
import msgwrap
## todo
## - wxquery gui
## - choosing speed units
## - option to keep only the runs selected

SCALE=1.94384         ## m/s to KNOTS
SELECT_BEST_500=False ## if True, the program will (crash or) select the corresponding segments and disable other points

speed5s=np.convolve(gpx.speed,np.ones(5)/5,mode='same')
speed10s=np.convolve(gpx.speed,np.ones(10)/10,mode='same')
speed30s=np.convolve(gpx.speed,np.ones(30)/30,mode='same')

sel=gpx.ok.copy()
print("\nBest 5s runs (time,avg speed):")
best5s_value_knots=[]
for _ in range(5):
    maxidx=np.argmax(speed5s[sel])
    best5s_value_knots.append( ( gpx.time[maxidx].strftime("%H:%M:%S"),SCALE*max(speed5s[sel])  ) )
    speed5s[maxidx-5:maxidx+5]=-np.inf
    print(best5s_value_knots[-1])

print("\nBest 10s runs (time,avg speed):")
best10s_value_knots=[]
for _ in range(5):
    maxidx=np.argmax(speed10s[sel])
    best10s_value_knots.append( ( gpx.time[maxidx].strftime("%H:%M:%S"),SCALE*max(speed10s[sel])  ) )
    speed10s[maxidx-10:maxidx+10]=-np.inf
    print(best10s_value_knots[-1])
    
print("\nBest 30s runs (time,avg speed):")
best30s_value_knots=[]
for _ in range(5):
    maxidx=np.argmax(speed30s[sel])
    best30s_value_knots.append( ( gpx.time[maxidx].strftime("%H:%M:%S"),SCALE*max(speed30s[sel])  ) )
    speed30s[maxidx-30:maxidx+30]=-np.inf
    print(best30s_value_knots[-1])

## compute 500 m segments
slices500=[]
best500m_value_s=[]
for idx1,d in enumerate(gpx.distance):
    idx2=np.searchsorted(gpx.distance,d+500)
    if idx2<len(gpx.distance)-1:
        _dist=np.sum(gpx.deltaxy[idx1:idx2])
        _speed=_dist/np.sum(gpx.deltat[idx1:idx2])
        _dur=np.sum(gpx.deltat[idx1:idx2])
        slices500.append((_speed,_dist,_dur,idx1,idx2))
    else:
        slices500.append((np.nan,np.nan,np.nan,np.nan,np.nan))
## now get the minimal (i.e fastest) and disable any overlapping
print("\nBest 500m runs:")
best500m_value_s=[]
for _ in range(5):
    speed,dist,dur,i1,i2=max(slices500)
    ## todo check if gpx.ok[i1:i2].all():
    best500m_value_s.append((speed,dist,dur,i1,i2))
    slices500=[s for s in slices500 if s[-1]<i1 or s[-2]>i2]
    print( (f"{gpx.time[i1].strftime('%H:%M:%S')} to {gpx.time[i2].strftime('%H:%M:%S')} |"
            f"| Duration: {str(dur)}"
            f" | Speed : {SCALE*speed}"
            f" | Distance: {dist}")
        )
    #if SELECT_BEST_500:
    #    sel[i1:i2]=False
    #    gpx['ok'][:]=~gpx.ok
    #    msgwrap.message("SELECTION_CHANGED",emitter=sh)


    
