try:
    import numpy as np
    import time
    import ipywidgets as widgets
    from IPython.display import display
    
    class Stopwatch(object):
        def __init__(self):
            self.sw = widgets.Label(value=time.strftime('%H:%M:%S', time.gmtime(0)),
                                    description='elapsed time',
                                    #layout=widgets.Layout(**{}),
                                    #style={},
                                    disabled=True)
            display(self.sw)
        
        def update(self, value):
            if type(value) is str:
                self.sw.value = value
            else:
                self.sw.value = time.strftime('%H:%M:%S', time.gmtime(value))
            
                    
except ImportError as e:
    print('ipywidgets could not be imported')