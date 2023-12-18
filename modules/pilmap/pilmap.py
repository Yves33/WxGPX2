#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# adapted from https://github.com/sinapsi/wxpymaps/

import warnings, logging
import pathlib,requests,shutil,queue   ## suggestion use https://github.com/JohnPaton/ratelimitqueue
from threading import Thread
from functools import lru_cache
from io import BytesIO
from itertools import cycle
from PIL import Image, ImageDraw, ImageFont

MPI=3.141592653589793
import math
try:
    import numpy as np
    _atan=np.arctan
    _atan2=np.arctan2
    _tan=np.tan
    _log=np.log
    _exp=np.exp
    _cos=np.cos
    _sin=np.sin
    _sqrt=np.sqrt
    _isnan=np.isnan
except:
    _atan=math.atan
    _atan2=math.atan2
    _tan=math.tan
    _log=math.log
    _exp=math.exp
    _cos=math.cos
    _sin=math.sin
    _sqrt=math.sqrt
    _isnan=math.isnan

## map src format: ("friendly-name", "url/{x}/{y}/{z}/{q}","cache_dir")
#{x}{y}{z}{q} will be replaced with computed values of zoom, longitude, latitude or quadkey
# a list of possible urls can be found on https://leaflet-extras.github.io/leaflet-providers/preview/
# these values may change periodically - you can renew them using the monitor console from your web browser
#"https://khms2.google.com/kh/v=147&x={0}&y={1}&z={2}"
#"https://www.google.com/maps/vt/pb=!1m4!1m3!1i{2}!2i{0}!3i{1}!2m3!1e0!2sm!3i258145710"
#"https://c.tile.thunderforest.com/outdoors/{z}/{x}/{y}.png"
#"http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
MAPSRC=[
("Google maps",                 "http://mt1.google.com/vt/lyrs=m@132&hl=en&x={x}&y={y}&z={z}","google_maps"),\
("Google terrain",              "http://mt1.google.com/vt/lyrs=t&x={x}&y={y}&z={z}","google_terrain"),\
("Google terrain+maps",         "http://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}","google_terrain_maps"),\
("Google satellite",            "http://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}","google_satellite"),\
("Google satellite+maps",       "http://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}","google_satellite_maps"),\
("Open street maps",            "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png","openstreetmaps"),\
("Open cycle maps",             "http://b.tile.opencyclemap.org/cycle/{z}/{x}/{y}.png","opencyclemaps"),\
("Open public transport",       "http://tile.xn--pnvkarte-m4a.de/tilegen/{z}/{x}/{y}.png","openpublictransport"),\
("Virtual earth maps",          "http://a1.ortho.tiles.virtualearth.net/tiles/r{q}.jpeg?g=50","virtualearth_maps"),\
("Virtual earth satellite",     "http://a1.ortho.tiles.virtualearth.net/tiles/a{q}.jpeg?g=50","virtualearth_satellite"),\
("Virtual earth satellite+maps","http://a1.ortho.tiles.virtualearth.net/tiles/a{q}.jpeg?g=50","virtualearth_satellite_maps"),\
]

## utility functions directly copied from globalmaptiles.py
def Haversine(lat1,lon1,lat2,lon2):
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    radius = 6378137    #meters
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1))* math.cos(math.radians(lat2))*math.sin(dlon/2)*math.sin(dlon/2)
    dist = radius*2 * _atan2(math.sqrt(a), math.sqrt(1-a))
    ## calculate heading
    dlon=lon2-lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(dlon))
    heading=(math.degrees(_atan2(x,y))+360)%360
    return (dist,heading)
    
def LatLonToMeters(lat, lon ):
    mx = lon * (MPI*6378137) / 180.0
    my = _log( _tan((90 + lat) * MPI / 360.0 )) / (MPI / 180.0)
    my = my * (MPI*6378137) / 180.0
    return mx, my

def MetersToPixels(mx, my, zoom):
    px = (mx + (MPI*6378137)) / (2*MPI*6378137/(256*(2**zoom)))
    py = (my + (MPI*6378137)) / (2*MPI*6378137/(256*(2**zoom)))
    return px, py

def MetersToLatLon(mx, my ):
    lon = (mx / (MPI*6378137)) * 180.0
    lat = (my / (MPI*6378137)) * 180.0
    lat = 180 / MPI * (2 * _atan( _exp( lat * MPI / 180.0)) - MPI / 2.0)
    return lat, lon

def PixelsToMeters(px, py, zoom):
    mx = px * (2*MPI*6378137/(256*(2**zoom))) - (MPI*6378137)
    my = py * (2*MPI*6378137/(256*(2**zoom))) - (MPI*6378137)
    return mx, my

def PixelsToLatLon(x,y,zoom):
    mx, my = PixelsToMeters(x, y, zoom)
    lat, lon = MetersToLatLon(mx, my)
    return -lat, lon

def LatLonToPixels(lat,lon,zoom):
    mx, my = LatLonToMeters(lat, lon)
    x, y = MetersToPixels(mx, my, zoom)
    y = ((2 ** zoom) * 256) - y
    return x, y

def quad_key( tx, ty, zoom ): ## some tile (e.g bing maps) providers use quadkey instead of x,y,z
    quadKey = ""
    for i in range(zoom, 0, -1):
        digit = 0
        mask = 1 << (i-1)
        if (tx & mask) != 0:
            digit += 1
        if (ty & mask) != 0:
            digit += 2
        quadKey += str(digit)
    return quadKey

class GeoTileMap:
    def __init__(self,width=640,height=480,center_lat = 44.8404400,center_lon = -0.5805000,zoom=10,provider=None,tripplebuffered=False):
        self.center_lat=center_lat
        self.center_lon=center_lon
        self.zoom_factor=zoom
        self.provider=provider
        self.layers={}
        self.tripplebuffered=tripplebuffered
        self.resize(width,height)

    def resize(self,width,height):
        self.width=width
        self.height=height
        self.bg=Image.new("RGB",(width,height))
        if len(self.layers)>0:
            self.fg=self.bg.copy()
        else:
            self.fg=self.bg
        if self.tripplebuffered:
            self.topmost=self.fg.copy()
        self.__calcbbox()

    def lookat(self,lat=None,lon=None,zoom=None):
        self.center_lat=lat if lat else self.center_lat
        self.center_lon=lon if lon else self.center_lon
        self.zoom_factor=zoom if zoom else self.zoom_factor
        self.__calcbbox()

    def zoomat(self,x=None,y=None,zinc=1):
        if x is None and y is None:
            x=self.width//2
            y=self.height//2
        self.center_lat,self.center_lon=PixelsToLatLon(x+self.left,y+self.top,self.zoom_factor)
        self.zoom_factor=max(0,min(self.zoom_factor+zinc,22)) ## make sure zoom is clamped between 0 and 22
        ## get new pixel coordinates for center, so that the same point stays at the same place
        center_x,center_y=LatLonToPixels(self.center_lat,self.center_lon,self.zoom_factor)
        center_x+=self.width/2-x
        center_y+=self.height/2-y
        self.center_lat,self.center_lon=PixelsToLatLon(center_x,center_y,self.zoom_factor)
        self.__calcbbox()

    def translate(self,dx,dy):
        center_x,center_y=LatLonToPixels(self.center_lat,self.center_lon,self.zoom_factor)
        center_x-=dx
        center_y-=dy
        self.center_lat,self.center_lon=PixelsToLatLon(center_x,center_y,self.zoom_factor)
        self.__calcbbox()

    def screentogeo(self,x,y):
        return PixelsToLatLon(x+self.left,y+self.top,self.zoom_factor)

    def geotoscreen(self,lat,lon):
        tx,ty=LatLonToPixels(lat,lon,self.zoom_factor)
        tx-=self.left
        ty-=self.top
        return tx,ty
        
    def geotoscreen_v(self,lat,lon):
        ## vectorized version. requires numpy
        try:
            zoom=self.zoom_factor
            left=self.left
            top=self.top
            oshift=math.pi * 6378137
            res=(MPI*6378137)/ (128*2**zoom)
            _y = np.log(np.tan((lat+90.0)*MPI/360.0)) / (MPI/180.0) *( oshift / 180 )
            _x = lon * oshift / 180.0
            _x=(_x+oshift)/res
            _y=(_y+oshift)/res
            _x=_x-left
            _y=((2 ** zoom) * 256)-_y-top
            return _x,_y
        except:
            xy=list(map(self.parent.geotoscreen,self.lat,self.lon))
            return zip(*xy)  ## zip(*iterable) is its own inverse
        
    def enclose(self,latmin,lonmin,latmax,lonmax):
        for z in range(0,22):
            t,l=LatLonToPixels(latmin,lonmin,z)
            b,r=LatLonToPixels(latmax,lonmax,z)
            if math.fabs(l-r)>self.width or math.fabs(b-t)>self.height:
                z=z-1
                break
        self.center_lat=(latmin+latmax)/2
        self.center_lon=(lonmin+lonmax)/2
        self.zoom_factor=z
        self.__calcbbox()

    def __calcbbox(self):
        self.center_x,self.center_y=LatLonToPixels(self.center_lat ,self.center_lon ,self.zoom_factor)
        self.left=self.center_x-self.width/2
        self.right=self.center_x+self.width/2
        self.top=self.center_y-self.height/2
        self.bottom=self.center_y+self.height/2
        # calculate tile limits
        self.tile_left=int(math.floor(self.left/256))
        self.tile_right=int(math.ceil(self.right/256))
        self.tile_top=int(math.floor(self.top/256))
        self.tile_bottom=int(math.ceil(self.bottom/256))
        self.ori_x=int(self.tile_left*256-self.left)
        self.ori_y=int(self.tile_top*256-self.top)
        self.pixelscale=6378137*2*MPI*math.cos(math.radians(self.center_lat))/(2**(self.zoom_factor+8))
    
    def update(self,tile=None,force=False):
        success=True
        for x,ht in enumerate(range(self.tile_left,self.tile_right)):
            for y,vt in enumerate(range (self.tile_top,self.tile_bottom)):
                if tile is None or (ht,vt)==tile: ##filter for partial updates
                    try:
                        img=self.provider.gettile(ht,vt,self.zoom_factor,force)
                        self.bg.paste(img,(x*256+self.ori_x,y*256+self.ori_y))
                    except:
                        success=False
        if not self.fg is self.bg:
            self.fg.paste(self.bg,(0,0))
            for layer in self.layers.values():
                layer.draw()
        return success

    def prefetch(self,zinc=2,fake=True):
        lat1,lon1=self.screentogeo(0,0)
        lat2,lon2=self.screentogeo(self.width,self.height)
        for z in range(self.zoom_factor, self.zoom_factor+zinc+1):
            start_x, start_y = tuple(int(x/256) for x in LatLonToPixels(lat1,lon1,z))
            stop_x, stop_y = tuple(int(x/256) for x in LatLonToPixels(lat2,lon2,z))
            # obviously, caching entire area will generate lots of tiles - just print what would be downloaded
            logging.getLogger().critical(f"Zoom level:{z} ,tile count: {stop_x-start_x} x  {stop_y-start_y} = {(stop_x-start_x)*(stop_y-start_y)} tiles")
            for x in range(start_x,stop_x+1):
                for y in range(start_y, stop_y+1):
                    logging.getLogger().critical(f"Downloading tile: {self.provider.cachedir}/{x}-{y}-{z}.png")
                    if not fake:
                        try: ## because gettile generates an exception if the tile is not present, we need to enclose in try block
                            self.provider.gettile(x,y,z)
                        except:
                            pass

    @property 
    def image(self):
        if not self.tripplebuffered:
            return self.fg
        else:
            self.topmost.paste(self.fg,(0,0))
            for layer in self.layers.values():
                layer.animate()
            return self.topmost

class MapLayer:
    def __init__(self,parent):
        self.parent=parent
        self.visible=True
        self.active=False ## reserved for interactivity
        self.zorder=-1    ## may be used one day!
    def draw(self):pass
    def animate(self):pass                  ## only for interactivity
    def onmousemove(self,x,y):pass        ## only for interactivity
    def onmousedown(self,x,y,btn=1):pass  ## only for interactivity
    def onmouseup(self,x,y,btn=1):pass    ## only for interactivity
    
class GeoScaleLayer(MapLayer):
    def __init__(self,parent,color=(255,255,255),offset=(20,20),captionoffset=20,linewidth=4):
        super().__init__(parent)
        self.color=color
        self.ox,self.oy=offset
        self.linewidth=linewidth
        self.captionoffset=captionoffset

    def draw(self):
        if self.visible:
            pixelscale=self.parent.pixelscale
            width,height=self.parent.width,self.parent.height
            scalebarmeters=10**math.floor(math.log(width*pixelscale,10))
            scalebarpixels=scalebarmeters/pixelscale
            # reduce scale bar so it is not more than 150px
            while scalebarpixels>150:
                scalebarmeters/=2
                scalebarpixels/=2
            # adjust units to km or m
            if scalebarmeters>999.99:
                caption=str(scalebarmeters/1000)+ " km"
            else:
                caption=str(scalebarmeters)+ " m"
            pen=ImageDraw.Draw(self.parent.fg)
            pen.line([(self.ox,height-self.oy),(self.ox+scalebarpixels,height-self.oy)], 
                     fill=self.color, 
                     width=self.linewidth, 
                     joint=None)
            pen.text((self.ox,height-self.oy-self.captionoffset),caption,fill=(255,255,255))

class GeoBasePathLayer(MapLayer):
    def __init__(self,parent,lat,lon,
                 color=[(255,255,255)],linewidth=1,joint='curve',dotsize=0.0,
                 dashed=False,numbers=False):
        super().__init__(parent)
        self.color=color
        self.linewidth=linewidth
        self.joint=joint
        self.lat=lat
        self.lon=lon
        self.dotsize=dotsize
        self.x,self.y=None,None
        self.textoffset=(6,6)
        self.dashed=dashed   ## in some cases, we may need our path to be draw as dashed lines
        self.numbers=numbers

    def draw(self):
        if self.visible and len(self.lat)>0 and len(self.lon)>0:
            pen=ImageDraw.Draw(self.parent.fg)
            try: ## lat and lon may be either array-like or lists
                xy=list(zip(*self.parent.geotoscreen_v(self.lat,self.lon)))
            except:
                xy=list(map(self.parent.geotoscreen,self.lat,self.lon))
            colorcycler=cycle(self.color) ## cyclers cannot be reset in python
            x1,y1=xy[0]
            for e,(x2,y2) in enumerate(xy[1:]):
                if not self.dashed or not e%2:
                    pen.line([(x1,y1),(x2,y2)],
                            fill=next(colorcycler), 
                            width=self.linewidth, 
                            joint=self.joint)
                x1,y1=x2,y2
            if self.dotsize:
                colorcycler=cycle(self.color)
                for x,y in xy:
                    pen.ellipse([x-self.dotsize/2,y-self.dotsize/2,x+self.dotsize/2,y+self.dotsize/2],
                                fill=next(colorcycler))
            if self.numbers:
                colorcycler=cycle(self.color)
                for e,(x,y) in enumerate(xy):
                    if not self.dashed:
                        pen.text((x+self.textoffset[0],y+self.textoffset[1]),str(e),fill=next(colorcycler))
                    else:
                        pen.text((x+self.textoffset[0],y+self.textoffset[1]),str(e//2),fill=next(colorcycler))

##quick & dirty polygon manipulation routines
def translate(p,h,v):
    return [(x+h,y+v) for x,y in p]
def scale(p,h,v):
    return [(x*h,y*v) for x,y in p]
def rotate(p,theta):
    return [(x*_cos(theta)-y*_sin(theta), x*_sin(theta)+y*_cos(theta)) for x,y in p]

class GeoAnimPathLayer(GeoBasePathLayer):
    def __init__(self,*args,**kwargs):
        self.tracker=kwargs.pop('tracker',[(0,2),(-4,4),(0,-5),(4,4)])
        self.trackercolor=kwargs.pop('trackercolor',(0,0,255))
        self.heading=kwargs.pop('heading',None)
        super().__init__(*args,**kwargs)
        
        if self.heading is None and len(self.lat)>0:
            self.heading=list(map(Haversine,self.lat[:-1],self.lon[:-1],self.lat[1:],self.lon[1:]))
            self.heading=[t[1]*0.0174533 for t in self.heading]+[self.heading[-1][1]*0.0174533]

    def animate(self):
        if not self.visible:
            return

        pen=ImageDraw.Draw(self.parent.topmost)
        if len(self.lat)>0 and (self.x,self.y) != (None,None):
            lat,lon=self.parent.screentogeo(self.x,self.y)
            dist=list(map(Haversine,self.lat,self.lon,[lat]*len(self.lat),[lon]*len(self.lat) ))
            idx=dist.index(min(dist))
            x,y=self.parent.geotoscreen(self.lat[idx],self.lon[idx])
            theta=self.heading[idx]
            pen.polygon(translate(scale(rotate(self.tracker,theta),
                                        2,2),
                                  x,y),
                        fill=self.trackercolor)
                        
    def onmousemove(self,x,y):
        self.x,self.y=x,y

class GeoWaypointLayer(GeoBasePathLayer):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def onmousedown(self,x,y,btn):
        if not self.active:
            return
        if btn==1:
            lat,lon=self.parent.screentogeo(x,y)
            try:
                self.lat.append(lat)
                self.lon.append(lon)
            except:
                self.lat=np.append(self.lat,lat)
                self.lon=np.append(self.lon,lon)
                
        elif btn==3:
            try: ## lat and lon may be either array-like or lists
                xy=list(zip(*self.parent.geotoscreen_v(self.lat,self.lon)))
            except:
                xy=list(map(self.parent.geotoscreen,self.lat,self.lon))
            for e,(_x,_y) in enumerate(xy):
                d=_sqrt( (x-_x)**2+(y-_y)**2 )
                if not self.dashed and d<self.dotsize:
                    try:
                        self.lat.pop(e)
                        self.lon.pop(e)
                    except:
                        self.lat=np.delete(self.lat,e)
                        self.lon=np.delete(self.lon,e)
                    break
                elif self.dashed and d<self.dotsize:
                    odd=(e//2)*2
                    try:
                        if odd+1<len(self.lat):
                            self.lat.pop(odd+1)
                            self.lon.pop(odd+1)
                        self.lat.pop(odd)
                        self.lon.pop(odd)
                    except:
                        if odd+1<len(self.lat):
                            self.lat=np.delete(self.lat,odd+1)
                            self.lon=np.delete(self.lon,odd+1)
                        self.lat=np.delete(self.lat,odd)
                        self.lon=np.delete(self.lon,odd)
                    break
                    
    def distance(self):
        d=0
        for e in range(len(self.lat)-1):
            d+=Haversine(self.lat[e],self.lon[e],self.lat[e+1],self.lon[e+1])[0]
        return d
    
class SimpleGeoTileProvider:
    '''minimal code. no cache, no thread!
    '''
    def __init__(self,baseurl="http://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"):
        self.baseurl=baseurl

    def gettile(self,x,y,z,force=False,cacheflag=None):
        import time
        time.sleep(0.05)
        url=self.baseurl.format(x=x,y=y,z=z,q=quad_key(int(x),int(y),int(z)))
        response = requests.get(url)
        return Image.open(BytesIO(response.content))

class DownloadThread(Thread):
    def __init__(self,downloadqueue,useragent='',notifyfunc=lambda x,y:None,):
        Thread.__init__(self)
        self.downloadqueue=downloadqueue
        self.useragent=useragent
        self.notify=notifyfunc

    def run(self):
        while True:
            imgurl,imgpath, x, y, z = self.downloadqueue.get()
            if imgurl=='quit':
                break
            try:
                response = requests.get(imgurl, stream=True,headers={'User-Agent': self.useragent})
                with open(imgpath, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                self.notify(x,y)
            except queue.Empty:
                pass
            self.downloadqueue.task_done()
        return

class ThreadedGeoTileProvider:
    def __init__(self,mapsrc,cachedir=None,useragent='',notifyfunc=None,numthreads=5):
        self.map_src=mapsrc
        self.cachedir=cachedir if cachedir else pathlib.Path.home()/".WxMapwidget"/"cache"
        try:
            self.cachedir.mkdir(parents=True,exist_ok=True)
        except FileExistsError:
            pass
        self.numthreads=numthreads
        self.downloadqueue=queue.LifoQueue(maxsize=0)
        self.useragent=useragent
        self.threads=[]
        for i in range(self.numthreads):                  ## not sure we need that many threads!
            self.threads.append(DownloadThread(self.downloadqueue,
                                                useragent,
                                                notifyfunc))
            self.threads[-1].name = str(i)
            self.threads[-1].start()

    ## when using @lru_cache,changing provider requires cleaning lru_cache using gettile.cache_clear()
    ## alternatively, you could pass any flag (e.g url) to force separating caches
    @lru_cache(maxsize=None)
    def gettile(self,x,y,z,force=False,cacheflag=None):
        imgpath=self.cachedir/self.map_src[2]/f"{x}-{y}-{z}.png"
        (self.cachedir/self.map_src[2]).mkdir(exist_ok=True)
        imgurl=self.map_src[1].format(x=x,y=y,z=z,q=quad_key(int(x),int(y),int(z)))
        if imgpath.exists() and not force:
            try:
                return Image.open(imgpath) ## should return io.Bytesio and delegate image decoding to map (then remove lru_cache)?
            except:
                self.downloadqueue.put((imgurl,imgpath,x,y,z))
                raise Exception('') ## prevent caching
        else:
            #t=Timer(0.5, self.downloadqueue.put,args=[(imgurl,imgpath,x,y,z), ])
            #t.start()
            self.downloadqueue.put((imgurl,imgpath,x,y,z))
            raise Exception('') ## prevent caching
        
    def kill(self):
        for _ in range(200):
            self.downloadqueue.put(("quit","",-1,-1,-1))
        for t in range(len(self.threads)):
            self.threads[t].join()

    def clearcache(self):
        for p in pathlib.Path(self.cachedir/self.map_src[2]).glob('*.png'):
            p.unlink()
            
if __name__=='__main__':
    USERAGENT="Mozilla/5.0 (X11; Fedora; Linux) Gecko/20100101 Firefox/63.0"
    ImageDraw.ImageDraw.font = ImageFont.truetype("/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",size=15)
    
    def snapshot(NW=(44.79083,-1.31583),SE=(44.79083,-1.31583),maxsize=640):
        provider=SimpleGeoTileProvider()
        map=GeoTileMap(provider=provider)
        map.resize((2*maxsize,2*maxsize))
        map.enclose(*NW,*SE)
        map.update()
        l,t=map.geotoscreen(*NW)
        r,b=map.geotoscreen(*SE)
        map.bg.crop([l,t,r,b]).thumbnail([maxsize,maxsize],PIL.Image.ANTIALIAS).show()
        exit(0)
    #######
    def test():
        provider=ThreadedGeoTileProvider(MAPSRC[0],
                                     useragent=USERAGENT,
                                     notifyfunc=lambda x,y:print(f"Tile {x},{y} is now ready!") or map.update((x,y))
                                     )
        map=GeoTileMap(provider=provider)
        map.layers['scalebar']=GeoScaleLayer(map)
        map.resize(640,480)
        map.zoomat(320,0,1)
        map.update()
        map.image.show()
        map.provider.kill()
        exit(0)
    test()
