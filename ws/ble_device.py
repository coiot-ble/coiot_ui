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

    def __getattr__(self, name):
        try:
            return self.__getattribute__(name)
        except AttributeError:
            return getattr(self.proxy, name)

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

class DBusBluez(DBusNode):
    def __init__(self):
        super().__init__(pydbus.SystemBus(), 'org.bluez')

    @property
    def adapters(self):
        return self.get_children('^hci\d+', DBusAdapter)

class DBusAdapter(DBusNode):
    @property
    def devices(self):
        return self.get_children('^dev_', DBusDevice, key=lambda n,d: d.proxy.Address)

class DBusDevice(DBusNode):
    @property
    def services(self):
        return self.get_children('^service', DBusGattService, key=lambda n,s: s.proxy.UUID)

class DBusGattService(DBusNode):
    @property
    def characteristics(self):
        return self.get_children('^char', DBusGattCharacteristic, key=lambda n,c: c.proxy.UUID)

class DBusGattCharacteristic(DBusNode):
    pass

if __name__ == "__main__":
    from coiot import BleClient

    hci0 = DBusBluez().adapters['hci0']
    hci0.proxy.Powered = True

    ble = BleClient(hci0)
    ble.connect()

    for a, d in ble.devices.items():
        print('device', a)
        for u, s in d.services.items():
            print('\t', u)
    print(ble.get_services_by_uuid(0x1815))
    cc = ble.get_characteristics_by_uuid(0x1815, 0x2a56)
    print(cc)
    for c in cc.values():
        print(c.proxy.ReadValue({}))
        c.proxy.WriteValue([0], {})
