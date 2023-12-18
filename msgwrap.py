#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# msgwrap is a simple wrapper around several message dispatching interfaces
# supported interfaces are :
#   + smokesignal
#   + pydisptach
#   + pypubsub

#import sys
#this could be determined dynamically with try:except:
#__backend__='smokesignal'
#__backend__='pydispatch'
#__backend__='pypubsub'

backends=[]
try:
    import smokesignal
    backends.append('smokesignal')
except ImportError:
    pass
try:
    import pydispatch
    backends.append('pydispatch')
except ImportError:
    pass
try:
    import pubsub
    backends.append('pypubsub')
except ImportError:
    pass
        
assert len(backends)>0,"Could not find suitable signal backend \nPlease install either PubSub or Pydispatcher or SmokeSignal"
__backend__=backends[0]
print("Using %s signal backend" % __backend__)

if __backend__=='pydispatch':
    from pydispatch import dispatcher 
    def register(callback,signal):
        dispatcher.connect(callback, signal=signal, sender=dispatcher.Any)

    def message(signal,*args,**kwargs):
        dispatcher.send(signal,*args,**kwargs)

elif __backend__=='pypubsub':
    try:
        from pubsub import setupkwargs
    except ImportError:
        pass
    from pubsub import pub
    
    def register(callback,signal):
        pub.subscribe(callback,signal)

    def message(signal,*args,**kwargs):
        pub.sendMessage(signal,*args,**kwargs)

elif __backend__=='smokesignal':
    import smokesignal
    def message(signal,*args,**kwargs):
        smokesignal.emit(signal,*args,**kwargs)

    def register(callback,signal):
        smokesignal.on(signal, callback)
