import gtk

class QTTable(gtk.TreeView):

    def __init__(self, colinfo, model):
        gtk.TreeView.__init__(self)

        self.set_model(model)

        self.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        self.set_headers_visible(True)

        self._colinfo = colinfo

        index = 0
        for colname, options in colinfo:
            renderer = gtk.CellRendererText()
            for item in ('size', 'scale'):
                if item in options:
                    renderer.set_property(item, options[item])

            column = gtk.TreeViewColumn(colname, renderer, text=index)
            self.append_column(column)

            index += 1
