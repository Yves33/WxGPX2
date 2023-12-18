## adjust colormap for tracks
mapview.layers["track1"].colors=[tuple(int(t*255) for t in colorsys.hsv_to_rgb(h,1.0,1.0)) for h in np.linspace(240/360,0/360,256)]
## generate new time series
gpx['newtime']=pd.date_range(start='1/1/2023',periods=len(gpx),freq='s')
## time shift dataframe
gpx['time']=gpx['time']+pd.Timedelta(seconds=5)
## merge two files sharing timestamps, renaming duplicated columns
## display a second track in map panel
## remove track from map panel
## add an annotation to map.layer
#mapview.map.layers["track1"].animcb=lambda(self,DC:...)
## download elevation data
## merge with heartrate,power, etc...
