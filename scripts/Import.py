import pandas as pd

class ExecInterrupt(Exception):
    pass

def __scriptmain__():
    if gpx is None:
        print("You must have one gpx file opened to import another one!")
    try:
        filename,dt=query("Choose file to Import",	\
                    [('wxfile','Filename',"Any compatible file|*.fit;*.gpx;*.gpx;*.csv;*.csv.gz;*.tsz;*.tsv.gz",'','str'),
                     ('wxspin','Resample (s)',"1|30|1",int(round(gpx.deltat).mode()),'int')
                    ],
                    control_size=(200,-1)
                    )
    except:
        return
    
    ## we'll work on a copy of our gpxfile*
    ogpx=gpx.copy().set_index('time')
    ngpx=app.frame.OpenFile(filename,resample=f"{dt}s").set_index('time')
    ngpxfields='|'.join([c for c in ngpx.columns if c not in ['ok','time','idx','deltat','seconds']])
    joinstyle='Outer'
    ngpxsuffix='_1'
    try:
        ngpxfields,joinstyle,ngpxsuffix=query("Import options",
                                   [('wxchecklist','Choose fields to import',ngpxfields,'lat|lon|speed|heading','str'),
                                    ('wxcombo','Merge policy','Outer|Inner|Keep|Async',joinstyle,'str'),
                                    ('wxentry','Suffix',None,ngpxsuffix,'str')
                                   ],
                                   control_size=(200,-1)
                                   )
        ngpxfields=ngpxfields.split('|')
        #ngpxfields='lat|lon|speed|heading'.split('|')
    except:
        return
    ## resample dataframes if required
    if resample!=int(round(gpx.deltat).mode()):
        ogpx=ogpx.resample(rule=f"{dt}s",origin=ogpx.index[0]).fillna(method='bfill').fillna(method='ffill')
    ngpx=ngpx.resample(rule=f"{dt}s",origin=ogpx.index[0]).fillna(method='bfill').fillna(method='ffill')
    
    ## filter new dataframe and rename columns to make sure we don't have collisions with column names
    ngpx=ngpx[[c for c in ngpxfields]].rename(columns={c:c+ngpxsuffix for c in ngpxfields})
    
    ## merge dataframes according to join style
    if joinstyle in ['Outer','Inner','Keep','Async']:
        if joinstyle=='Outer':
            merged=pd.concat([ogpx,ngpx],axis=1,join='outer')
        elif joinstyle=='Inner':
            merged=pd.concat([ogpx,ngpx],axis=1,join='inner')
        elif joinstyle=='Keep':
            merged=pd.concat([ogpx,ngpx],axis=1,join='outer')
            merged=merged[merged.index.isin(ogpx.index)]
        elif joinstyle=='Async':
            merged=pd.concat([ogpx.reset_index(drop=True),ngpx.reset_index(drop=True)],axis=1)
            nperiods=max(len(ngpx),len(ogpx))
            merged['time']=pd.date_range(start=ogpx.index[0],periods=nperiods,freq=f'{dt}s')
            merged.set_index('time')
    
    ## clearnup some columns
    merged['ok']=True
    merged['idx']=range(len(merged))
    try:
        merged['deltat']=duration(merged.index).apply(lambda x:x.total_seconds())
    except:
        merged['deltat']=duration(merged.index).apply(lambda x:pd.Timedelta(x).total_seconds())
    merged['seconds']=np.cumsum(merged.deltat)
    merged.fillna(method='ffill',inplace=True)
    merged.fillna(method='bfill',inplace=True)
    app.frame.AttachGpx(merged.reset_index())

__scriptmain__()