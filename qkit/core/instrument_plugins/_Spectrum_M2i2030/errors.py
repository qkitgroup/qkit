class errors():
    # ***********************************************************************
    #
    # SpcErr.h = (c) Spectrum GmbH, 2006
    #
    # ***********************************************************************
    #
    # error codes of the Spectrum drivers. Until may 2004 this file was
    # errors.h. Name has been changed because errors.h has been already in
    # use by windows.
    #
    # ***********************************************************************

    ERR_OK = 0x0000  # 0 No Error
    ERR_INIT = 0x0001  # 1 Initialisation error
    ERR_NR = 0x0002  # 2 Board number out of range
    ERR_TYP = 0x0003  # 3 Unknown board Typ
    ERR_FNCNOTSUPPORTED =0x0004  # 4 This function is not supported by the hardware
    ERR_BRDREMAP = 0x0005  # 5 The Board Index Remap table is wrong
    ERR_KERNELVERSION = 0x0006  # 6 The kernel version and the dll version are mismatching
    ERR_HWDRVVERSION = 0x0007  # 7 The driver version doesn't match the minimum requirements of the board
    ERR_ADRRANGE = 0x0008  # 8 The address range is disabled (fatal error)
    ERR_INVALIDHANDLE = 0x0009  # 9 Handle not valid
    ERR_BOARDNOTFOUND = 0x000A  # 10 Card mit given name hasn't been found
    ERR_BOARDINUSE = 0x000B  # 11 Card mit given name is already in use by another application
    ERR_LASTERR = 0x0010  # 16 Old Error waiting to be read
    ERR_ABORT = 0x0020  # 32 Abort of wait function
    ERR_BOARDLOCKED = 0x0030  # 48 Board acess already locked by another process. it's not possible to acess one board through multiple processes

    ERR_REG = 0x0100  #256 unknown Register for this Board
    ERR_VALUE = 0x0101  #257 Not a possible value in this state
    ERR_FEATURE = 0x0102  #258 Feature of the board not installed
    ERR_SEQUENCE = 0x0103  #259 Channel sequence not allowed
    ERR_READABORT = 0x0104  #260 Read not allowed after abort
    ERR_NOACCESS = 0x0105  #261 Access to this register denied
    ERR_POWERDOWN = 0x0106  #262 not allowed in Powerdown mode
    ERR_TIMEOUT = 0x0107  #263 timeout occured while waiting for interrupt
    ERR_CALLTYPE = 0x0108  #264 call type (int32 mux) is not allowed for this register
    ERR_EXCEEDSINT32 = 0x0109  #265 return value is int32 but software register exceeds the 32 bit integer range -> use 2x32 or 64
    ERR_NOWRITEALLOWED = 0x010A  #267 register cannot be written, read only
    ERR_SETUP = 0x010B  #268 the setup isn't valid
    ERR_CHANNEL = 0x0110  #272 Wrong number of Channel to be read out
    ERR_NOTIFYSIZE = 0x0111  #273 Notify block size isn't valid
    ERR_RUNNING = 0x0120  #288 Board is running, changes not allowed
    ERR_ADJUST = 0x0130  #304 Auto Adjust has an error
    ERR_PRETRIGGERLEN = 0x0140  #320 pretrigger length exceeds allowed values
    ERR_DIRMISMATCH = 0x0141  #321 direction of card and memory transfer mismatch
    ERR_POSTEXCDSEGMENT= 0x0142  #322 posttrigger exceeds segment size in multiple recording mode
    ERR_SEGMENTINMEM = 0x0143  #323 memsize is not a multiple of segmentsize, last segment hasn't full length
    ERR_MULTIPLEPW = 0x0144  #324 multiple pulsewidth counters used but card only supports one at the time
    ERR_NOCHANNELPWOR = 0x0145  #325 channel pulsewidth can't be OR'd
    ERR_ANDORMASKOVRLAP= 0x0146  #326 AND mask and OR mask overlap in at least one channel -> not possible
    ERR_ANDMASKEDGE = 0x0147  #327 AND mask together with edge trigger mode is not allowed
    ERR_ORMASKLEVEL = 0x0148  #328 OR mask together with level trigger mode is not allowed
    ERR_EDGEPERMOD = 0x0149  #329 All trigger edges must be simular on one module
    ERR_DOLEVELMINDIFF = 0x014A  #330 minimum difference between low output level and high output level not reached
    ERR_STARHUBENABLE = 0x014B  #331 card holding the star-hub must be active for sync
    ERR_PATPWSMALLEDGE = 0x014C  #332 Combination of pattern with pulsewidht smaller and edge is not allowed

    ERR_NOPCI = 0x0200  #512 No PCI bus found
    ERR_PCIVERSION = 0x0201  #513 Wrong PCI bus version
    ERR_PCINOBOARDS = 0x0202  #514 No Spectrum PCI boards found
    ERR_PCICHECKSUM = 0x0203  #515 Checksum error on PCI board
    ERR_DMALOCKED = 0x0204  #516 DMA buffer in use, try later
    ERR_MEMALLOC = 0x0205  #517 Memory Allocation error
    ERR_EEPROMLOAD = 0x0206  #518 EEProm load error, timeout occured
    ERR_CARDNOSUPPORT = 0x0207  #519 no support for that card in the library

    ERR_FIFOBUFOVERRUN = 0x0300  #768 Buffer overrun in FIFO mode
    ERR_FIFOHWOVERRUN = 0x0301  #769 Hardware buffer overrun in FIFO mode
    ERR_FIFOFINISHED = 0x0302  #770 FIFO transfer hs been finished. Number of buffers has been transferred
    ERR_FIFOSETUP = 0x0309  #777 FIFO setup not possible, transfer rate to high (max 250 MB/s)

    ERR_TIMESTAMP_SYNC = 0x0310  #784 Synchronisation to ref clock failed
    ERR_STARHUB = 0x0320  #800 Autorouting of Starhub failed

    ERR_INTERNAL_ERROR = 0xFFFF  #65535 Internal hardware error detected, please check for update


