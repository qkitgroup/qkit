import gtk

class OrderedVBox(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self)
        self._items = []

    def _rebuild(self):
        self.hide()

        for i in self:
            self.remove(i)

        self._items.sort()
        for orderid, item in self._items:
            self.pack_start(item, True, True)

        self.show_all()

    def add(self, item, orderid=1000, rebuild=True):
        self._items.append((orderid, item))
        if rebuild:
            self._rebuild()

