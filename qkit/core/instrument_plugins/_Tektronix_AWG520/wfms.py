import numpy
import types
from plot import plot as qtplot

def plot(wfm, m=None):
    '''
    bla
    '''

    if type(wfm) is types.ListType:
        pass
    elif type(wfm) is types.TupleType and len(wfm) == 3:
        wfm = numpy.add(numpy.multiply(wfm[0],wfm[1]),wfm[2])
    else:
        raise ValueError("did not receive understandable waveform")

    if m is not None:
        p = qtplot(wfm, name='AWG520',
                xlabel='samle #', ylabel='amplitude (raw or volts)',
                clear=True, update=False)
        p = qtplot(m, name='AWG520')
    else:
        p = qtplot(wfm, name='AWG520',
                xlabel='samle #', ylabel='amplitude (raw or volts)',
                clear=True)

def create_edge(clock, risetime, risetype, from_level, to_level):
    '''
    bla
    '''

    if risetime == 0:
        return []

    numpoints = clock * risetime + 2

    if risetype == '' or risetype == 'lin':
        edge = numpy.linspace(from_level, to_level, numpoints)
        return edge[1:-1]

    if risetype == 'sin':
        edge = (-1*numpy.cos(numpy.linspace(0,numpy.pi,numpoints))/2.0+0.5)*(to_level-from_level)+from_level
        return edge[1:-1]

    raise ValueError("specified risetype did not match any of available types")

def Marker_Single_Pulse(clock, period, start, width):
    '''
    bla
    '''

    numpoints = int(round(period*clock))
    numstart = int(round(start*clock))
    numstop = int(round((start+width)*clock))

    wfm = numpy.zeros(numpoints, int)
    wfm[numstart:numstop]=1

    return wfm.tolist()

def Marker_Double_Pulse(clock, period, start1, width1, start2, width2):
    '''
    bla
    '''

    numpoints = int(round(period*clock))
    numstart1 = int(round(start1*clock))
    numstop1 = int(round((start1+width1)*clock))
    numstart2 = int(round(start2*clock))
    numstop2 = int(round((start2+width2)*clock))

    wfm = numpy.zeros(numpoints, int)
    wfm[numstart1:numstop1]=1
    wfm[numstart2:numstop2]=1

    return wfm.tolist()

def Marker_Zeros(numpoints):
    '''
    bla
    '''

    wfm = numpy.zeros(numpoints,int)
    return wfm.tolist()

def Marker_Ones(numpoints):
    '''
    bla
    '''

    wfm = numpy.ones(numpoints,int)
    return wfm.tolist()

def Channel_Zeros(numpoints):
    '''
    bla
    '''
    wfm = numpy.zeros(numpoints)
    return wfm.tolist()

def Channel_Triangle(clock, period):
    '''
    bla
    '''
    numpoints = int(round(period*clock))

    x1 = numpy.arange(0,1,2.0/numpoints)
    x2 = numpy.arange(1,0,-2.0/numpoints)
    wfm = numpy.append(x1,x2)
    return wfm

def Channel_DC_Offset(clock, period):
    '''
    bla
    '''
    numpoints = int(round(period*clock))
    wfm = numpy.ones(numpoints)
    return wfm

def Channel_Single_Pulse(clock, period, start, width, low, high, amplitude=None, offset=None):
    '''
    bla
    '''

    if (amplitude is None) and (offset is None):
        amplitude = abs((high - low))
        offset = (high + low)/2.0
        b_low = -1
        b_high = 1
    elif (amplitude is not None) and (offset is not None):
        b_low = (low - offset)/(amplitude/2.0)
        b_high = (high - offset)/(amplitude/2.0)
        if abs(b_low) > 1 or abs(b_high) > 1:
            raise ValueError("low and/or high level out of bounds for chosen offset and amplitude")
    else:
        raise ValueError("amplitude and offset must both be defined, or both not")

    numpoints = int(round(period*clock))
    numstart = int(round(start*clock))
    numstop = int(round((start+width)*clock))

    wfm = b_low * numpy.ones(numpoints)
    wfm[numstart:numstop] = b_high

    wfm = wfm.tolist()

    wfm_all = (wfm, amplitude, offset)
    return wfm_all


def Channel_TwoLevel_Pulse(clock, period, start, width):
    '''
    bla
    '''

    return False


def Channel_MultiLevel_Pulse(clock, period, pulsedef, amplitude=None, offset=None):
    '''
    pulsedef is a list of tuples.
    The first tuple is special. It contains 4 elements:
    (base_leve, rise_time, rise_type, starttime) -  Note that the rise_time and rise_type
                                                    are for the *last* edge in the sequence
                                                    of plateaus
    All following tuples (at least one is required) define the plateaus in the pulse:
    (level, rise_time, rise_type, width) -  rise_time and rise_type are for the edge preceding
                                            plateau.
    '''
    if len(pulsedef) < 2:
        raise ValueError("at least one level (besides baselevel) needs to be specified")

    level_list = [a[0] for a in pulsedef]
    nr_of_plateaus = len(pulsedef) - 1
    max_level = max(level_list)
    min_level = min(level_list)

    if (amplitude is None) and (offset is None):
        amplitude = abs((max_level - min_level))
        offset = (max_level + min_level)/2.0
    elif (amplitude is not None) and (offset is not None):
        pass
    else:
        raise ValueError("amplitude and offset must both be defined, or both not")

    b_level_list = numpy.divide(numpy.subtract(level_list,offset),(amplitude/2.0))
    if numpy.max(numpy.abs(b_level_list)) > 1+1e-12:
        raise ValueError("one of the levels is out of range for chosen amplitude and offset")

    numpoints = int(round(period*clock))
    base_level = b_level_list[0]
    wfm = base_level * numpy.ones(round(pulsedef[0][3]*clock))

    for i in range(1,nr_of_plateaus +1):
        from_level = b_level_list[i-1]
        to_level = b_level_list[i]
        risetime = pulsedef[i][1]
        risetype = pulsedef[i][2]
        width = pulsedef[i][3]

        numrisetime=int(round(risetime*clock))
        numwidth=int(round(width*clock))

        edge = create_edge(clock, risetime, risetype, from_level, to_level)
        plateau = to_level * numpy.ones(numwidth)
        both = numpy.append(edge, plateau)

        wfm = numpy.append(wfm, both)
        last_plateau_level = to_level


    last_risetime = pulsedef[0][1]
    last_risetype = pulsedef[0][2]

    last_edge = create_edge(clock, last_risetime, last_risetype, last_plateau_level, base_level)
    last_plateau = b_level_list[0] * numpy.ones(numpoints - len(wfm) - len(last_edge))
    last_both = numpy.append(last_edge, last_plateau)
    wfm = numpy.append(wfm, last_both)

    wfm = wfm.tolist()
    wfm_all = (wfm, amplitude, offset)
    return wfm_all
