
SIGNALS = {
'info':         5,
'update':       10,
'reload':       11,
'stop-request': 12,
'close-gui':    13,
'changed':          14, # self._changed

'measurement-start':20,
'measurement-end':  21,
'measurement-idle': 22,
'new-data-point':   23,
'new-data-block':   24,

'removed':          30, 		# self.get_name()
'parameter-added':  32,	# name
'parameter-removed':33,	# name
'parameter-changed':34,	# name


'tags-added':       40, #newtags
'instrument-added': 41,	# name
'instrument-removed':42,# name
'instrument-changed':43,# sender.get_name(), changes
'item-added':       44, 	# name
}
