# -*- coding: utf-8 -*-
"""
Remote interface client (RIC) to access the RI service or any zerorpc service


@author: HR,AS@KIT 2018

To use the client to control a qkit instance, just open a new notebook and execute the following:
    
    import qkit.core.lib.com.ri_client as rc
    rc.control_panel(rc.start_ric())
    
"""
import qkit

#import logging # the logging mechanism does not work here, since qkit is not started



def __update_tab(ric):
    # try to be smart and add the remote functions to the __dict__ for tabbing in ipython
    rflist = ric._zerorpc_list()
    for f in rflist: 
        ric.__dict__.update({f:getattr(ric,f)})

def __getdoc():
    return _zerorpc_help
    
    
def start_ric(host = None,port = None):
    import zerorpc
    """
    starts a remote interface client (ric)
    to a 
        host = host (default =  localhost)
    at a 
        port  = port (default =  5700)
    
    ric is based on zerorpc, so every zerorpc server should be accessible
    
    """
    ric = zerorpc.Client(); 
    if not host:
        host = qkit.cfg.get("ris_host","127.0.0.1")
    if not port:
        port = qkit.cfg.get("ris_port",5700)
    print("starting ric client on host %s and port %s" % (host,port))
    ric.connect("tcp://" + host + ":" + str(port))
    
    qkit.ric = ric    
    __update_tab(ric)
    
    return ric

"""
list of internal functions
_zerorpc_list to list calls
_zerorpc_name to know who you’re talking to
_zerorpc_ping (redundant with the previous one)
_zerorpc_help to retrieve the docstring of a call
_zerorpc_args to retrieve the argspec of a call
_zerorpc_inspect to retrieve everything at once
"""


def control_panel(ric = None):
    from ipywidgets import Button, HTML,HBox,Accordion
    from IPython.core.display import display
    def fmt(inp):
        if inp is None:
            return "--"
        elif type(inp) is float:
            return "{:.4g}".format(inp)
        else:
            return str(inp)

    if ric is None:
        ric = qkit.ric

    def update_instrument_params(b):
        insdict = ric.get_all_instrument_params()
        for ins in sorted(insdict):
            if not ins in b.accordions:
                b.accordions[ins] = Accordion()
            table = "<table style='line-height:180%'>"  # <tr style='font-weight:bold'><td> Parameter </td><td>Value</td></tr>
            for p in sorted(insdict[ins]):
                table += "<tr><td style='text-align:right;padding-right:10px'>" + str(p) + "</td><td>" + fmt(insdict[ins][p][0]) + insdict[ins][p][
                    1] + "</td></tr>"
            table += """</table>"""
            b.accordions[ins].children = [HTML(table)]
            b.accordions[ins].set_title(0, ins)
        for child in b.accordions.keys():
            if child not in insdict:
                del b.accordions[child]
        b.hbox.children = b.accordions.values()

    update_button = Button(description="Update")
    update_button.on_click(update_instrument_params)
    update_button.accordions = {}
    update_button.hbox = HBox()
    stop_button = Button(description="Stop measurement")
    stop_button.on_click(lambda b: qkit.ric.stop_measure())
    stop_button.button_style = "danger"
    update_instrument_params(update_button)
    display(HBox([update_button,stop_button]),update_button.hbox)
