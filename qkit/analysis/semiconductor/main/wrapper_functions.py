import traceback

def do_monitored(func):
    def wrapper(self):
        try:
            func(self)
        except:
            error_msg = traceback.format_exc()
            self.view.show_error_msg(error_msg)

    return wrapper