# MP/AS @ KIT 05/2017
# JSON en-/decoder for non-JSON standard data-types

import json
import types
import numpy as np
import qkit
                
class QkitJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) == np.ndarray:
            return {'dtype' : type(obj).__name__, 'content' : obj.tolist()}
        if type(obj) == types.InstanceType:
            return {'dtype' : type(obj).__name__, 'content': str(obj.get_name())}
        try:
            return obj._json()
        except AttributeError:
            return {'dtype' : type(obj).__name__, 'content' : json.JSONEncoder.default(self, obj)}

class QkitJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if obj.has_key('content') and obj.has_key("dtype") and len(obj)==2:
            if obj['dtype'] == 'ndarray':   return np.array(obj['content'])
            if obj['dtype'] == 'instance' or obj['dtype']=='qkitInstrument':  return qkit.instruments.get(obj['content'])
        else:
            return obj 