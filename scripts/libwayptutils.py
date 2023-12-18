#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

'''
for some unknown reason, mapview is not visible when using import wayptutils from shell.
in order to use these functions, you must use sh.run(scriptdir/"_wayptutils.py")
'''

def savegates(layer='gates'):
    '''
    returns a zipped list of (latitudes,longitude) from specified layer
    '''
    return list(zip(mapview.map.layers[layer].lat,mapview.map.layers[layer].lon))
    
def loadgates(gates,layer='gates'):
    '''
    updates specified map layer with a list of (latitudes, longitudes=
    '''
    mapview.map.layers[layer].lat,mapview.map.layers[layer].lon=map(list,zip(*gates))
    mapview.map.update()
    mapview.UpdateDrawing()