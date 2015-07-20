from subprocess import Popen, PIPE
def plot(h5_filepath, datasets=[], refresh = 5, live = True, echo = False):
    ds = ""
    for s in datasets: ds+=s+","
    ds = ds.strip(",")

    cmd = "python"
    cmd += " -m qkit.gui.qviewkit.main"
    options =  " -f " + h5_filepath.encode("string-escape")
    if ds:
        options += " -ds "+ str(ds)
    options += " -rt "+ str(refresh)
    if live:
        options += " -live "

    if echo:
        print "Qviewkit open cmd: "+ cmd + options
        print Popen(cmd+options, shell=True, stdout=PIPE).stdout.read()
    else:
        Popen(cmd+options, shell=True)