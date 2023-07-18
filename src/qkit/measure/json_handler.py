# MP/AS @ KIT 05/2017
# JSON en-/decoder for non-JSON standard data-types

import json
import types
import numpy as np
import logging
import qkit
try:
    if qkit.module_available('uncertainties'):
        import uncertainties
        uncertainties_enable = True
    else:
        uncertainties_enable = False
except AttributeError:
    try:
        import uncertainties
        uncertainties_enable = True
    except ImportError:
        uncertainties_enable = False

class QkitJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) == np.ndarray:
            return {'dtype': type(obj).__name__, 'content': obj.tolist()}
        # if type(obj) == types.InstanceType:  # no valid synatx in python 3 and probably not needed (MMW)
        #    return {'dtype' : type(obj).__name__, 'content': str(obj.get_name())}
        if uncertainties_enable or qkit.module_available('uncertainties'):
            if type(obj) in (uncertainties.core.Variable, uncertainties.core.AffineScalarFunc):
                return {'dtype': 'ufloat',
                        'content': {'nominal_value': obj.nominal_value,
                                    'std_dev': obj.std_dev}}
        try:
            return obj._json()
        except AttributeError:
            return {'dtype': type(obj).__name__, 'content': json.JSONEncoder.default(self, obj)}


class QkitJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if 'content' in obj and 'dtype' in obj and len(obj) == 2:
            if obj['dtype'] == 'ndarray':
                return np.array(obj['content'], dtype=object)
            if obj['dtype'] == 'ufloat':
                if uncertainties_enable or qkit.module_available('uncertainties'):
                    return uncertainties.ufloat(nominal_value=obj['content']['nominal_value'],
                                                std_dev=obj['content']['std_dev'])
                else:
                    logging.warning('Uncertainties package not installed. Only nominal value returned.')
                    return float(obj['content']['nominal_value'])
            if obj['dtype'] == 'qkitInstrument':  # or obj['dtype'] == 'instance'
                return qkit.instruments.get(obj['content'])
        else:
            return obj 