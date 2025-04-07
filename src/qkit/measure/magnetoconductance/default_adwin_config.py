# default config for adwin
# 'hard wired' configuration of the adwin and accessories
default_hard_config = {
            'no_output_channels': 8,
            'outputs': {
                'bx': {'card': 3, 'channel': 1, 'scale': 0.995, 'unit': 'T', 'bits':16},
                'by': {'card': 3, 'channel': 3, 'scale': 0.945, 'unit': 'T', 'bits':16},
                'bz': {'card': 3, 'channel': 5, 'scale': 1.265, 'unit': 'T', 'bits':16},
                'vg': {'card': 3, 'channel': 7, 'scale': 10, 'unit': 'V', 'bits':16},
                'vd': {'card': 3, 'channel': 8, 'scale': 10, 'unit': 'V', 'bits':16}
                },
            'inputs': {
                'id': {'card': 2, 'channel': 7, 'scale': 10, 'unit': 'A', 'bits': 18}
                }
            }
        # between measurement 'switchable' configuration of adwin accessories 
default_soft_config = {
            'vdivs': {'vg':0.5, 'vd':0.01},
            'iv_gain': {'id':1e8},
            'readout_channel': 'id'
        }