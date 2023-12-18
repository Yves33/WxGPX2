from xml.dom import minidom
import os

if not 'sh' in locals().keys():
    ## this enables the script to run outside wxgpx
    import sys
    sys.path.insert(0,"./")
    sys.path.insert(0,"./modules")
    from wxquery import WxQuery as query
    import wx
    from gpxutils import *

def splitgpx():
    try:
        filename,=query("Choose file to split",	\
                    [('wxfile','Filename','Gpx (*.gpx)|*.gpx',os.getcwd()+'/data/defiwind2007.gpx','str'),
                    ],
                    control_size=(200,-1)
                    )
    except:
        return
    doc=minidom.parse(filename)
    doc.normalize()
    tracks={}
    for e,trk in enumerate(doc.documentElement.getElementsByTagName('trk')):
        try:
            name = trk.getElementsByTagName('name')[0].firstChild.data
        except:
            name=f'track_{e}'
        tracks[e]=name.replace(' ','_')
    try:
        tracklist,=query("Select tracks to export",
                        [('wxchecklist','Choose tracks to export','|'.join(tracks.values()),'','str')])
    except:
        return
    tracklist=[k for k,v in tracks.items() if v in tracklist.split('|')]
    for t in tracklist:
        savename=filename.replace(".gpx",'_'+tracks[t]+'.gpx')
        df=parsegpxfile(filename,trkname=f"track_{t}")
        df.rename(columns={c:c.split(':')[-1] for c in df.columns if ':' in c},inplace=True)
        savegpxfile(df,savename,name=tracks[t])
        print(savename)
    print("Done!")

if not 'sh' in locals().keys():
    app = wx.App(False)
    splitgpx()
    app.MainLoop()
else:
    splitgpx()