
SIGNALS = {
'reload':       10,
'stop-request': 11,
'close-gui':    12,
'stop-request': 13,

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
'instrument-added': 42,	# name
'instrument-removed':43,# name
'instrument-changed':44,# sender.get_name(), changes
'item-added':       45, 	# name
}
