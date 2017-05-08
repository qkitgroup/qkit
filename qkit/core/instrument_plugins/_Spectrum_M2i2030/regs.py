#regs.py

class regs():

    #  ***********************************************************************
    #
    #  regs.h = (c) Spectrum GmbH, 2006
    #
    #  ***********************************************************************
    #
    #  software register and constants definition for all Spectrum drivers.
    #  Please stick to the card manual to see which of the inhere defined
    #  registers are used on your hardware.
    #  =
    #  ***********************************************************************



    #  ***********************************************************************
    #  macros for kilo, Mega or Giga as standard version or binary (_B) (2^x)
    #  ***********************************************************************

    # mcs: Perhaps this needs to be fixed
    #KILO(k) = (1000 * k)
    #MEGA(m) = (1000 * 1000 * m)
    #GIGA(g) = (1000 * 1000 * 1000 * g)
    #KILO_B(k) = (1024 * k)
    #MEGA_B(m) = (1024 * 1024 * m)
    #GIGA_B(g) = ((uint64) 1024 * 1024 * 1024 * g)


    # #Self created!!!
    SPCM_BUF_DATA = 1000
    SPCM_DIR_PCTOCARD = 0
    SPCM_DIR_CARDTOPC = 1




    #  ***********************************************************************
    #  card types
    #  ***********************************************************************

    TYP_PCIDEVICEID = 0x00000000l

    #  ***** Board Types ***************
    TYP_EVAL = 0x00000010l
    TYP_RSDLGA = 0x00000014l
    TYP_GMG = 0x00000018l
    TYP_VAN8 = 0x00000020l
    TYP_VAC = 0x00000028l

    TYP_PCIAUTOINSTALL = 0x000000FFl

    TYP_DAP116 = 0x00000100l
    TYP_PAD82 = 0x00000200l
    TYP_PAD82a = 0x00000210l
    TYP_PAD82b = 0x00000220l
    TYP_PCI212 = 0x00000300l
    TYP_PAD1232a = 0x00000400l
    TYP_PAD1232b = 0x00000410l
    TYP_PAD1232c = 0x00000420l
    TYP_PAD1616a = 0x00000500l
    TYP_PAD1616b = 0x00000510l
    TYP_PAD1616c = 0x00000520l
    TYP_PAD1616d = 0x00000530l
    TYP_PAD52 = 0x00000600l
    TYP_PAD242 = 0x00000700l
    TYP_PCK400 = 0x00000800l
    TYP_PAD164_2M = 0x00000900l
    TYP_PAD164_5M = 0x00000910l
    TYP_PCI208 = 0x00001000l
    TYP_CPCI208 = 0x00001001l
    TYP_PCI412 = 0x00001100l
    TYP_PCIDIO32 = 0x00001200l
    TYP_PCI248 = 0x00001300l
    TYP_PADCO = 0x00001400l
    TYP_TRS582 = 0x00001500l
    TYP_PCI258 = 0x00001600l


    #  ------ series and familiy identifiers -----
    TYP_SERIESMASK = 0x00FF0000l      #  the series (= type of base card), e.g. MI.xxxx
    TYP_VERSIONMASK = 0x0000FFFFl      #  the version, e.g. XX.3012
    TYP_FAMILYMASK = 0x0000FF00l      #  the family, e.g. XX.30xx
    TYP_TYPEMASK = 0x000000FFl      #  the type, e.g. XX.xx12
    TYP_SPEEDMASK = 0x000000F0l      #  the speed grade, e.g. XX.xx1x
    TYP_CHMASK = 0x0000000Fl      #  the channel/modules, e.g. XX.xxx2

    TYP_MISERIES = 0x00000000l
    TYP_MCSERIES = 0x00010000l
    TYP_MXSERIES = 0x00020000l
    TYP_M2ISERIES = 0x00030000l
    TYP_M2IEXPSERIES = 0x00040000l



    #  ----- MI.20xx, MC.20xx, MX.20xx -----
    TYP_MI2020 = 0x00002020l
    TYP_MI2021 = 0x00002021l
    TYP_MI2025 = 0x00002025l
    TYP_MI2030 = 0x00002030l
    TYP_MI2031 = 0x00002031l

    TYP_M2I2020 = 0x00032020l
    TYP_M2I2021 = 0x00032021l
    TYP_M2I2025 = 0x00032025l
    TYP_M2I2030 = 0x00032030l
    TYP_M2I2031 = 0x00032031l

    TYP_M2I2020EXP = 0x00042020l
    TYP_M2I2021EXP = 0x00042021l
    TYP_M2I2025EXP = 0x00042025l
    TYP_M2I2030EXP = 0x00042030l
    TYP_M2I2031EXP = 0x00042031l

    TYP_MC2020 = 0x00012020l
    TYP_MC2021 = 0x00012021l
    TYP_MC2025 = 0x00012025l
    TYP_MC2030 = 0x00012030l
    TYP_MC2031 = 0x00012031l

    TYP_MX2020 = 0x00022020l
    TYP_MX2025 = 0x00022025l
    TYP_MX2030 = 0x00022030l



    #  ----- MI.30xx, MC.30xx, MX.30xx -----
    TYP_MI3010 = 0x00003010l
    TYP_MI3011 = 0x00003011l
    TYP_MI3012 = 0x00003012l
    TYP_MI3013 = 0x00003013l
    TYP_MI3014 = 0x00003014l
    TYP_MI3015 = 0x00003015l
    TYP_MI3016 = 0x00003016l
    TYP_MI3020 = 0x00003020l
    TYP_MI3021 = 0x00003021l
    TYP_MI3022 = 0x00003022l
    TYP_MI3023 = 0x00003023l
    TYP_MI3024 = 0x00003024l
    TYP_MI3025 = 0x00003025l
    TYP_MI3026 = 0x00003026l
    TYP_MI3027 = 0x00003027l
    TYP_MI3031 = 0x00003031l
    TYP_MI3033 = 0x00003033l

    TYP_M2I3010 = 0x00033010l
    TYP_M2I3011 = 0x00033011l
    TYP_M2I3012 = 0x00033012l
    TYP_M2I3013 = 0x00033013l
    TYP_M2I3014 = 0x00033014l
    TYP_M2I3015 = 0x00033015l
    TYP_M2I3016 = 0x00033016l
    TYP_M2I3020 = 0x00033020l
    TYP_M2I3021 = 0x00033021l
    TYP_M2I3022 = 0x00033022l
    TYP_M2I3023 = 0x00033023l
    TYP_M2I3024 = 0x00033024l
    TYP_M2I3025 = 0x00033025l
    TYP_M2I3026 = 0x00033026l
    TYP_M2I3027 = 0x00033027l
    TYP_M2I3031 = 0x00033031l
    TYP_M2I3033 = 0x00033033l

    TYP_M2I3010EXP = 0x00043010l
    TYP_M2I3011EXP = 0x00043011l
    TYP_M2I3012EXP = 0x00043012l
    TYP_M2I3013EXP = 0x00043013l
    TYP_M2I3014EXP = 0x00043014l
    TYP_M2I3015EXP = 0x00043015l
    TYP_M2I3016EXP = 0x00043016l
    TYP_M2I3020EXP = 0x00043020l
    TYP_M2I3021EXP = 0x00043021l
    TYP_M2I3022EXP = 0x00043022l
    TYP_M2I3023EXP = 0x00043023l
    TYP_M2I3024EXP = 0x00043024l
    TYP_M2I3025EXP = 0x00043025l
    TYP_M2I3026EXP = 0x00043026l
    TYP_M2I3027EXP = 0x00043027l
    TYP_M2I3031EXP = 0x00043031l
    TYP_M2I3033EXP = 0x00043033l

    TYP_MC3010 = 0x00013010l
    TYP_MC3011 = 0x00013011l
    TYP_MC3012 = 0x00013012l
    TYP_MC3013 = 0x00013013l
    TYP_MC3014 = 0x00013014l
    TYP_MC3015 = 0x00013015l
    TYP_MC3016 = 0x00013016l
    TYP_MC3020 = 0x00013020l
    TYP_MC3021 = 0x00013021l
    TYP_MC3022 = 0x00013022l
    TYP_MC3023 = 0x00013023l
    TYP_MC3024 = 0x00013024l
    TYP_MC3025 = 0x00013025l
    TYP_MC3026 = 0x00013026l
    TYP_MC3027 = 0x00013027l
    TYP_MC3031 = 0x00013031l
    TYP_MC3033 = 0x00013033l

    TYP_MX3010 = 0x00023010l
    TYP_MX3011 = 0x00023011l
    TYP_MX3012 = 0x00023012l
    TYP_MX3020 = 0x00023020l
    TYP_MX3021 = 0x00023021l
    TYP_MX3022 = 0x00023022l
    TYP_MX3031 = 0x00023031l



    #  ----- MI.31xx, MC.31xx, MX.31xx -----
    TYP_MI3110 = 0x00003110l
    TYP_MI3111 = 0x00003111l
    TYP_MI3112 = 0x00003112l
    TYP_MI3120 = 0x00003120l
    TYP_MI3121 = 0x00003121l
    TYP_MI3122 = 0x00003122l
    TYP_MI3130 = 0x00003130l
    TYP_MI3131 = 0x00003131l
    TYP_MI3132 = 0x00003132l
    TYP_MI3140 = 0x00003140l

    TYP_M2I3110 = 0x00033110l
    TYP_M2I3111 = 0x00033111l
    TYP_M2I3112 = 0x00033112l
    TYP_M2I3120 = 0x00033120l
    TYP_M2I3121 = 0x00033121l
    TYP_M2I3122 = 0x00033122l
    TYP_M2I3130 = 0x00033130l
    TYP_M2I3131 = 0x00033131l
    TYP_M2I3132 = 0x00033132l

    TYP_M2I3110EXP = 0x00043110l
    TYP_M2I3111EXP = 0x00043111l
    TYP_M2I3112EXP = 0x00043112l
    TYP_M2I3120EXP = 0x00043120l
    TYP_M2I3121EXP = 0x00043121l
    TYP_M2I3122EXP = 0x00043122l
    TYP_M2I3130EXP = 0x00043130l
    TYP_M2I3131EXP = 0x00043131l
    TYP_M2I3132EXP = 0x00043132l

    TYP_MC3110 = 0x00013110l
    TYP_MC3111 = 0x00013111l
    TYP_MC3112 = 0x00013112l
    TYP_MC3120 = 0x00013120l
    TYP_MC3121 = 0x00013121l
    TYP_MC3122 = 0x00013122l
    TYP_MC3130 = 0x00013130l
    TYP_MC3131 = 0x00013131l
    TYP_MC3132 = 0x00013132l

    TYP_MX3110 = 0x00023110l
    TYP_MX3111 = 0x00023111l
    TYP_MX3120 = 0x00023120l
    TYP_MX3121 = 0x00023121l
    TYP_MX3130 = 0x00023130l
    TYP_MX3131 = 0x00023131l



    #  ----- MI.40xx, MC.40xx, MX.40xx -----
    TYP_MI4020 = 0x00004020l
    TYP_MI4021 = 0x00004021l
    TYP_MI4022 = 0x00004022l
    TYP_MI4030 = 0x00004030l
    TYP_MI4031 = 0x00004031l
    TYP_MI4032 = 0x00004032l

    TYP_M2I4020 = 0x00034020l
    TYP_M2I4021 = 0x00034021l
    TYP_M2I4022 = 0x00034022l
    TYP_M2I4028 = 0x00034028l
    TYP_M2I4030 = 0x00034030l
    TYP_M2I4031 = 0x00034031l
    TYP_M2I4032 = 0x00034032l

    TYP_M2I4020EXP = 0x00044020l
    TYP_M2I4021EXP = 0x00044021l
    TYP_M2I4022EXP = 0x00044022l
    TYP_M2I4028EXP = 0x00044028l
    TYP_M2I4030EXP = 0x00044030l
    TYP_M2I4031EXP = 0x00044031l
    TYP_M2I4032EXP = 0x00044032l

    TYP_MC4020 = 0x00014020l
    TYP_MC4021 = 0x00014021l
    TYP_MC4022 = 0x00014022l
    TYP_MC4030 = 0x00014030l
    TYP_MC4031 = 0x00014031l
    TYP_MC4032 = 0x00014032l

    TYP_MX4020 = 0x00024020l
    TYP_MX4021 = 0x00024021l
    TYP_MX4030 = 0x00024030l
    TYP_MX4031 = 0x00024031l



    #  ----- MI.45xx, MC.45xx, MX.45xx -----
    TYP_MI4520 = 0x00004520l
    TYP_MI4521 = 0x00004521l
    TYP_MI4530 = 0x00004530l
    TYP_MI4531 = 0x00004531l
    TYP_MI4540 = 0x00004540l
    TYP_MI4541 = 0x00004541l

    TYP_M2I4520 = 0x00034520l
    TYP_M2I4521 = 0x00034521l
    TYP_M2I4530 = 0x00034530l
    TYP_M2I4531 = 0x00034531l
    TYP_M2I4540 = 0x00034540l
    TYP_M2I4541 = 0x00034541l

    TYP_MC4520 = 0x00014520l
    TYP_MC4521 = 0x00014521l
    TYP_MC4530 = 0x00014530l
    TYP_MC4531 = 0x00014531l
    TYP_MC4540 = 0x00014540l
    TYP_MC4541 = 0x00014541l

    TYP_MX4520 = 0x00024520l
    TYP_MX4530 = 0x00024530l
    TYP_MX4540 = 0x00024540l



    #  ----- MI.46xx, MC.46xx, MX.46xx -----
    TYP_MI4620 = 0x00004620l
    TYP_MI4621 = 0x00004621l
    TYP_MI4622 = 0x00004622l
    TYP_MI4630 = 0x00004630l
    TYP_MI4631 = 0x00004631l
    TYP_MI4632 = 0x00004632l
    TYP_MI4640 = 0x00004640l
    TYP_MI4641 = 0x00004641l
    TYP_MI4642 = 0x00004642l
    TYP_MI4650 = 0x00004650l
    TYP_MI4651 = 0x00004651l
    TYP_MI4652 = 0x00004652l

    TYP_M2I4620 = 0x00034620l
    TYP_M2I4621 = 0x00034621l
    TYP_M2I4622 = 0x00034622l
    TYP_M2I4630 = 0x00034630l
    TYP_M2I4631 = 0x00034631l
    TYP_M2I4632 = 0x00034632l
    TYP_M2I4640 = 0x00034640l
    TYP_M2I4641 = 0x00034641l
    TYP_M2I4642 = 0x00034642l
    TYP_M2I4650 = 0x00034650l
    TYP_M2I4651 = 0x00034651l
    TYP_M2I4652 = 0x00034652l

    TYP_M2I4620EXP = 0x00044620l
    TYP_M2I4621EXP = 0x00044621l
    TYP_M2I4622EXP = 0x00044622l
    TYP_M2I4630EXP = 0x00044630l
    TYP_M2I4631EXP = 0x00044631l
    TYP_M2I4632EXP = 0x00044632l
    TYP_M2I4640EXP = 0x00044640l
    TYP_M2I4641EXP = 0x00044641l
    TYP_M2I4642EXP = 0x00044642l
    TYP_M2I4650EXP = 0x00044650l
    TYP_M2I4651EXP = 0x00044651l
    TYP_M2I4652EXP = 0x00044652l

    TYP_MC4620 = 0x00014620l
    TYP_MC4621 = 0x00014621l
    TYP_MC4622 = 0x00014622l
    TYP_MC4630 = 0x00014630l
    TYP_MC4631 = 0x00014631l
    TYP_MC4632 = 0x00014632l
    TYP_MC4640 = 0x00014640l
    TYP_MC4641 = 0x00014641l
    TYP_MC4642 = 0x00014642l
    TYP_MC4650 = 0x00014650l
    TYP_MC4651 = 0x00014651l
    TYP_MC4652 = 0x00014652l

    TYP_MX4620 = 0x00024620l
    TYP_MX4621 = 0x00024621l
    TYP_MX4630 = 0x00024630l
    TYP_MX4631 = 0x00024631l
    TYP_MX4640 = 0x00024640l
    TYP_MX4641 = 0x00024641l
    TYP_MX4650 = 0x00024650l
    TYP_MX4651 = 0x00024651l



    #  ----- MI.47xx, MC.47xx, MX.47xx -----
    TYP_MI4710 = 0x00004710l
    TYP_MI4711 = 0x00004711l
    TYP_MI4720 = 0x00004720l
    TYP_MI4721 = 0x00004721l
    TYP_MI4730 = 0x00004730l
    TYP_MI4731 = 0x00004731l

    TYP_M2I4710 = 0x00034710l
    TYP_M2I4711 = 0x00034711l
    TYP_M2I4720 = 0x00034720l
    TYP_M2I4721 = 0x00034721l
    TYP_M2I4730 = 0x00034730l
    TYP_M2I4731 = 0x00034731l

    TYP_M2I4710EXP = 0x00044710l
    TYP_M2I4711EXP = 0x00044711l
    TYP_M2I4720EXP = 0x00044720l
    TYP_M2I4721EXP = 0x00044721l
    TYP_M2I4730EXP = 0x00044730l
    TYP_M2I4731EXP = 0x00044731l

    TYP_MC4710 = 0x00014710l
    TYP_MC4711 = 0x00014711l
    TYP_MC4720 = 0x00014720l
    TYP_MC4721 = 0x00014721l
    TYP_MC4730 = 0x00014730l
    TYP_MC4731 = 0x00014731l

    TYP_MX4710 = 0x00024710l
    TYP_MX4720 = 0x00024720l
    TYP_MX4730 = 0x00024730l



    #  ----- MI.60xx, MC.60xx, MX.60xx -----
    TYP_MI6010 = 0x00006010l
    TYP_MI6011 = 0x00006011l
    TYP_MI6012 = 0x00006012l
    TYP_MI6021 = 0x00006021l
    TYP_MI6022 = 0x00006022l
    TYP_MI6030 = 0x00006030l
    TYP_MI6031 = 0x00006031l
    TYP_MI6033 = 0x00006033l
    TYP_MI6034 = 0x00006034l

    TYP_M2I6010 = 0x00036010l
    TYP_M2I6011 = 0x00036011l
    TYP_M2I6012 = 0x00036012l
    TYP_M2I6021 = 0x00036021l
    TYP_M2I6022 = 0x00036022l
    TYP_M2I6030 = 0x00036030l
    TYP_M2I6031 = 0x00036031l
    TYP_M2I6033 = 0x00036033l
    TYP_M2I6034 = 0x00036034l

    TYP_M2I6010EXP = 0x00046010l
    TYP_M2I6011EXP = 0x00046011l
    TYP_M2I6012EXP = 0x00046012l
    TYP_M2I6021EXP = 0x00046021l
    TYP_M2I6022EXP = 0x00046022l
    TYP_M2I6030EXP = 0x00046030l
    TYP_M2I6031EXP = 0x00046031l
    TYP_M2I6033EXP = 0x00046033l
    TYP_M2I6034EXP = 0x00046034l

    TYP_MC6010 = 0x00016010l
    TYP_MC6011 = 0x00016011l
    TYP_MC6012 = 0x00016012l
    TYP_MC6021 = 0x00016021l
    TYP_MC6022 = 0x00016022l
    TYP_MC6030 = 0x00016030l
    TYP_MC6031 = 0x00016031l
    TYP_MC6033 = 0x00016033l
    TYP_MC6034 = 0x00016034l

    TYP_MX6010 = 0x00026010l
    TYP_MX6011 = 0x00026011l
    TYP_MX6021 = 0x00026021l
    TYP_MX6030 = 0x00026030l
    TYP_MX6033 = 0x00026033l



    #  ----- MI.61xx, MC.61xx, MX.61xx -----
    TYP_MI6110 = 0x00006110l
    TYP_MI6111 = 0x00006111l

    TYP_M2I6110 = 0x00036110l
    TYP_M2I6111 = 0x00036111l

    TYP_M2I6110EXP = 0x00046110l
    TYP_M2I6111EXP = 0x00046111l

    TYP_MC6110 = 0x00016110l
    TYP_MC6111 = 0x00016111l

    TYP_MX6110 = 0x00026110l



    #  ----- MI.70xx, MC.70xx, MX.70xx -----
    TYP_MI7005 = 0x00007005l
    TYP_MI7010 = 0x00007010l
    TYP_MI7011 = 0x00007011l
    TYP_MI7020 = 0x00007020l
    TYP_MI7021 = 0x00007021l

    TYP_M2I7005 = 0x00037005l
    TYP_M2I7010 = 0x00037010l
    TYP_M2I7011 = 0x00037011l
    TYP_M2I7020 = 0x00037020l
    TYP_M2I7021 = 0x00037021l

    TYP_M2I7005EXP = 0x00047005l
    TYP_M2I7010EXP = 0x00047010l
    TYP_M2I7011EXP = 0x00047011l
    TYP_M2I7020EXP = 0x00047020l
    TYP_M2I7021EXP = 0x00047021l

    TYP_MC7005 = 0x00017005l
    TYP_MC7010 = 0x00017010l
    TYP_MC7011 = 0x00017011l
    TYP_MC7020 = 0x00017020l
    TYP_MC7021 = 0x00017021l

    TYP_MX7005 = 0x00027005l
    TYP_MX7010 = 0x00027010l
    TYP_MX7011 = 0x00027011l



    #  ----- MI.72xx, MC.72xx, MX.72xx -----
    TYP_MI7210 = 0x00007210l
    TYP_MI7211 = 0x00007211l
    TYP_MI7220 = 0x00007220l
    TYP_MI7221 = 0x00007221l

    TYP_M2I7210 = 0x00037210l
    TYP_M2I7211 = 0x00037211l
    TYP_M2I7220 = 0x00037220l
    TYP_M2I7221 = 0x00037221l

    TYP_M2I7210EXP = 0x00047210l
    TYP_M2I7211EXP = 0x00047211l
    TYP_M2I7220EXP = 0x00047220l
    TYP_M2I7221EXP = 0x00047221l

    TYP_MC7210 = 0x00017210l
    TYP_MC7211 = 0x00017211l
    TYP_MC7220 = 0x00017220l
    TYP_MC7221 = 0x00017221l

    TYP_MX7210 = 0x00027210l
    TYP_MX7220 = 0x00027220l




    #  ***********************************************************************
    #  software registers
    #  ***********************************************************************


    #  ***** PCI Features Bits (MI/MC/MX and prior cards) *********
    PCIBIT_MULTI = 0x00000001
    PCIBIT_DIGITAL = 0x00000002
    PCIBIT_CH0DIGI = 0x00000004
    PCIBIT_EXTSAM = 0x00000008
    PCIBIT_3CHANNEL = 0x00000010
    PCIBIT_GATE = 0x00000020
    PCIBIT_SLAVE = 0x00000040
    PCIBIT_MASTER = 0x00000080
    PCIBIT_DOUBLEMEM = 0x00000100
    PCIBIT_SYNC = 0x00000200
    PCIBIT_TIMESTAMP = 0x00000400
    PCIBIT_STARHUB = 0x00000800
    PCIBIT_CA = 0x00001000
    PCIBIT_XIO = 0x00002000
    PCIBIT_AMPLIFIER = 0x00004000
    PCIBIT_DIFFMODE	= 0x00008000

    PCIBIT_ELISA = 0x10000000


    #  ***** PCI features starting with M2i card series *****
    SPCM_FEAT_MULTI = 0x00000001      #  multiple recording
    SPCM_FEAT_GATE = 0x00000002      #  gated sampling
    SPCM_FEAT_DIGITAL = 0x00000004      #  additional synchronous digital inputs or outputs
    SPCM_FEAT_TIMESTAMP = 0x00000008      #  timestamp
    SPCM_FEAT_STARHUB5 = 0x00000020      #  starhub for 5 cards installed
    SPCM_FEAT_STARHUB16 = 0x00000040      #  starhub for 16 cards installed
    SPCM_FEAT_ABA = 0x00000080      #  ABA mode installed
    SPCM_FEAT_BASEXIO = 0x00000100      #  extra I/O on base card installed
    SPCM_FEAT_AMPLIFIER_10V	= 0x00000200      #  external amplifier for 60/61
    SPCM_FEAT_STARHUBSYSMASTER = 0x00000400      #  system starhub master installed
    SPCM_FEAT_DIFFMODE = 0x00000800      #  Differential mode installed
    SPCM_FEAT_CUSTOMMOD_MASK = 0xF0000000      #  mask for custom modification code, meaning of code depends on type and customer


    #  ***** Error Request *************
    ERRORTEXTLEN = 200
    SPC_LASTERRORTEXT = 999996l
    SPC_LASTERRORVALUE = 999997l
    SPC_LASTERRORREG = 999998l
    SPC_LASTERRORCODE = 999999l      #  Reading this reset the internal error-memory.



    #  ***** Register and Command Structure
    SPC_COMMAND = 0l
    SPC_RESET = 0l
#define		SPC_SOFTRESET			1l
    SPC_WRITESETUP = 2l
    SPC_START = 10l
    SPC_STARTANDWAIT = 11l
    SPC_FIFOSTART = 12l
    SPC_FIFOWAIT = 13l
    SPC_FORCETRIGGER = 16l
    SPC_STOP = 20l
    SPC_FLUSHFIFOBUFFER = 21l
    SPC_POWERDOWN = 30l
    SPC_SYNCMASTER = 100l
    SPC_SYNCTRIGGERMASTER = 101l
    SPC_SYNCMASTERFIFO = 102l
    SPC_SYNCSLAVE = 110l
    SPC_SYNCTRIGGERSLAVE = 111l
    SPC_SYNCSLAVEFIFO = 112l
    SPC_NOSYNC = 120l
    SPC_SYNCSTART = 130l
    SPC_SYNCCALCMASTER = 140l
    SPC_SYNCCALCMASTERFIFO = 141l
    SPC_RELAISON = 200l
    SPC_RELAISOFF = 210l
    SPC_ADJUSTSTART = 300l
    SPC_FIFO_BUFREADY0 = 400l
    SPC_FIFO_BUFREADY1 = 401l
    SPC_FIFO_BUFREADY2 = 402l
    SPC_FIFO_BUFREADY3 = 403l
    SPC_FIFO_BUFREADY4 = 404l
    SPC_FIFO_BUFREADY5 = 405l
    SPC_FIFO_BUFREADY6 = 406l
    SPC_FIFO_BUFREADY7 = 407l
    SPC_FIFO_BUFREADY8 = 408l
    SPC_FIFO_BUFREADY9 = 409l
    SPC_FIFO_BUFREADY10 = 410l
    SPC_FIFO_BUFREADY11 = 411l
    SPC_FIFO_BUFREADY12 = 412l
    SPC_FIFO_BUFREADY13 = 413l
    SPC_FIFO_BUFREADY14 = 414l
    SPC_FIFO_BUFREADY15 = 415l
    SPC_FIFO_AUTOBUFSTART = 500l
    SPC_FIFO_AUTOBUFEND = 510l

    SPC_STATUS = 10l
    SPC_RUN = 0l
    SPC_TRIGGER = 10l
    SPC_READY = 20l



    #  commands for M2 cards
    SPC_M2CMD = 100l      #  write a command
    M2CMD_CARD_RESET = 0x00000001l		    #  hardware reset =
    M2CMD_CARD_WRITESETUP	 = 0x00000002l 	    #  write setup only
    M2CMD_CARD_START		=	0x00000004l		    #  start of card (including writesetup)
    M2CMD_CARD_ENABLETRIGGER =	0x00000008l		    #  enable trigger engine
    M2CMD_CARD_FORCETRIGGER	=	0x00000010l		    #  force trigger
    M2CMD_CARD_DISABLETRIGGER =	0x00000020l		    #  disable trigger engine again (multi or gate)
    M2CMD_CARD_STOP			=	0x00000040l		    #  stop run
    M2CMD_CARD_FLUSHFIFO	=	0x00000080l		    #  flush fifos to memory

    M2CMD_ALL_STOP = 0x00440060l      #  stops card and all running transfers

    M2CMD_CARD_WAITPREFULL = 0x00001000l		    #  wait until pretrigger is full
    M2CMD_CARD_WAITTRIGGER	=	0x00002000l		    #  wait for trigger recognition
    M2CMD_CARD_WAITREADY	=	0x00004000l		    #  wait for card ready

    M2CMD_DATA_STARTDMA	 = 0x00010000l		    #  start of DMA transfer for data
    M2CMD_DATA_WAITDMA		 = 0x00020000l		    #  wait for end of data transfer / next block ready
    M2CMD_DATA_STOPDMA = 0x00040000l      #  abort the data transfer
    M2CMD_DATA_POLL = 0x00080000l      #  transfer data using single access and polling

    M2CMD_EXTRA_STARTDMA = 0x00100000l		    #  start of DMA transfer for extra (ABA + timestamp) data
    M2CMD_EXTRA_WAITDMA = 0x00200000l		    #  wait for end of extra (ABA + timestamp) data transfer / next block ready
    M2CMD_EXTRA_STOPDMA = 0x00400000l      #  abort the extra (ABA + timestamp) data transfer
    M2CMD_EXTRA_POLL = 0x00800000l      #  transfer data using single access and polling



    #  status for M2 cards (bitmask)
    SPC_M2STATUS = 110l      #  read the current status
    M2STAT_NONE = 0x00000000l      #  status empty
    M2STAT_CARD_PRETRIGGER		= 0x00000001l		    #  pretrigger area is full
    M2STAT_CARD_TRIGGER			= 0x00000002l		    #  trigger recognized
    M2STAT_CARD_READY			= 0x00000004l		    #  card is ready, run finished

    M2STAT_DATA_BLOCKREADY	=	0x00000100l		    #  next data block is available
    M2STAT_DATA_END = 0x00000200l      #  data transfer has ended
    M2STAT_DATA_OVERRUN = 0x00000400l      #  FIFO overrun (record) or underrun (replay)
    M2STAT_DATA_ERROR = 0x00000800l      #  internal error

    M2STAT_EXTRA_BLOCKREADY		= 0x00001000l		    #  next extra data (ABA and timestamp) block is available
    M2STAT_EXTRA_END = 0x00002000l      #  extra data (ABA and timestamp) transfer has ended
    M2STAT_EXTRA_OVERRUN = 0x00004000l     #  FIFO overrun
    M2STAT_EXTRA_ERROR = 0x00008000l      #  internal error

    M2STAT_INTERNALMASK = 0xff000000l      #  mask for internal status signals
    M2STAT_INTERNAL_SYSLOCK = 0x02000000l



    #  buffer control registers for samples data
    SPC_DATA_AVAIL_USER_LEN = 200l      #  number of bytes available for user (valid data if READ, free buffer if WRITE)
    SPC_DATA_AVAIL_USER_POS = 201l      #  the current byte position where the available user data starts
    SPC_DATA_AVAIL_CARD_LEN = 202l      #  number of bytes available for card (free buffer if READ, filled data if WRITE)
    SPC_DATA_OUTBUFSIZE = 209l      #  output buffer size in samples

    #  buffer control registers for extra data (ABA slow data, timestamps)
    SPC_ABA_AVAIL_USER_LEN = 210l      #  number of bytes available for user (valid data if READ, free buffer if WRITE)
    SPC_ABA_AVAIL_USER_POS = 211l      #  the current byte position where the available user data starts
    SPC_ABA_AVAIL_CARD_LEN = 212l      #  number of bytes available for card (free buffer if READ, filled data if WRITE)

    SPC_TS_AVAIL_USER_LEN = 220l      #  number of bytes available for user (valid data if READ, free buffer if WRITE)
    SPC_TS_AVAIL_USER_POS = 221l      #  the current byte position where the available user data starts
    SPC_TS_AVAIL_CARD_LEN = 222l      #  number of bytes available for card (free buffer if READ, filled data if WRITE)



    #  Installation
    SPC_VERSION = 1000l
    SPC_ISAADR = 1010l
    SPC_INSTMEM = 1020l
    SPC_INSTSAMPLERATE = 1030l
    SPC_BRDTYP = 1040l

    #  MI/MC/MX type information (internal use)
    SPC_MIINST_MODULES = 1100l
    SPC_MIINST_CHPERMODULE = 1110l
    SPC_MIINST_BYTESPERSAMPLE = 1120l
    SPC_MIINST_BITSPERSAMPLE = 1125l
    SPC_MIINST_MINADCLOCK = 1130l
    SPC_MIINST_MAXADCLOCK = 1140l
    SPC_MIINST_MINEXTCLOCK = 1145l
    SPC_MIINST_MAXEXTCLOCK = 1146l
    SPC_MIINST_QUARZ = 1150l
    SPC_MIINST_QUARZ2 = 1151l
    SPC_MIINST_FLAGS = 1160l
    SPC_MIINST_FIFOSUPPORT = 1170l
    SPC_MIINST_ISDEMOCARD = 1175l

    #  Driver information
    SPC_GETDRVVERSION = 1200l
    SPC_GETKERNELVERSION = 1210l
    SPC_GETDRVTYPE = 1220l
    DRVTYP_DOS = 0l
    DRVTYP_LINUX = 1l
    DRVTYP_VXD = 2l
    DRVTYP_NTLEGACY = 3l
    DRVTYP_WDM = 4l
    SPC_GETCOMPATIBILITYVERSION = 1230l

    #  PCI, CompactPCI and PXI Installation Information
    SPC_PCITYP = 2000l

    #  ***** available card function types *****
    SPC_FNCTYPE = 2001l
    SPCM_TYPE_AI = 0x01
    SPCM_TYPE_AO = 0x02
    SPCM_TYPE_DI = 0x04
    SPCM_TYPE_DO = 0x08
    SPCM_TYPE_DIO = 0x10

    SPC_PCIVERSION = 2010l
    SPC_PCIEXTVERSION = 2011l
    SPC_PCIMODULEVERSION = 2012l
    SPC_PCIMODULEBVERSION = 2013l
    SPC_PCIDATE = 2020l
    SPC_CALIBDATE = 2025l
    SPC_PCISERIALNR = 2030l
    SPC_PCISERIALNO = 2030l
    SPC_PCISAMPLERATE = 2100l
    SPC_PCIMEMSIZE = 2110l
    SPC_PCIFEATURES = 2120l
    SPC_PCIINFOADR = 2200l
    SPC_PCIINTERRUPT = 2300l
    SPC_PCIBASEADR0 = 2400l
    SPC_PCIBASEADR1 = 2401l
    SPC_PCIREGION0 = 2410l
    SPC_PCIREGION1 = 2411l
    SPC_READTRGLVLCOUNT = 2500l
    SPC_READIRCOUNT = 3000l
    SPC_READUNIPOLAR0 = 3010l
    SPC_READUNIPOLAR1 = 3020l
    SPC_READUNIPOLAR2 = 3030l
    SPC_READUNIPOLAR3 = 3040l
    SPC_READMAXOFFSET = 3100l

    SPC_READAIFEATURES = 3101l
    SPCM_AI_TERM = 0x00000001      #  input termination available
    SPCM_AI_SE = 0x00000002      #  single-ended mode available
    SPCM_AI_DIFF = 0x00000004      #  differential mode available
    SPCM_AI_OFFSPERCENT = 0x00000008     #  offset programming is done in percent of input range
    SPCM_AI_OFFSMV = 0x00000010      #  offset programming is done in mV absolut
    SPCM_AI_OVERRANGEDETECT = 0x00000020      #  overrange detection is programmable
    SPCM_AI_AUTOCALOFFS = 0x00001000      #  automatic offset calibration in hardware
    SPCM_AI_AUTOCALGAIN = 0x00002000      #  automatic gain calibration in hardware
    SPCM_AI_AUTOCALOFFSNOIN = 0x00004000      #  automatic offset calibration with open inputs
    SPCM_AI_INDIVPULSEWIDTH = 0x00100000      #  individual pulsewidth per channel available

    SPC_READAOFEATURES = 3102l
    SPCM_AO_SE = 0x00000002      #  single-ended mode available
    SPCM_AO_DIFF = 0x00000004      #  differential mode available
    SPCM_AO_PROGFILTER = 0x00000008      #  programmable filters available
    SPCM_AO_PROGOFFSET = 0x00000010      #  programmable offset available
    SPCM_AO_PROGGAIN = 0x00000020      #  programmable gain available
    SPCM_AO_PROGSTOPLEVEL = 0x00000040      #  programmable stop level available

    SPC_READDIFEATURES = 3103l
    SPCM_DI_TERM = 0x00000001      #  input termination available
    SPCM_DI_SE = 0x00000002      #  single-ended mode available
    SPCM_DI_DIFF = 0x00000004      #  differential mode available
    SPCM_DI_INDIVPULSEWIDTH = 0x00100000      #  individual pulsewidth per channel available
    SPCM_DI_IOCHANNEL = 0x00200000      #  connected with DO channel

    SPC_READDOFEATURES = 3104l
    SPCM_DO_SE = 0x00000002      #  single-ended mode available
    SPCM_DO_DIFF = 0x00000004      #  differential mode available
    SPCM_DO_PROGSTOPLEVEL = 0x00000008      #  programmable stop level available
    SPCM_DO_PROGOUTLEVELS = 0x00000010     #  programmable output levels (low + high) available
    SPCM_DO_ENABLEMASK = 0x00000020    #  individual enable mask for each output channel
    SPCM_DO_IOCHANNEL = 0x00200000      #  connected with DI channel

    SPC_READCHGROUPING = 3110l

    SPC_READRANGECH0_0 = 3200l
    SPC_READRANGECH0_1 = 3201l
    SPC_READRANGECH0_2 = 3202l
    SPC_READRANGECH0_3 = 3203l
    SPC_READRANGECH0_4 = 3204l
    SPC_READRANGECH0_5 = 3205l
    SPC_READRANGECH0_6 = 3206l
    SPC_READRANGECH0_7 = 3207l
    SPC_READRANGECH0_8 = 3208l
    SPC_READRANGECH0_9 = 3209l
    SPC_READRANGECH1_0 = 3300l
    SPC_READRANGECH1_1 = 3301l
    SPC_READRANGECH1_2 = 3302l
    SPC_READRANGECH1_3 = 3303l
    SPC_READRANGECH1_4 = 3304l
    SPC_READRANGECH1_5 = 3305l
    SPC_READRANGECH1_6 = 3306l
    SPC_READRANGECH1_7 = 3307l
    SPC_READRANGECH1_8 = 3308l
    SPC_READRANGECH1_9 = 3309l
    SPC_READRANGECH2_0 = 3400l
    SPC_READRANGECH2_1 = 3401l
    SPC_READRANGECH2_2 = 3402l
    SPC_READRANGECH2_3 = 3403l
    SPC_READRANGECH3_0 = 3500l
    SPC_READRANGECH3_1 = 3501l
    SPC_READRANGECH3_2 = 3502l
    SPC_READRANGECH3_3 = 3503l

    SPC_READRANGEMIN0 = 4000l
    SPC_READRANGEMIN99 = 4099l
    SPC_READRANGEMAX0 = 4100l
    SPC_READRANGEMAX99 = 4199l
    SPC_READOFFSMIN0 = 4200l
    SPC_READOFFSMIN99 = 4299l
    SPC_READOFFSMAX0 = 4300l
    SPC_READOFFSMAX99 = 4399l
    SPC_PCICOUNTER = 9000l
    SPC_BUFFERPOS = 9010l


    SPC_CARDMODE = 9500l      #  card modes as listed below
    SPC_AVAILCARDMODES = 9501l      #  list with available card modes

    #  card modes
    SPC_REC_STD_SINGLE = 0x00000001      #  singleshot recording to memory
    SPC_REC_STD_MULTI = 0x00000002      #  multiple records to memory on each trigger event
    SPC_REC_STD_GATE = 0x00000004      #  gated recording to memory on gate signal
    SPC_REC_STD_ABA = 0x00000008      #  ABA: A slowly to extra FIFO, B to memory on each trigger event

    SPC_REC_FIFO_SINGLE = 0x00000010      #  singleshot to FIFO on trigger event
    SPC_REC_FIFO_MULTI = 0x00000020      #  multiple records to FIFO on each trigger event
    SPC_REC_FIFO_GATE = 0x00000040      #  gated sampling to FIFO on gate signal
    SPC_REC_FIFO_ABA = 0x00000080      #  ABA: A slowly to extra FIFO, B to FIFO on each trigger event

    SPC_REP_STD_SINGLE = 0x00000100      #  single replay from memory on trigger event
    SPC_REP_STD_MULTI = 0x00000200      #  multiple replay from memory on each trigger event
    SPC_REP_STD_GATE = 0x00000400      #  gated replay from memory on gate signal

    SPC_REP_FIFO_SINGLE = 0x00000800      #  single replay from FIFO on trigger event
    SPC_REP_FIFO_MULTI = 0x00001000      #  multiple replay from FIFO on each trigger event
    SPC_REP_FIFO_GATE = 0x00002000      #  gated replay from FIFO on gate signal

    SPC_REP_STD_CONTINUOUS = 0x00004000      #  continuous replay started by one trigger event
    SPC_REP_STD_SINGLERESTART = 0x00008000      #  single replays on every detected trigger event




    #  Memory
    SPC_MEMSIZE = 10000l
    SPC_SEGMENTSIZE = 10010l
    SPC_LOOPS = 10020l
    SPC_PRETRIGGER = 10030l
    SPC_ABADIVIDER = 10040l
    SPC_POSTTRIGGER = 10100l
    SPC_STARTOFFSET = 10200l





    #  Channels
    SPC_CHENABLE = 11000l
    SPC_CHCOUNT = 11001l
    SPC_CHMODACOUNT = 11100l
    SPC_CHMODBCOUNT = 11101l


    #  ----- channel enable flags for A/D and D/A boards (MI/MC/MX series) -----
    #  = and all cards on M2i series
    CHANNEL0 = 0x00000001
    CHANNEL1 = 0x00000002
    CHANNEL2 = 0x00000004
    CHANNEL3 = 0x00000008
    CHANNEL4 = 0x00000010
    CHANNEL5 = 0x00000020
    CHANNEL6 = 0x00000040
    CHANNEL7 = 0x00000080
    CHANNEL8 = 0x00000100
    CHANNEL9 = 0x00000200
    CHANNEL10 = 0x00000400
    CHANNEL11 = 0x00000800
    CHANNEL12 = 0x00001000
    CHANNEL13 = 0x00002000
    CHANNEL14 = 0x00004000
    CHANNEL15 = 0x00008000
    CHANNEL16 = 0x00010000
    CHANNEL17 = 0x00020000
    CHANNEL18 = 0x00040000
    CHANNEL19 = 0x00080000
    CHANNEL20 = 0x00100000
    CHANNEL21 = 0x00200000
    CHANNEL22 = 0x00400000
    CHANNEL23 = 0x00800000
    CHANNEL24 = 0x01000000
    CHANNEL25 = 0x02000000
    CHANNEL26 = 0x04000000
    CHANNEL27 = 0x08000000
    CHANNEL28 = 0x10000000
    CHANNEL29 = 0x20000000
    CHANNEL30 = 0x40000000
    CHANNEL31 = 0x80000000
    #  CHANNEL32 up to CHANNEL63 are placed in the upper 32 bit of a 64 bit word (M2i only)


    #  ----- old digital i/o settings for 16 bit implementation (MI/MC/MX series) = -----
    CH0_8BITMODE = 65536l      #  for MI.70xx only
    CH0_16BIT = 1l
    CH0_32BIT = 3l
    CH1_16BIT = 4l
    CH1_32BIT = 12l

    #  ----- new digital i/o settings for 8 bit implementation (MI/MC/MX series) -----
    MOD0_8BIT = 1l
    MOD0_16BIT = 3l
    MOD0_32BIT = 15l
    MOD1_8BIT = 16l
    MOD1_16BIT = 48l
    MOD1_32BIT = 240l

    SPC_CHROUTE0 = 11010l
    SPC_CHROUTE1 = 11020l

    SPC_BITENABLE = 11030l



    #  ----- Clock Settings -----
    SPC_SAMPLERATE = 20000l
    SPC_SYNCCLOCK = 20005l
    SPC_SAMPLERATE2 = 20010l
    SPC_SR2 = 20020l
    SPC_PLL_ENABLE = 20030l
    SPC_CLOCKDIV = 20040l
    SPC_INTCLOCKDIV = 20041l
    SPC_PLL_R = 20060l
    SPC_PLL_F = 20061l
    SPC_PLL_S = 20062l
    SPC_PLL_DIV = 20063l
    SPC_EXTERNALCLOCK = 20100l
    SPC_EXTERNOUT = 20110l
    SPC_CLOCKOUT = 20110l
    SPC_CLOCK50OHM = 20120l
    SPC_CLOCK110OHM = 20120l
    SPC_EXTERNRANGE = 20130l
    SPC_EXTRANGESHDIRECT = 20131l
    EXRANGE_NONE = 0l
    EXRANGE_NOPLL = 1l
    EXRANGE_SINGLE = 2l
    EXRANGE_BURST_S = 4l
    EXRANGE_BURST_M = 8l
    EXRANGE_BURST_L = 16l
    EXRANGE_BURST_XL = 32l
    EXRANGE_LOW = 64l
    EXRANGE_HIGH = 128l
    EXRANGE_LOW_DPS = 256l      #  digital phase synchronization
    SPC_REFERENCECLOCK = 20140l
    REFCLOCK_PXI = -1l

    #  ----- new clock registers starting with M2i cards -----
    SPC_CLOCKMODE = 20200l      #  clock mode as listed below
    SPC_AVAILCLOCKMODES = 20201l      #  returns all available clock modes
    SPC_CM_INTPLL = 0x00000001      #  use internal PLL
    SPC_CM_QUARTZ1 = 0x00000002      #  use plain quartz1 (with divider)
    SPC_CM_QUARTZ2 = 0x00000004      #  use plain quartz2 (with divider)
    SPC_CM_EXTERNAL = 0x00000008      #  use external clock directly
    SPC_CM_EXTDIVIDER = 0x00000010      #  use external clock with programmed divider
    SPC_CM_EXTREFCLOCK = 0x00000020     #  external reference clock fed in (defined with SPC_REFERENCECLOCK)
    SPC_CM_PXIREFCLOCK = 0x00000040      #  PXI reference clock
    SPC_CM_SHDIRECT = 0x00000080      #  Star-hub direct clock (not synchronised)

    #  ----- internal use only! -----
    SPC_CM_SYNCINT = 0x01000000
    SPC_CM_SYNCEXT = 0x02000000
    SPC_BURSTSYSCLOCKMODE = 20210l
    SPC_SYNCMASTERSYSCLOCKMODE = 20211l


    #  mux definitions for channel routing
    SPC_CHANNELMUXINFO = 20300l
    SPCM_MUX_NONE = 0x00000000      #  nothing is interlaced
    SPCM_MUX_MUXONMOD = 0x00000001      #  data on module is multiplexed, only one channel can have full speed
    SPCM_MUX_INVERTCLKONMOD = 0x00000002      #  two channels on one module run with inverted clock
    SPCM_MUX_DLY = 0x00000003      #  delay cable between modules, one channel can have full interlace speed
    SPCM_MUX_DLYANDMUXONMOD = 0x00000004      #  delay cable between modules and multplexing on module
    SPCM_MUX_MUXBETWEENMODS = 0x00000005      #  multiplexed between modules (fastest sampling rate only with one module)


    #  ----- In/Out Range -----
    SPC_OFFS0 = 30000l
    SPC_AMP0 = 30010l
    SPC_ACDC0 = 30020l
    SPC_50OHM0 = 30030l
    SPC_DIFF0 = 30040l
    SPC_DOUBLEOUT0 = 30041l
    SPC_DIGITAL0 = 30050l
    SPC_110OHM0 = 30060l
    SPC_110OHM0L = 30060l
    SPC_INOUT0 = 30070l
    SPC_FILTER0 = 30080l
    SPC_BANKSWITCH0 = 30081l

    SPC_OFFS1 = 30100l
    SPC_AMP1 = 30110l
    SPC_ACDC1 = 30120l
    SPC_50OHM1 = 30130l
    SPC_DIFF1 = 30140l
    SPC_DOUBLEOUT1 = 30141l
    SPC_DIGITAL1 = 30150l
    SPC_110OHM1 = 30160l
    SPC_110OHM0H = 30160l
    SPC_INOUT1 = 30170l
    SPC_FILTER1 = 30180l
    SPC_BANKSWITCH1 = 30181l

    SPC_OFFS2 = 30200l
    SPC_AMP2 = 30210l
    SPC_ACDC2 = 30220l
    SPC_50OHM2 = 30230l
    SPC_DIFF2 = 30240l
    SPC_DOUBLEOUT2 = 30241l
    SPC_110OHM2 = 30260l
    SPC_110OHM1L = 30260l
    SPC_INOUT2 = 30270l
    SPC_FILTER2 = 30280l
    SPC_BANKSWITCH2 = 30281l

    SPC_OFFS3 = 30300l
    SPC_AMP3 = 30310l
    SPC_ACDC3 = 30320l
    SPC_50OHM3 = 30330l
    SPC_DIFF3 = 30340l
    SPC_DOUBLEOUT3 = 30341l
    SPC_110OHM3 = 30360l
    SPC_110OHM1H = 30360l
    SPC_INOUT3 = 30370l
    SPC_FILTER3 = 30380l
    SPC_BANKSWITCH3 = 30381l

    SPC_OFFS4 = 30400l
    SPC_AMP4 = 30410l
    SPC_ACDC4 = 30420l
    SPC_50OHM4 = 30430l
    SPC_DIFF4 = 30440l

    SPC_OFFS5 = 30500l
    SPC_AMP5 = 30510l
    SPC_ACDC5 = 30520l
    SPC_50OHM5 = 30530l
    SPC_DIFF5 = 30540l

    SPC_OFFS6 = 30600l
    SPC_AMP6 = 30610l
    SPC_ACDC6 = 30620l
    SPC_50OHM6 = 30630l
    SPC_DIFF6 = 30640l

    SPC_OFFS7 = 30700l
    SPC_AMP7 = 30710l
    SPC_ACDC7 = 30720l
    SPC_50OHM7 = 30730l
    SPC_DIFF7 = 30740l

    SPC_OFFS8 = 30800l
    SPC_AMP8 = 30810l
    SPC_ACDC8 = 30820l
    SPC_50OHM8 = 30830l
    SPC_DIFF8 = 30840l

    SPC_OFFS9 = 30900l
    SPC_AMP9 = 30910l
    SPC_ACDC9 = 30920l
    SPC_50OHM9 = 30930l
    SPC_DIFF9 = 30940l

    SPC_OFFS10 = 31000l
    SPC_AMP10 = 31010l
    SPC_ACDC10 = 31020l
    SPC_50OHM10 = 31030l
    SPC_DIFF10 = 31040l

    SPC_OFFS11 = 31100l
    SPC_AMP11 = 31110l
    SPC_ACDC11 = 31120l
    SPC_50OHM11 = 31130l
    SPC_DIFF11 = 31140l

    SPC_OFFS12 = 31200l
    SPC_AMP12 = 31210l
    SPC_ACDC12 = 31220l
    SPC_50OHM12 = 31230l
    SPC_DIFF12 = 31240l

    SPC_OFFS13 = 31300l
    SPC_AMP13 = 31310l
    SPC_ACDC13 = 31320l
    SPC_50OHM13 = 31330l
    SPC_DIFF13 = 31340l

    SPC_OFFS14 = 31400l
    SPC_AMP14 = 31410l
    SPC_ACDC14 = 31420l
    SPC_50OHM14 = 31430l
    SPC_DIFF14 = 31440l

    SPC_OFFS15 = 31500l
    SPC_AMP15 = 31510l
    SPC_ACDC15 = 31520l
    SPC_50OHM15 = 31530l
    SPC_DIFF15 = 31540l

    SPC_110OHMTRIGGER = 30400l
    SPC_110OHMCLOCK = 30410l


    AMP_BI200 = 200l
    AMP_BI500 = 500l
    AMP_BI1000 = 1000l
    AMP_BI2000 = 2000l
    AMP_BI2500 = 2500l
    AMP_BI4000 = 4000l
    AMP_BI5000 = 5000l
    AMP_BI10000 = 10000l
    AMP_UNI400 = 100400l
    AMP_UNI1000 = 101000l
    AMP_UNI2000 = 102000l


    #  ----- Trigger Settings -----
    SPC_TRIGGERMODE = 40000l
    SPC_TRIG_OUTPUT = 40100l
    SPC_TRIGGEROUT = 40100l
    SPC_TRIG_TERM = 40110l
    SPC_TRIG_TERM0 = 40110l
    SPC_TRIGGER50OHM = 40110l
    SPC_TRIGGER110OHM0 = 40110l
    SPC_TRIG_TERM1 = 40111l
    SPC_TRIGGER110OHM1 = 40111l

    SPC_TRIGGERMODE0 = 40200l
    SPC_TRIGGERMODE1 = 40201l
    SPC_TRIGGERMODE2 = 40202l
    SPC_TRIGGERMODE3 = 40203l
    SPC_TRIGGERMODE4 = 40204l
    SPC_TRIGGERMODE5 = 40205l
    SPC_TRIGGERMODE6 = 40206l
    SPC_TRIGGERMODE7 = 40207l
    SPC_TRIGGERMODE8 = 40208l
    SPC_TRIGGERMODE9 = 40209l
    SPC_TRIGGERMODE10 = 40210l
    SPC_TRIGGERMODE11 = 40211l
    SPC_TRIGGERMODE12 = 40212l
    SPC_TRIGGERMODE13 = 40213l
    SPC_TRIGGERMODE14 = 40214l
    SPC_TRIGGERMODE15 = 40215l

    TM_SOFTWARE = 0l
    TM_NOTRIGGER = 10l
    TM_CHXPOS = 10000l
    TM_CHXPOS_LP = 10001l
    TM_CHXPOS_SP = 10002l
    TM_CHXPOS_GS = 10003l
    TM_CHXPOS_SS = 10004l
    TM_CHXNEG = 10010l
    TM_CHXNEG_LP = 10011l
    TM_CHXNEG_SP = 10012l
    TM_CHXNEG_GS = 10013l
    TM_CHXNEG_SS = 10014l
    TM_CHXOFF = 10020l
    TM_CHXBOTH = 10030l
    TM_CHXWINENTER = 10040l
    TM_CHXWINENTER_LP = 10041l
    TM_CHXWINENTER_SP = 10042l
    TM_CHXWINLEAVE = 10050l
    TM_CHXWINLEAVE_LP = 10051l
    TM_CHXWINLEAVE_SP = 10052l

    TM_CH0POS = 10000l
    TM_CH0NEG = 10010l
    TM_CH0OFF = 10020l
    TM_CH0BOTH = 10030l
    TM_CH1POS = 10100l
    TM_CH1NEG = 10110l
    TM_CH1OFF = 10120l
    TM_CH1BOTH = 10130l
    TM_CH2POS = 10200l
    TM_CH2NEG = 10210l
    TM_CH2OFF = 10220l
    TM_CH2BOTH = 10230l
    TM_CH3POS = 10300l
    TM_CH3NEG = 10310l
    TM_CH3OFF = 10320l
    TM_CH3BOTH = 10330l

    TM_TTLPOS = 20000l
    TM_TTLHIGH_LP = 20001l
    TM_TTLHIGH_SP = 20002l
    TM_TTLNEG = 20010l
    TM_TTLLOW_LP = 20011l
    TM_TTLLOW_SP = 20012l
    TM_TTL = 20020l
    TM_TTLBOTH = 20030l
    TM_TTLBOTH_LP = 20031l
    TM_TTLBOTH_SP = 20032l
    TM_CHANNEL = 20040l
    TM_PATTERN = 21000l
    TM_PATTERN_LP = 21001l
    TM_PATTERN_SP = 21002l
    TM_PATTERNANDEDGE = 22000l
    TM_PATTERNANDEDGE_LP = 22001l
    TM_PATTERNANDEDGE_SP = 22002l
    TM_GATELOW = 30000l
    TM_GATEHIGH = 30010l
    TM_GATEPATTERN = 30020l
    TM_CHOR = 35000l
    TM_CHAND = 35010l

    SPC_PXITRGOUT = 40300l
    PTO_OFF = 0l
    PTO_LINE0 = 1l
    PTO_LINE1 = 2l
    PTO_LINE2 = 3l
    PTO_LINE3 = 4l
    PTO_LINE4 = 5l
    PTO_LINE5 = 6l
    PTO_LINE6 = 7l
    PTO_LINE7 = 8l
    PTO_LINESTAR = 9l
    SPC_PXITRGOUT_AVAILABLE = 40301l      #  bitmap register


    SPC_PXITRGIN = 40310l      #  bitmap register
    PTI_OFF = 0l
    PTI_LINE0 = 1l
    PTI_LINE1 = 2l
    PTI_LINE2 = 4l
    PTI_LINE3 = 8l
    PTI_LINE4 = 16l
    PTI_LINE5 = 32l
    PTI_LINE6 = 64l
    PTI_LINE7 = 128l
    PTI_LINESTAR = 256l
    SPC_PXITRGIN_AVAILABLE = 40311l      #  bitmap register


    #  new registers of M2i driver
    SPC_TRIG_AVAILORMASK = 40400l
    SPC_TRIG_ORMASK = 40410l
    SPC_TRIG_AVAILANDMASK = 40420l
    SPC_TRIG_ANDMASK = 40430l
    SPC_TMASK_NONE = 0x00000000
    SPC_TMASK_SOFTWARE = 0x00000001
    SPC_TMASK_EXT0 = 0x00000002
    SPC_TMASK_EXT1 = 0x00000004
    SPC_TMASK_XIO0 = 0x00000100
    SPC_TMASK_XIO1 = 0x00000200
    SPC_TMASK_XIO2 = 0x00000400
    SPC_TMASK_XIO3 = 0x00000800
    SPC_TMASK_XIO4 = 0x00001000
    SPC_TMASK_XIO5 = 0x00002000
    SPC_TMASK_XIO6 = 0x00004000
    SPC_TMASK_XIO7 = 0x00008000
    SPC_TMASK_PXI0 = 0x00100000
    SPC_TMASK_PXI1 = 0x00200000
    SPC_TMASK_PXI2 = 0x00400000
    SPC_TMASK_PXI3 = 0x00800000
    SPC_TMASK_PXI4 = 0x01000000
    SPC_TMASK_PXI5 = 0x02000000
    SPC_TMASK_PXI6 = 0x04000000
    SPC_TMASK_PXI7 = 0x08000000
    SPC_TMASK_PXISTAR = 0x80000000

    SPC_TRIG_CH_AVAILORMASK0 = 40450l
    SPC_TRIG_CH_AVAILORMASK1 = 40451l
    SPC_TRIG_CH_ORMASK0 = 40460l
    SPC_TRIG_CH_ORMASK1 = 40461l
    SPC_TRIG_CH_AVAILANDMASK0 = 40470l
    SPC_TRIG_CH_AVAILANDMASK1 = 40471l
    SPC_TRIG_CH_ANDMASK0 = 40480l
    SPC_TRIG_CH_ANDMASK1 = 40481l
    SPC_TMASK0_NONE = 0x00000000
    SPC_TMASK0_CH0 = 0x00000001
    SPC_TMASK0_CH1 = 0x00000002
    SPC_TMASK0_CH2 = 0x00000004
    SPC_TMASK0_CH3 = 0x00000008
    SPC_TMASK0_CH4 = 0x00000010
    SPC_TMASK0_CH5 = 0x00000020
    SPC_TMASK0_CH6 = 0x00000040
    SPC_TMASK0_CH7 = 0x00000080
    SPC_TMASK0_CH8 = 0x00000100
    SPC_TMASK0_CH9 = 0x00000200
    SPC_TMASK0_CH10 = 0x00000400
    SPC_TMASK0_CH11 = 0x00000800
    SPC_TMASK0_CH12 = 0x00001000
    SPC_TMASK0_CH13 = 0x00002000
    SPC_TMASK0_CH14 = 0x00004000
    SPC_TMASK0_CH15 = 0x00008000
    SPC_TMASK0_CH16 = 0x00010000
    SPC_TMASK0_CH17 = 0x00020000
    SPC_TMASK0_CH18 = 0x00040000
    SPC_TMASK0_CH19 = 0x00080000
    SPC_TMASK0_CH20 = 0x00100000
    SPC_TMASK0_CH21 = 0x00200000
    SPC_TMASK0_CH22 = 0x00400000
    SPC_TMASK0_CH23 = 0x00800000
    SPC_TMASK0_CH24 = 0x01000000
    SPC_TMASK0_CH25 = 0x02000000
    SPC_TMASK0_CH26 = 0x04000000
    SPC_TMASK0_CH27 = 0x08000000
    SPC_TMASK0_CH28 = 0x10000000
    SPC_TMASK0_CH29 = 0x20000000
    SPC_TMASK0_CH30 = 0x40000000
    SPC_TMASK0_CH31 = 0x80000000

    SPC_TMASK1_NONE = 0x00000000
    SPC_TMASK1_CH32 = 0x00000001
    SPC_TMASK1_CH33 = 0x00000002
    SPC_TMASK1_CH34 = 0x00000004
    SPC_TMASK1_CH35 = 0x00000008
    SPC_TMASK1_CH36 = 0x00000010
    SPC_TMASK1_CH37 = 0x00000020
    SPC_TMASK1_CH38 = 0x00000040
    SPC_TMASK1_CH39 = 0x00000080
    SPC_TMASK1_CH40 = 0x00000100
    SPC_TMASK1_CH41 = 0x00000200
    SPC_TMASK1_CH42 = 0x00000400
    SPC_TMASK1_CH43 = 0x00000800
    SPC_TMASK1_CH44 = 0x00001000
    SPC_TMASK1_CH45 = 0x00002000
    SPC_TMASK1_CH46 = 0x00004000
    SPC_TMASK1_CH47 = 0x00008000
    SPC_TMASK1_CH48 = 0x00010000
    SPC_TMASK1_CH49 = 0x00020000
    SPC_TMASK1_CH50 = 0x00040000
    SPC_TMASK1_CH51 = 0x00080000
    SPC_TMASK1_CH52 = 0x00100000
    SPC_TMASK1_CH53 = 0x00200000
    SPC_TMASK1_CH54 = 0x00400000
    SPC_TMASK1_CH55 = 0x00800000
    SPC_TMASK1_CH56 = 0x01000000
    SPC_TMASK1_CH57 = 0x02000000
    SPC_TMASK1_CH58 = 0x04000000
    SPC_TMASK1_CH59 = 0x08000000
    SPC_TMASK1_CH60 = 0x10000000
    SPC_TMASK1_CH61 = 0x20000000
    SPC_TMASK1_CH62 = 0x40000000
    SPC_TMASK1_CH63 = 0x80000000

    SPC_TRIG_EXT_AVAILMODES = 40500l
    SPC_TRIG_EXT0_MODE = 40510l
    SPC_TRIG_EXT1_MODE = 40511l
    SPC_TRIG_XIO_AVAILMODES = 40550l
    SPC_TRIG_XIO0_MODE = 40560l
    SPC_TRIG_XIO1_MODE = 40561l
    SPC_TM_MODEMASK = 0x00FFFFFF
    SPC_TM_NONE = 0x00000000
    SPC_TM_POS = 0x00000001
    SPC_TM_NEG = 0x00000002
    SPC_TM_BOTH = 0x00000004
    SPC_TM_HIGH = 0x00000008
    SPC_TM_LOW = 0x00000010
    SPC_TM_WINENTER = 0x00000020
    SPC_TM_WINLEAVE = 0x00000040
    SPC_TM_INWIN = 0x00000080
    SPC_TM_OUTSIDEWIN = 0x00000100
    SPC_TM_SPIKE = 0x00000200
    SPC_TM_PATTERN = 0x00000400
    SPC_TM_STEEPPOS = 0x00000800
    SPC_TM_STEEPNEG = 0x00001000
    SPC_TM_EXTRAMASK = 0xFF000000
    SPC_TM_REARM = 0x01000000
    SPC_TM_PW_SMALLER = 0x02000000
    SPC_TM_PW_GREATER = 0x04000000
    SPC_TM_DOUBLEEDGE = 0x08000000

    SPC_TRIG_PATTERN_AVAILMODES = 40580l
    SPC_TRIG_PATTERN_MODE = 40590l

    SPC_TRIG_CH_AVAILMODES = 40600l
    SPC_TRIG_CH0_MODE = 40610l
    SPC_TRIG_CH1_MODE = 40611l
    SPC_TRIG_CH2_MODE = 40612l
    SPC_TRIG_CH3_MODE = 40613l
    SPC_TRIG_CH4_MODE = 40614l
    SPC_TRIG_CH5_MODE = 40615l
    SPC_TRIG_CH6_MODE = 40616l
    SPC_TRIG_CH7_MODE = 40617l
    SPC_TRIG_CH8_MODE = 40618l
    SPC_TRIG_CH9_MODE = 40619l
    SPC_TRIG_CH10_MODE = 40620l
    SPC_TRIG_CH11_MODE = 40621l
    SPC_TRIG_CH12_MODE = 40622l
    SPC_TRIG_CH13_MODE = 40623l
    SPC_TRIG_CH14_MODE = 40624l
    SPC_TRIG_CH15_MODE = 40625l
    SPC_TRIG_CH16_MODE = 40626l
    SPC_TRIG_CH17_MODE = 40627l
    SPC_TRIG_CH18_MODE = 40628l
    SPC_TRIG_CH19_MODE = 40629l
    SPC_TRIG_CH20_MODE = 40630l
    SPC_TRIG_CH21_MODE = 40631l
    SPC_TRIG_CH22_MODE = 40632l
    SPC_TRIG_CH23_MODE = 40633l
    SPC_TRIG_CH24_MODE = 40634l
    SPC_TRIG_CH25_MODE = 40635l
    SPC_TRIG_CH26_MODE = 40636l
    SPC_TRIG_CH27_MODE = 40637l
    SPC_TRIG_CH28_MODE = 40638l
    SPC_TRIG_CH29_MODE = 40639l
    SPC_TRIG_CH30_MODE = 40640l
    SPC_TRIG_CH31_MODE = 40641l

    SPC_TRIG_CH32_MODE = 40642l
    SPC_TRIG_CH33_MODE = 40643l
    SPC_TRIG_CH34_MODE = 40644l
    SPC_TRIG_CH35_MODE = 40645l
    SPC_TRIG_CH36_MODE = 40646l
    SPC_TRIG_CH37_MODE = 40647l
    SPC_TRIG_CH38_MODE = 40648l
    SPC_TRIG_CH39_MODE = 40649l
    SPC_TRIG_CH40_MODE = 40650l
    SPC_TRIG_CH41_MODE = 40651l
    SPC_TRIG_CH42_MODE = 40652l
    SPC_TRIG_CH43_MODE = 40653l
    SPC_TRIG_CH44_MODE = 40654l
    SPC_TRIG_CH45_MODE = 40655l
    SPC_TRIG_CH46_MODE = 40656l
    SPC_TRIG_CH47_MODE = 40657l
    SPC_TRIG_CH48_MODE = 40658l
    SPC_TRIG_CH49_MODE = 40659l
    SPC_TRIG_CH50_MODE = 40660l
    SPC_TRIG_CH51_MODE = 40661l
    SPC_TRIG_CH52_MODE = 40662l
    SPC_TRIG_CH53_MODE = 40663l
    SPC_TRIG_CH54_MODE = 40664l
    SPC_TRIG_CH55_MODE = 40665l
    SPC_TRIG_CH56_MODE = 40666l
    SPC_TRIG_CH57_MODE = 40667l
    SPC_TRIG_CH58_MODE = 40668l
    SPC_TRIG_CH59_MODE = 40669l
    SPC_TRIG_CH60_MODE = 40670l
    SPC_TRIG_CH61_MODE = 40671l
    SPC_TRIG_CH62_MODE = 40672l
    SPC_TRIG_CH63_MODE = 40673l


    SPC_TRIG_AVAILDELAY = 40800l
    SPC_TRIG_DELAY = 40810l

    SPC_SINGLESHOT = 41000l
    SPC_OUTONTRIGGER = 41100l
    SPC_RESTARTCONT = 41200l
    SPC_SINGLERESTART		=	41300l

    SPC_TRIGGERLEVEL = 42000l
    SPC_TRIGGERLEVEL0 = 42000l
    SPC_TRIGGERLEVEL1 = 42001l
    SPC_TRIGGERLEVEL2 = 42002l
    SPC_TRIGGERLEVEL3 = 42003l
    SPC_TRIGGERLEVEL4 = 42004l
    SPC_TRIGGERLEVEL5 = 42005l
    SPC_TRIGGERLEVEL6 = 42006l
    SPC_TRIGGERLEVEL7 = 42007l
    SPC_TRIGGERLEVEL8 = 42008l
    SPC_TRIGGERLEVEL9 = 42009l
    SPC_TRIGGERLEVEL10 = 42010l
    SPC_TRIGGERLEVEL11 = 42011l
    SPC_TRIGGERLEVEL12 = 42012l
    SPC_TRIGGERLEVEL13 = 42013l
    SPC_TRIGGERLEVEL14 = 42014l
    SPC_TRIGGERLEVEL15 = 42015l

    SPC_AVAILHIGHLEVEL_MIN = 41997l
    SPC_AVAILHIGHLEVEL_MAX = 41998l
    SPC_AVAILHIGHLEVEL_STEP = 41999l

    SPC_HIGHLEVEL0 = 42000l
    SPC_HIGHLEVEL1 = 42001l
    SPC_HIGHLEVEL2 = 42002l
    SPC_HIGHLEVEL3 = 42003l
    SPC_HIGHLEVEL4 = 42004l
    SPC_HIGHLEVEL5 = 42005l
    SPC_HIGHLEVEL6 = 42006l
    SPC_HIGHLEVEL7 = 42007l
    SPC_HIGHLEVEL8 = 42008l
    SPC_HIGHLEVEL9 = 42009l
    SPC_HIGHLEVEL10 = 42010l
    SPC_HIGHLEVEL11 = 42011l
    SPC_HIGHLEVEL12 = 42012l
    SPC_HIGHLEVEL13 = 42013l
    SPC_HIGHLEVEL14 = 42014l
    SPC_HIGHLEVEL15 = 42015l

    SPC_AVAILLOWLEVEL_MIN = 42097l
    SPC_AVAILLOWLEVEL_MAX = 42098l
    SPC_AVAILLOWLEVEL_STEP = 42099l

    SPC_LOWLEVEL0 = 42100l
    SPC_LOWLEVEL1 = 42101l
    SPC_LOWLEVEL2 = 42102l
    SPC_LOWLEVEL3 = 42103l
    SPC_LOWLEVEL4 = 42104l
    SPC_LOWLEVEL5 = 42105l
    SPC_LOWLEVEL6 = 42106l
    SPC_LOWLEVEL7 = 42107l
    SPC_LOWLEVEL8 = 42108l
    SPC_LOWLEVEL9 = 42109l
    SPC_LOWLEVEL10 = 42110l
    SPC_LOWLEVEL11 = 42111l
    SPC_LOWLEVEL12 = 42112l
    SPC_LOWLEVEL13 = 42113l
    SPC_LOWLEVEL14 = 42114l
    SPC_LOWLEVEL15 = 42115l

    SPC_TRIG_CH0_LEVEL0 = 42200l
    SPC_TRIG_CH1_LEVEL0 = 42201l
    SPC_TRIG_CH2_LEVEL0 = 42202l
    SPC_TRIG_CH3_LEVEL0 = 42203l
    SPC_TRIG_CH4_LEVEL0 = 42204l
    SPC_TRIG_CH5_LEVEL0 = 42205l
    SPC_TRIG_CH6_LEVEL0 = 42206l
    SPC_TRIG_CH7_LEVEL0 = 42207l
    SPC_TRIG_CH8_LEVEL0 = 42208l
    SPC_TRIG_CH9_LEVEL0 = 42209l
    SPC_TRIG_CH10_LEVEL0 = 42210l
    SPC_TRIG_CH11_LEVEL0 = 42211l
    SPC_TRIG_CH12_LEVEL0 = 42212l
    SPC_TRIG_CH13_LEVEL0 = 42213l
    SPC_TRIG_CH14_LEVEL0 = 42214l
    SPC_TRIG_CH15_LEVEL0 = 42215l

    SPC_TRIG_CH0_LEVEL1 = 42300l
    SPC_TRIG_CH1_LEVEL1 = 42301l
    SPC_TRIG_CH2_LEVEL1 = 42302l
    SPC_TRIG_CH3_LEVEL1 = 42303l
    SPC_TRIG_CH4_LEVEL1 = 42304l
    SPC_TRIG_CH5_LEVEL1 = 42305l
    SPC_TRIG_CH6_LEVEL1 = 42306l
    SPC_TRIG_CH7_LEVEL1 = 42307l
    SPC_TRIG_CH8_LEVEL1 = 42308l
    SPC_TRIG_CH9_LEVEL1 = 42309l
    SPC_TRIG_CH10_LEVEL1 = 42310l
    SPC_TRIG_CH11_LEVEL1 = 42311l
    SPC_TRIG_CH12_LEVEL1 = 42312l
    SPC_TRIG_CH13_LEVEL1 = 42313l
    SPC_TRIG_CH14_LEVEL1 = 42314l
    SPC_TRIG_CH15_LEVEL1 = 42315l

    SPC_TRIGGERPATTERN = 43000l
    SPC_TRIGGERPATTERN0 = 43000l
    SPC_TRIGGERPATTERN1 = 43001l
    SPC_TRIGGERMASK = 43100l
    SPC_TRIGGERMASK0 = 43100l
    SPC_TRIGGERMASK1 = 43101l

    SPC_PULSEWIDTH = 44000l
    SPC_PULSEWIDTH0 = 44000l
    SPC_PULSEWIDTH1 = 44001l

    SPC_TRIG_CH_AVAILPULSEWIDTH = 44100l
    SPC_TRIG_CH_PULSEWIDTH = 44101l
    SPC_TRIG_CH0_PULSEWIDTH = 44101l
    SPC_TRIG_CH1_PULSEWIDTH = 44102l
    SPC_TRIG_CH2_PULSEWIDTH = 44103l
    SPC_TRIG_CH3_PULSEWIDTH = 44104l
    SPC_TRIG_CH4_PULSEWIDTH = 44105l
    SPC_TRIG_CH5_PULSEWIDTH = 44106l
    SPC_TRIG_CH6_PULSEWIDTH = 44107l
    SPC_TRIG_CH7_PULSEWIDTH = 44108l
    SPC_TRIG_CH8_PULSEWIDTH = 44109l
    SPC_TRIG_CH9_PULSEWIDTH = 44110l
    SPC_TRIG_CH10_PULSEWIDTH = 44111l
    SPC_TRIG_CH11_PULSEWIDTH = 44112l
    SPC_TRIG_CH12_PULSEWIDTH = 44113l
    SPC_TRIG_CH13_PULSEWIDTH = 44114l
    SPC_TRIG_CH14_PULSEWIDTH = 44115l
    SPC_TRIG_CH15_PULSEWIDTH = 44116l

    SPC_TRIG_EXT_AVAILPULSEWIDTH = 44200l
    SPC_TRIG_EXT0_PULSEWIDTH = 44210l


    SPC_READTROFFSET = 45000l
    SPC_TRIGGEREDGE = 46000l
    SPC_TRIGGEREDGE0 = 46000l
    SPC_TRIGGEREDGE1 = 46001l
    TE_POS = 10000l
    TE_NEG = 10010l
    TE_BOTH = 10020l
    TE_NONE = 10030l


    #  ----- Timestamp -----
    CH_TIMESTAMP = 9999l

    SPC_TIMESTAMP_CMD = 47000l
    TS_RESET = 0l
    TS_MODE_DISABLE = 10l
    TS_MODE_STARTRESET = 11l
    TS_MODE_STANDARD = 12l
    TS_MODE_REFCLOCK = 13l
    TS_MODE_TEST5555 = 90l
    TS_MODE_TESTAAAA = 91l
    TS_MODE_ZHTEST = 92l

    #  ----- modes for M2i hardware (bitmap) -----
    SPC_TIMESTAMP_AVAILMODES = 47001l
    SPC_TSMODE_DISABLE = 0x00000000
    SPC_TS_RESET = 0x00000001
    SPC_TSMODE_STANDARD = 0x00000002
    SPC_TSMODE_STARTRESET = 0x00000004
    SPC_TSCNT_INTERNAL = 0x00000100
    SPC_TSCNT_REFCLOCKPOS = 0x00000200
    SPC_TSCNT_REFCLOCKNEG = 0x00000400

    SPC_TSXIOACQ_DISABLE = 0x00000000
    SPC_TSXIOACQ_ENABLE = 0x00001000

    SPC_TSMODE_MASK = 0x000000FF
    SPC_TSCNT_MASK = 0x00000F00


    SPC_TIMESTAMP_STATUS = 47010l
    TS_FIFO_EMPTY = 0l
    TS_FIFO_LESSHALF = 1l
    TS_FIFO_MOREHALF = 2l
    TS_FIFO_OVERFLOW = 3l

    SPC_TIMESTAMP_COUNT = 47020l
    SPC_TIMESTAMP_STARTTIME = 47030l
    SPC_TIMESTAMP_STARTDATE = 47031l
    SPC_TIMESTAMP_FIFO = 47040l
    SPC_TIMESTAMP_TIMEOUT = 47045l

    SPC_TIMESTAMP_RESETMODE = 47050l
    TS_RESET_POS = 10l
    TS_RESET_NEG = 20l



    #  ----- Extra I/O module -----
    SPC_XIO_DIRECTION = 47100l
    XD_CH0_INPUT = 0l
    XD_CH0_OUTPUT = 1l
    XD_CH1_INPUT = 0l
    XD_CH1_OUTPUT = 2l
    XD_CH2_INPUT = 0l
    XD_CH2_OUTPUT = 4l
    SPC_XIO_DIGITALIO = 47110l
    SPC_XIO_ANALOGOUT0 = 47120l
    SPC_XIO_ANALOGOUT1 = 47121l
    SPC_XIO_ANALOGOUT2 = 47122l
    SPC_XIO_ANALOGOUT3 = 47123l
    SPC_XIO_WRITEDACS = 47130l



    #  ----- Star-Hub -----
    SPC_STARHUB_CMD = 48000l
    SH_INIT = 0l      #  Internal use: Initialisation of Starhub
    SH_AUTOROUTE = 1l      #  Internal use: Routing of Starhub
    SH_INITDONE = 2l     #  Internal use: End of Init
    SH_SYNCSTART = 3l     #  Internal use: Synchronisation

    SPC_STARHUB_STATUS = 48010l

    SPC_STARHUB_ROUTE0 = 48100l      #  Routing Information for Test
    SPC_STARHUB_ROUTE99 = 48199l      #  ...


    #  Spcm driver (M2i) sync setup registers
    SPC_SYNC_READ_SYNCCOUNT = 48990l      #  number of sync'd cards

    SPC_SYNC_READ_CARDIDX0 = 49000l      #  read index of card at location 0 of sync
    SPC_SYNC_READ_CARDIDX1 = 49001l      #  ...
    SPC_SYNC_READ_CARDIDX2 = 49002l      #  ...
    SPC_SYNC_READ_CARDIDX3 = 49003l      #  ...
    SPC_SYNC_READ_CARDIDX4 = 49004l      #  ...
    SPC_SYNC_READ_CARDIDX5 = 49005l      #  ...
    SPC_SYNC_READ_CARDIDX6 = 49006l      #  ...
    SPC_SYNC_READ_CARDIDX7 = 49007l      #  ...
    SPC_SYNC_READ_CARDIDX8 = 49008l      #  ...
    SPC_SYNC_READ_CARDIDX9 = 49009l      #  ...
    SPC_SYNC_READ_CARDIDX10 = 49010l      #  ...
    SPC_SYNC_READ_CARDIDX11 = 49011l      #  ...
    SPC_SYNC_READ_CARDIDX12 = 49012l      #  ...
    SPC_SYNC_READ_CARDIDX13 = 49013l      #  ...
    SPC_SYNC_READ_CARDIDX14 = 49014l      #  ...
    SPC_SYNC_READ_CARDIDX15 = 49015l      #  ...

    SPC_SYNC_READ_CABLECON0 = 49100l      #  read cable connection of card at location 0 of sync
    SPC_SYNC_READ_CABLECON1 = 49101l      #  ...
    SPC_SYNC_READ_CABLECON2 = 49102l      #  ...
    SPC_SYNC_READ_CABLECON3 = 49103l      #  ...
    SPC_SYNC_READ_CABLECON4 = 49104l      #  ...
    SPC_SYNC_READ_CABLECON5 = 49105l      #  ...
    SPC_SYNC_READ_CABLECON6 = 49106l      #  ...
    SPC_SYNC_READ_CABLECON7 = 49107l      #  ...
    SPC_SYNC_READ_CABLECON8 = 49108l      #  ...
    SPC_SYNC_READ_CABLECON9 = 49109l      #  ...
    SPC_SYNC_READ_CABLECON10 = 49110l      #  ...
    SPC_SYNC_READ_CABLECON11 = 49111l      #  ...
    SPC_SYNC_READ_CABLECON12 = 49112l      #  ...
    SPC_SYNC_READ_CABLECON13 = 49113l      #  ...
    SPC_SYNC_READ_CABLECON14 = 49114l      #  ...
    SPC_SYNC_READ_CABLECON15 = 49115l      #  ...

    SPC_SYNC_ENABLEMASK = 49200l      #  synchronisation enable (mask)
    SPC_SYNC_NOTRIGSYNCMASK = 49210l      #  trigger disabled for sync (mask)
    SPC_SYNC_CLKMASK = 49220l      #  clock master (mask)


    #  ----- Gain and Offset Adjust DAC's -----
    SPC_ADJ_START = 50000l

    SPC_ADJ_LOAD = 50000l
    SPC_ADJ_SAVE = 50010l
    ADJ_DEFAULT = 0l
    ADJ_USER0 = 1l
    ADJ_USER1 = 2l
    ADJ_USER2 = 3l
    ADJ_USER3 = 4l
    ADJ_USER4 = 5l
    ADJ_USER5 = 6l
    ADJ_USER6 = 7l
    ADJ_USER7 = 8l

    SPC_ADJ_AUTOADJ = 50020l
    ADJ_ALL = 0l
    ADJ_CURRENT = 1l
    ADJ_EXTERNAL = 2l
    ADJ_1MOHM	 = 3l

    SPC_ADJ_SOURCE_CALLBACK = 50021l
    SPC_ADJ_PROGRESS_CALLBACK = 50022l

    SPC_ADJ_SET = 50030l
    SPC_ADJ_FAILMASK = 50040l

    SPC_ADJ_CALIBSOURCE			=50050l
#define		ADJ_CALSRC_OFF				0l
#define		ADJ_CALSRC_GND			 = -1l
#define		ADJ_CALSRC_GNDOFFS		 = -2l

    SPC_ADJ_CALIBVALUE0			=50060l
    SPC_ADJ_CALIBVALUE1			=50061l
    SPC_ADJ_CALIBVALUE2			=50062l
    SPC_ADJ_CALIBVALUE3			=50063l
    SPC_ADJ_CALIBVALUE4			=50064l
    SPC_ADJ_CALIBVALUE5			=50065l
    SPC_ADJ_CALIBVALUE6			=50066l
    SPC_ADJ_CALIBVALUE7			=50067l


    SPC_ADJ_OFFSET0 = 51000l
    SPC_ADJ_OFFSET999 = 51999l

    SPC_ADJ_GAIN0 = 52000l
    SPC_ADJ_GAIN999 = 52999l

    SPC_ADJ_CORRECT0 = 53000l
    SPC_ADJ_OFFS_CORRECT0 = 53000l
    SPC_ADJ_CORRECT999 = 53999l
    SPC_ADJ_OFFS_CORRECT999 = 53999l

    SPC_ADJ_XIOOFFS0 = 54000l
    SPC_ADJ_XIOOFFS1 = 54001l
    SPC_ADJ_XIOOFFS2 = 54002l
    SPC_ADJ_XIOOFFS3 = 54003l

    SPC_ADJ_XIOGAIN0 = 54010l
    SPC_ADJ_XIOGAIN1 = 54011l
    SPC_ADJ_XIOGAIN2 = 54012l
    SPC_ADJ_XIOGAIN3 = 54013l

    SPC_ADJ_GAIN_CORRECT0 = 55000l
    SPC_ADJ_GAIN_CORRECT999 = 55999l

    SPC_ADJ_OFFSCALIBCORRECT0 = 56000l
    SPC_ADJ_OFFSCALIBCORRECT999= 56999l

    SPC_ADJ_GAINCALIBCORRECT0 = 57000l
    SPC_ADJ_GAINCALIBCORRECT999 =57999l

    SPC_ADJ_END = 59999l



    #  ----- FIFO Control -----
    SPC_FIFO_BUFFERS = 60000l      #  number of FIFO buffers
    SPC_FIFO_BUFLEN = 60010l      #  len of each FIFO buffer
    SPC_FIFO_BUFCOUNT = 60020l      #  number of FIFO buffers tranfered until now
    SPC_FIFO_BUFMAXCNT = 60030l      #  number of FIFO buffers to be transfered (0=continuous)
    SPC_FIFO_BUFADRCNT = 60040l      #  number of FIFO buffers allowed
    SPC_FIFO_BUFREADY = 60050l      #  fifo buffer ready register (same as SPC_COMMAND + SPC_FIFO_BUFREADY0...)
    SPC_FIFO_BUFADR0 = 60100l      #  adress of FIFO buffer no. 0
    SPC_FIFO_BUFADR1 = 60101l     #  ...
    SPC_FIFO_BUFADR2 = 60102l      #  ...
    SPC_FIFO_BUFADR3 = 60103l      #  ...
    SPC_FIFO_BUFADR4 = 60104l      #  ...
    SPC_FIFO_BUFADR5 = 60105l      #  ...
    SPC_FIFO_BUFADR6 = 60106l      #  ...
    SPC_FIFO_BUFADR7 = 60107l      #  ...
    SPC_FIFO_BUFADR8 = 60108l      #  ...
    SPC_FIFO_BUFADR9 = 60109l      #  ...
    SPC_FIFO_BUFADR10 = 60110l      #  ...
    SPC_FIFO_BUFADR11 = 60111l      #  ...
    SPC_FIFO_BUFADR12 = 60112l      #  ...
    SPC_FIFO_BUFADR13 = 60113l      #  ...
    SPC_FIFO_BUFADR14 = 60114l      #  ...
    SPC_FIFO_BUFADR15 = 60115l      #  ...
    SPC_FIFO_BUFADR255 = 60355l      #  last



    #  ----- Filter -----
    SPC_FILTER = 100000l



    #  ----- Pattern -----
    SPC_PATTERNENABLE = 110000l
    SPC_READDIGITAL = 110100l



    #  ----- Miscellanous -----
    SPC_MISCDAC0 = 200000l
    SPC_MISCDAC1 = 200010l
    SPC_FACTORYMODE = 200020l
    SPC_DIRECTDAC = 200030l
    SPC_NOTRIGSYNC = 200040l
    SPC_DSPDIRECT = 200100l
    SPC_DMAPHYSICALADR = 200110l
    SPC_MICXCOMPATIBILITYMODE = 200120l
    SPC_TEST_FIFOSPEED = 200121l
    SPC_RELOADDEMO = 200122l
    SPC_OVERSAMPLINGFACTOR	=	200123l
    SPC_XYZMODE = 200200l
    SPC_INVERTDATA = 200300l
    SPC_GATEMARKENABLE = 200400l
    SPC_CONTOUTMARK = 200450l
    SPC_EXPANDINT32 = 200500l
    SPC_NOPRETRIGGER = 200600l
    SPC_RELAISWAITTIME = 200700l
    SPC_DACWAITTIME = 200710l
    SPC_ILAMODE = 200800l
    SPC_NMDGMODE = 200810l
    SPC_CKADHALF_OUTPUT = 200820l
    SPC_LONGTRIG_OUTPUT = 200830l
    SPC_STOREMODAENDOFSEGMENT = 200840l
    SPC_ENHANCEDSTATUS = 200900l
    SPC_FILLSIZEPROMILLE = 200910l
    SPC_OVERRANGEBIT = 201000l
    SPC_2CH8BITMODE = 201100l
    SPC_12BITMODE = 201200l
    SPC_HOLDLASTSAMPLE = 201300l
    SPC_CKSYNC0 = 202000l
    SPC_CKSYNC1 = 202001l
    SPC_DISABLEMOD0 = 203000l
    SPC_DISABLEMOD1 = 203010l
    SPC_ENABLEOVERRANGECHECK = 204000l
    SPC_OVERRANGESTATUS = 204010l
    SPC_BITMODE = 205000l

    SPC_READBACK = 206000l
    SPC_AVAILSTOPLEVEL = 206009l
    SPC_STOPLEVEL1 = 206010l
    SPC_STOPLEVEL0 = 206020l
    SPC_CH0_STOPLEVEL = 206020l
    SPC_CH1_STOPLEVEL = 206021l
    SPC_CH2_STOPLEVEL = 206022l
    SPC_CH3_STOPLEVEL = 206023l
    SPCM_STOPLVL_TRISTATE = 0x00000001
    SPCM_STOPLVL_LOW = 0x00000002
    SPCM_STOPLVL_HIGH = 0x00000004
    SPCM_STOPLVL_HOLDLAST = 0x00000008
    SPCM_STOPLVL_ZERO = 0x00000010

    SPC_DIFFMODE = 206030l
    SPC_DACADJUST = 206040l

#define	SPC_AMP_MODE				207000l

    SPCM_FW_CTRL = 210000l
    SPCM_FW_CLOCK = 210010l
    SPCM_FW_CONFIG = 210020l
    SPCM_FW_MODULEA = 210030l
    SPCM_FW_MODULEB = 210031l
    SPCM_FW_MODEXTRA = 210050l

    SPC_MULTI = 220000l
    SPC_DOUBLEMEM = 220100l
    SPC_MULTIMEMVALID = 220200l
    SPC_BANK = 220300l
    SPC_GATE = 220400l
    SPC_RELOAD = 230000l
    SPC_USEROUT = 230010l
    SPC_WRITEUSER0 = 230100l
    SPC_WRITEUSER1 = 230110l
    SPC_READUSER0 = 230200l
    SPC_READUSER1 = 230210l
    SPC_MUX = 240000l
    SPC_ADJADC = 241000l
    SPC_ADJOFFS0 = 242000l
    SPC_ADJOFFS1 = 243000l
    SPC_ADJGAIN0 = 244000l
    SPC_ADJGAIN1 = 245000l
    SPC_READEPROM = 250000l
    SPC_WRITEEPROM = 250010l
    SPC_DIRECTIO = 260000l
    SPC_DIRECT_MODA = 260010l
    SPC_DIRECT_MODB = 260020l
    SPC_DIRECT_EXT0 = 260030l
    SPC_DIRECT_EXT1 = 260031l
    SPC_DIRECT_EXT2 = 260032l
    SPC_DIRECT_EXT3 = 260033l
    SPC_DIRECT_EXT4 = 260034l
    SPC_DIRECT_EXT5 = 260035l
    SPC_DIRECT_EXT6 = 260036l
    SPC_DIRECT_EXT7 = 260037l
    SPC_MEMTEST = 270000l
    SPC_NODMA = 275000l
    SPC_NOCOUNTER = 275010l
    SPC_NOSCATTERGATHER = 275020l
    SPC_RUNINTENABLE = 290000l
    SPC_XFERBUFSIZE = 295000l
    SPC_CHLX = 295010l
    SPC_SPECIALCLOCK = 295100l
    SPC_STARTDELAY = 295110l
    SPC_BASISTTLTRIG = 295120l
    SPC_TIMEOUT = 295130l
    SPC_LOGDLLCALLS = 299999l






    #  ----- PCK400 -----
    SPC_FREQUENCE = 300000l
    SPC_DELTAFREQUENCE = 300010l
    SPC_PINHIGH = 300100l
    SPC_PINLOW = 300110l
    SPC_PINDELTA = 300120l
    SPC_STOPLEVEL = 300200l
    SPC_PINRELAIS = 300210l
    SPC_EXTERNLEVEL = 300300l



    #  ----- PADCO -----
    SPC_COUNTER0 = 310000l
    SPC_COUNTER1 = 310001l
    SPC_COUNTER2 = 310002l
    SPC_COUNTER3 = 310003l
    SPC_COUNTER4 = 310004l
    SPC_COUNTER5 = 310005l
    SPC_MODE0 = 310100l
    SPC_MODE1 = 310101l
    SPC_MODE2 = 310102l
    SPC_MODE3 = 310103l
    SPC_MODE4 = 310104l
    SPC_MODE5 = 310105l
    CM_SINGLE = 1l
    CM_MULTI = 2l
    CM_POSEDGE = 4l
    CM_NEGEDGE = 8l
    CM_HIGHPULSE = 16l
    CM_LOWPULSE = 32l



    #  ----- PAD1616 -----
    SPC_SEQUENCERESET = 320000l
    SPC_SEQUENCEADD = 320010l
    SEQ_IR_10000MV = 0l
    SEQ_IR_5000MV = 1l
    SEQ_IR_2000MV = 2l
    SEQ_IR_1000MV = 3l
    SEQ_IR_500MV = 4l
    SEQ_CH0 = 0l
    SEQ_CH1 = 8l
    SEQ_CH2 = 16l
    SEQ_CH3 = 24l
    SEQ_CH4 = 32l
    SEQ_CH5 = 40l
    SEQ_CH6 = 48l
    SEQ_CH7 = 56l
    SEQ_CH8 = 64l
    SEQ_CH9 = 72l
    SEQ_CH10 = 80l
    SEQ_CH11 = 88l
    SEQ_CH12 = 96l
    SEQ_CH13 = 104l
    SEQ_CH14 = 112l
    SEQ_CH15 = 120l
    SEQ_TRIGGER = 128l
    SEQ_START = 256l



    #  ----- Option CA -----
    SPC_CA_MODE = 330000l
    CAMODE_OFF = 0l
    CAMODE_CDM = 1l
    CAMODE_KW = 2l
    CAMODE_OT = 3l
    CAMODE_CDMMUL = 4l
    SPC_CA_TRIGDELAY = 330010l
    SPC_CA_CKDIV = 330020l
    SPC_CA_PULS = 330030l
    SPC_CA_CKMUL = 330040l
    SPC_CA_DREHZAHLFORMAT = 330050l
    CADREH_4X4 = 0l
    CADREH_1X16 = 1l
    SPC_CA_KWINVERT = 330060l
    SPC_CA_OUTA = 330100l
    SPC_CA_OUTB = 330110l
    CAOUT_TRISTATE = 0l
    CAOUT_LOW = 1l
    CAOUT_HIGH = 2l
    CAOUT_CDM = 3l
    CAOUT_OT = 4l
    CAOUT_KW = 5l
    CAOUT_TRIG = 6l
    CAOUT_CLK = 7l
    CAOUT_KW60 = 8l
    CAOUT_KWGAP = 9l
    CAOUT_TRDLY = 10l
    CAOUT_INVERT = 16l



    #  ----- Hardware registers (debug use only) -----
    SPC_REG0x00 = 900000l
    SPC_REG0x02 = 900010l
    SPC_REG0x04 = 900020l
    SPC_REG0x06 = 900030l
    SPC_REG0x08 = 900040l
    SPC_REG0x0A = 900050l
    SPC_REG0x0C = 900060l
    SPC_REG0x0E = 900070l

    SPC_DEBUGREG0 = 900100l
    SPC_DEBUGREG15 = 900115l
    SPC_DEBUGVALUE0 = 900200l
    SPC_DEBUGVALUE15 = 900215l

    SPC_MI_ISP = 901000l
    ISP_TMS_0 = 0l
    ISP_TMS_1 = 1l
    ISP_TDO_0 = 0l
    ISP_TDO_1 = 2l


    SPC_EE_RWAUTH = 901100l
    SPC_EE_REG = 901110l
    SPC_EE_RESETCOUNTER = 901120l

    #  ----- Test Registers -----
    SPC_TEST_BASE = 902000l
    SPC_TEST_LOCAL_START = 902100l
    SPC_TEST_LOCAL_END = 902356l
    SPC_TEST_PLX_START = 902400l
    SPC_TEST_PLX_END = 902656l
