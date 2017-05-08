import gtk
import gobject
import os

class DirectoryTree(gtk.VBox):

    def __init__(self, dir=None, show_hidden=False):
        gtk.VBox.__init__(self)

        self._show_hidden = show_hidden

        self._scroll = gtk.ScrolledWindow()
        self._scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add(self._scroll)

        self._store = gtk.TreeStore(gobject.TYPE_STRING)
        self._view = gtk.TreeView(self._store)
        self._view.connect('row-expanded', self._row_expanded_cb)
        self._view.connect('row-collapsed', self._row_collapsed_cb)
        self._scroll.add(self._view)

        self._column = gtk.TreeViewColumn()
        cell = gtk.CellRendererPixbuf()
        self._column.pack_start(cell, False)

#        cellrenderer.set_property('pixbuf-expander-open',
#                gdk.Pixbuf(open)
#        cellrenderer.set_property('pixbuf-expander-closed',
#                gdk.Pixbuf(closed)

        cell = gtk.CellRendererText()
        self._column.pack_start(cell, True)
        self._column.set_attributes(cell, text=0)
        self._view.append_column(self._column)

        self._view.connect('row-activated', self._row_activated_cb)

        if dir is not None:
            self.open_dir(dir)

    def _add_files(self, nodes):
        nodes.append([])

    def _walk_dir(self, dir, node, depth=1):
        '''
        Add files / directories and recurse a maximum of <depth> levels.
        Directories at the maximum depth get a placeholder entry so that
        they are still shown as expandable entries.
        '''

        # Directory might not be accessible
        try:
            entries = os.listdir(dir)
        except:
            return

        dirs = []
        files = []
        for i in entries:
            if not self._show_hidden and i.startswith('.'):
                continue

            fullname = os.path.join(dir, i)
            if os.path.isdir(fullname):
                dirs.append(i)
            else:
                files.append(i)

        dirs.sort()
        for i in dirs:
            fullname = os.path.join(dir, i)
            newnode = self._store.append(node, (i, ))
            path = self._store.get_path(newnode)
            self._nodes[path] = {'fullname': fullname}
            if depth > 1:
                self._walk_dir(fullname, newnode, depth=depth-1)
            else:
                self._nodes[path]['placeholder'] = \
                        self._store.append(newnode, ('', ))

        files.sort()
        for i in files:
            fullname = os.path.join(dir, i)
            newnode = self._store.append(node, (i, ))
            path = self._store.get_path(newnode)
            self._nodes[path] = {'fullname': fullname}

    def open_dir(self, dir):
        if not os.path.isdir(dir):
            return False
        self.set_title(dir)
        self._store.clear()
        self._nodes = {}
        self._walk_dir(dir, None)

    def set_title(self, title):
        self._title = title
        self._column.set_title(title)

    def _row_expanded_cb(self, sender, iter, path):
        '''
        Callback when a row is expanded.
        If a placeholder is present for an entry, walk that directory and
        re-expand the row.
        '''

        if path not in self._nodes:
            return
        info = self._nodes[path]
        if 'placeholder' not in info:
            return

        del self._store[info['placeholder']]
        del info['placeholder']
        dir = info['fullname']
        self._walk_dir(dir, iter, depth=1)

        self._view.expand_row(path, False)

    def _row_collapsed_cb(self, sender, iter, path):
        return

    def _row_activated_cb(self, view, path, column):
        if path not in self._nodes:
            return
        filename = self._nodes[path]['fullname']
        self.emit('file-activated', filename)

gobject.signal_new("file-activated", DirectoryTree,
        gobject.SIGNAL_RUN_FIRST,
        None, (str,))

if __name__ == '__main__':
    tree = DirectoryTree('/')
    win = gtk.Window()
    win.set_size_request(300, 600)
    win.add(tree)
    win.show_all()
    gtk.main()

