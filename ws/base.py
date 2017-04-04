devices = {
    "1": {
        "type": "oven",
        "on": False,
        "image": lambda d: "oven_2.png" if not d['on'] else "oven_2_on.png"
        },
    "2": {
        "type":"lamp",
        "on": False,
        "image": lambda d: "light_2.png" if not d['on'] else "light_2_on.png"
        },
    "3": {
        "type":"speaker",
        "on": False,
        "image": "speaker_2.png"
        },
    "4": {
        "type":"coffee machine",
        "on": False,
        "image": lambda d: "coffee_machine_2.png" if not d['on'] else "coffee_machine_2_on.png"
        }
}

class CoiotWsError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.code = 500

class SubNotFound(CoiotWsError):
    def __init__(self, name, value, accept):
        super().__init__("unknown "+name+": "+value)
        self.name = name
        self.value = value
        self.accept = accept
        self.code = 404

class CoiotWs:
    def __init__(self):
        pass

    def route_sub_get(self, path, name, description, **accept):
        if len(path) == 0:
            return {'name': name, 'description': description, 'accept': list(accept.keys())}
        p, psub = path[0], path[1:]
        for k,v in accept.items():
            if p == k:
                return v[0](psub, *v[1])
        raise SubNotFound(name, p, accept)

    def route_sub_set(self, path, data, name, **accept):
        if len(path) == 0:
            return {'name': name, 'description': description, 'accept': list(accept.keys())}
        p, psub = path[0], path[1:]
        for k,v in accept.items():
            if p == k:
                return v[0](psub, data, *v[1])
        raise SubNotFound(name, p, accept)

    def get_single_device(self, path, d):
        return self.route_sub_get(path,
                "attribute", "attribute to get from the device",
                **{ k: (lambda p, d, a: a(d) if callable(a) else a, [d, v]) for (k,v) in d.items() },
                **{"*": (lambda p, d: {n: v if not callable(v) else v(d) for (n,v) in d.items() }, [d])})

    def set_single_device(self, path, data, d):
        p = path[0]
        if p == "*":
            assert(type(data) is dict)
            assert(all(type(data[k]) is type(d[k]) for k in data.keys()))
            for k,v in data.items():
                d[k] = v
        else:
            assert(p in d)
            assert(type(data) is type(d[p]))
            d[p] = data

    def set_multiple_devices(self, path, data, devices):
        p = path[0]
        assert(type(data) is dict)
        if p == '*':
            for d in devices.values():
                self.set_single_device(path, data, d)
        else:
            for k in data.keys():
                self.set_single_device(path, data[k], devices[k])

    def get_device(self, path, devices):
        return self.route_sub_get(path,
                "device", "device from which to get an attribute",
                **{ k: (self.get_single_device, [v]) for (k,v) in devices.items() },
                **{"*": (lambda p, d: {k: self.get_single_device(p, v) for (k,v) in d.items() }, [devices])})

    def set_device(self, path, data, devices):
        return self.route_sub_set(path, data, "device",
                **{ k: (self.set_single_device, [v]) for (k,v) in devices.items() },
                **{"*": (self.set_multiple_devices, [devices])})

    def get_v1(self, path):
        return self.route_sub_get(path,
                "category", "category of attribute to get",
                device = (self.get_device, [devices]))

    def set_v1(self, path, data):
        return self.route_sub_set(path, data, "version",
                device = (self.set_device, [devices]))

    def get(self, request):
        path = [p for p in request.split("/") if p != ""]
        return self.route_sub_get(path[1:],
                "version", "version of the protocol to use",
                v1 = (self.get_v1, []))

    def set(self, request, data):
        path = [p for p in request.split("/") if p != ""]
        return self.route_sub_set(path[1:], data, "version",
                v1 = (self.set_v1, []))
