#!/usr/bin/env python

import pydbus

from xml.etree import ElementTree
import re

class DBusNode:
    def __init__(self, bus, service, path=None):
        self.bus = bus
        self.service = service
        if path is None:
            path = '/' + service.replace('.','/')
        self.path = path

    @property
    def proxy(self):
        if 'proxy' not in self.__dict__:
            self.__dict__['proxy'] = self.bus.get(self.service, self.path)
        return self.__dict__['proxy']

    def clear_cache(self):
        del self.__dict__['proxy']

    def get_children(self, filt, Cls, key=lambda n,v: n):
        children = {}
        for n in [e.attrib['name'] for e in ElementTree.fromstring(self.proxy.Introspect()) if e.tag == 'node']:
            if re.match(filt, n):
                v = Cls(self.bus, self.service, self.path+'/'+n)
                children[key(n,v)] = v
        return children

    def __repr__(self):
        return '{}({}, \'{}\', \'{}\')'.format(type(self).__name__, self.bus, self.service, self.path)

class DBusCoiot(DBusNode):
    def __init__(self):
        super().__init__(pydbus.SystemBus(), 'org.coiot')

    @property
    def devices(self):
        return self.get_children('.*', DBusCoiotDevice)

class DBusCoiotDevice(DBusNode):
    pass
