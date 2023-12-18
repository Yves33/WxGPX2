#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

kts={"u_scale":1.94384,"u_sym":'kts'}
kmh={"u_scale":3.6,"u_sym":"km/h"}
mph={"u_scale":0.44704,"u_sym":"mph"}
m={"u_scale":1.0,"u_sym":"m"}
km={"u_scale":0.001,"u_sym":"km"}
mi={"u_scale":0.000621371,"u_sym":"mi"}
nmi={"u_scale":0.000539957,"u_sym":"nmi"}
ft={"u_scale":3.28084,"u_sym":"ft"}
ms={"u_scale":1.0,"u_sym":"m/s"}
ms2={"u_scale":1.0,"u_sym":"m/s²"}
s={"u_scale":1.0,"u_sym":"s"}
si={"u_scale":1.0,"u_sym":"S.I"}
deg={"u_scale":1.0,"u_sym":"deg"}
hhmmss={"u_scale":1.0,"u_sym":"hh:mm:ss"}

unit_dict={"m/s":ms,
	   'kts':kts,
       "km/h":kmh,
       "mph":mph,
       "m":m,
	   "ft":ft,
       "km":km,
	   "mi":mi,
       "nmi":nmi,
       "m/s²":ms2,
       "s":s,
       "s.i":si,
       "deg":deg,
	   "hh:mm:ss":hhmmss
       }
    
import pandas as pd

def attrs_save(df):
    return{k:v.attrs.copy() for k,v in df.items()}

def attrs_load(df,attrs):
    for k,v in attrs.items():
        if k in df.columns:
            df[k].attrs.update(v)

@pd.api.extensions.register_series_accessor("unit")
class UnitAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    @property
    def scaled(self):
        try:
            return self._obj*self._obj.attrs['u_scale']
        except:
            return self._obj

    @property
    def sym(self):
        try:
            return self._obj.attrs['u_sym']
        except:
            return 's.i'
        
    @property
    def legend(self):
        try:
            return self._obj.name+' ('+self._obj.attrs['u_sym']+')'
        except:
            return self._obj.name+' (s.i)'

    def use(self,u):
        if isinstance(u,dict):
            self._obj.attrs.update(u)
        elif isinstance(u,str):
            self._obj.attrs.update(unit_dict[u])

'''@pd.api.extensions.register_dataframe_accessor("unit")
class UnitAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def save(self):
        return {k:v.attrs.copy() for k,v in self._obj.items()}

    def restore(self,attrs):
        if attrs:
            for k,v in attrs.items():
                if k in self._obj.columns and "u_sym" in v.keys():
                    self._obj[k].unit.use(v["u_sym"])
                    #self._obj[k].attrs.update(v)
                else:
                    print("no u_sym attribute for key ",k,v)
        else:
            print("attrs is empty")'''
            
