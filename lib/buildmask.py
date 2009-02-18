"""
Functions to build mask files for PyDrizzle.
    - buildMaskImage(rootname,bitvalue,extname='DQ',extver=None):
        This function takes the DQ array(or array from extension given)
        and builds a bit mask as an input weighting mask for 'drizzle'.

    - buildShadowMaskImage(rootname,detnum,replace=no):
        This function builds a weighting image for use with drizzle from
        the WFPC2 shadow mask functions derived from 'wmosaic'.
"""

#
# Revision History:
#
#   14-Nov-2001 - Revised to produce proper simple FITS image starting
#                   with 'SIMPLE=T' keyword instead of 'XTENSION'. WJH
#
#   25-Jan-2002 - Converted to work with PyFITS V0.6.1 and numarray. WJH
#
#   12-June-2002 - Added check to remove old versions of or existing mask
#                  files before building a new one.
#   23-July-2002 - Saved space in mask file by using only Int8 instead of Int16
#
#   7-Mar-2003   - Updated to use memory mapping in PyFITS where possible
#
#   4-Jun-2003   - WFPC2 mask file now incorporates .c1h file if present
#
#  13-Jan-2005   - Simplified filename generation into one function and
#                   added output filename as input parameter to 'buildMask'
#                   functions. WJH
#
import string,os,types

from pytools import fileutil, readgeis

import pyfits
import numpy as N

def build_mask(imageObjectList,configObj):
    # value of driz_separate needs to come from configObj object/dictionary
    dqfile = []
    detnum = []
    outputnames = []
    instrument = []
    extname = []
    extver = []
    binned = []
        
    # Insure that input imageObject is a list
    if not isinstance(imageObjectList, list):
        imageObjectList = [imageObjectList]
    
    for img in imageObjectList:
        img.buildMask(configObj)
    """
        dqfile += img.getKeywordList('dqfile')
        detnum += img.getKeywordList('detnum')
        outputnames += img.getKeywordList('outputNames')
        instrument += [img._instrument]*img._numchips
        extname += [img.maskExt]*img._numchips
        extver += img.getKeywordList('_chip')
        binned += img.getKeywordList('binned')

    for chip in range(len(dqfile)):
        masknames = []
        if configObj['driz_separate']:
            masknames.append([outputnames[chip]['singleDrizMask'],configObj['driz_sep_bit']])
        if configObj['driz_combine']:
            masknames.append([outputnames[chip]['drizMask'],configObj['final_bits']])

        # Loop over all masks that need to be built for this chip: single and/or final
        for maskname in masknames:
            if instrument[chip] == 'WFPC2':
                buildShadowMaskImage(dqfile[chip],detnum[chip],extnum[chip],maskname[0],bitvalue=maskname[1],binned=binned[chip])
            else:
                print 'Building ',maskname,' for ',dqfile[chip]
                buildMaskImage(dqfile[chip],maskname[1],maskname[0],extname=extname[chip],extver=extver[chip]) 
    """
def buildMask(dqarr,bitvalue):
    """ Builds a bit-mask from an input DQ array and a bitvalue flag"""
    if bitvalue == None:
        return (dqarr * 0.0) + 1.0
    _maskarr = N.bitwise_or(dqarr,N.array([bitvalue]))
    return N.choose(N.greater(_maskarr,bitvalue),(1,0)).astype(N.uint8)


def buildMaskImage(rootname,bitvalue,output,extname='DQ',extver=1):
    """ Builds mask image from rootname's DQ array
        If there is no valid 'DQ' array in image, then return
        an empty string.
    """

    # If no bitvalue is set or rootname given, assume no mask is desired
    # However, this name would be useful as the output mask from
    # other processing, such as MultiDrizzle, so return it anyway.
    #if bitvalue == None or rootname == None:
    #    return None

    # build output name
    maskname = output

    # If an old version of the maskfile was present, remove it and rebuild it.
    if fileutil.findFile(maskname):
        fileutil.removeFile(maskname)

    # Open input file with DQ array
    fdq = fileutil.openImage(rootname,memmap=0,mode='readonly')
    try:
        _extn = fileutil.findExtname(fdq,extname,extver=extver)
        if _extn != None:
            # Read in DQ array
            dqarr = fdq[_extn].data
        else:
            dqarr = None
            
        # For the case where there is no DQ array,
        # create a mask image of all ones.
        if dqarr == None:
            # We need to get the dimensions of the output DQ array
            # Since the DQ array is non-existent, look for the SCI extension
            _sci_extn = fileutil.findExtname(fdq,'SCI',extver=extver)
            if _sci_extn != None:
                _shape = fdq[_sci_extn].data.shape
                dqarr = N.zeros(_shape,dtype=N.uint16)
            else:
                raise Exception
        # Build mask array from DQ array
        maskarr = buildMask(dqarr,bitvalue)
        #Write out the mask file as simple FITS file
        fmask = pyfits.open(maskname,'append')
        maskhdu = pyfits.PrimaryHDU(data=maskarr)
        fmask.append(maskhdu)

        #Close files
        fmask.close()
        del fmask
        fdq.close()
        del fdq

    except:
        fdq.close()
        del fdq
        # Safeguard against leaving behind an incomplete file
        if fileutil.findFile(maskname):
            os.remove(maskname)
        _errstr = "\nWarning: Problem creating MASK file for "+rootname+".\n"
        #raise IOError, _errstr
        print _errstr
        return None

    # Return the name of the mask image written out
    return maskname

# Utility functions for generating X and Y arrays for
# creating the WFPC2 shadow masks.
# Coefficients are from WMOSAIC function 'get_edge2.x'
"""
_coeffs = {'1':[[52.20921,0.009072887,0.009072887],[42.62779,0.009122855,-1.106709E-5]],
          '2':[[21.77283,0.01842164,-1.398300E-5],[47.68184,0.00265608,-1.468158E-5]],
          '3':[[44.18944,0.0138938,-1.412296E-5],[30.23626,0.008156041,-1.491324E-5]],
          '4':[[44.56632,0.003509023,-1.278723E-5],[40.91462,0.01273679,-1.063462E-5]]}
"""
def _func_Shadow_WF1y(x,y):
    return y + 0.5 - (42.62779 + 0.009122855*y - 1.106709E-5*y**2)
def _func_Shadow_WF1x(x,y):
    return x + 0.5 - (52.20921 + 0.009072887*x - 9.941337e-6*x**2)

def _func_Shadow_WF2y(x,y):
    return y + 0.5 - (47.68184 + 0.00265608*y - 1.468158E-5*y**2)
def _func_Shadow_WF2x(x,y):
    return x + 0.5 - (21.77283 + 0.01842164*x - 1.398300E-5*x**2)

def _func_Shadow_WF3y(x,y):
    return y + 0.5 - (30.23626 + 0.008156041*y - 1.491324E-5*y**2 )
def _func_Shadow_WF3x(x,y):
    return x + 0.5 - (44.18944 + 0.0138938*x - 1.412296E-5*x**2)

def _func_Shadow_WF4y(x,y):
    return y + 0.5 - (40.91462 + 0.01273679*y - 1.063462E-5*y**2)
def _func_Shadow_WF4x(x,y):
    return x + 0.5 - (44.56632 + 0.003509023*x - 1.278723E-5*x**2)

# Function for creating the weighting image for WFPC2 drizzling
# from the 'wmosaic' shadow mask polynomials.

def buildShadowMaskImage(dqfile,detnum,extnum,maskname,bitvalue=None,binned=1):
    """ Builds mask image from WFPC2 shadow calibrations.
      detnum - string value for 'DETECTOR' detector
    """
    # insure detnum is a string
    if not isinstance(detnum,types.StringType):
        detnum = repr(detnum)

    _funcroot = '_func_Shadow_WF'

    # build template shadow mask's filename
    _mask = 'wfpc2_inmask'+detnum+'.fits'

    # If an old version of the maskfile was present, remove it and rebuild it.
    if fileutil.findFile(maskname):
        fileutil.removeFile(maskname)

    _use_inmask = False
    if fileutil.findFile(dqfile) != True or bitvalue == None:
        _use_inmask = True

    # Check to see if file exists...
    if _use_inmask and not fileutil.findFile(_mask):
    # If not, create the file.
    # This takes a long time to run, so it should be done
    # only when absolutely necessary...
        try:
            _funcx = _funcroot+detnum+'x'
            _funcy = _funcroot+detnum+'y'

            _xarr = N.clip(N.fromfunction(eval(_funcx),(800,800)),0.0,1.0).astype(N.uint8)
            _yarr = N.clip(N.fromfunction(eval(_funcy),(800,800)),0.0,1.0).astype(N.uint8)
            maskarr = _xarr * _yarr

            if binned !=1:
                print 'in buildmask', binned
                bmaskarr = maskarr[::2,::2]
                bmaskarr *= maskarr[1::2,::2]
                bmaskarr *= maskarr[::2,1::2]
                bmaskarr *= maskarr[1::2,1::2]
                maskarr = bmaskarr.copy()
                del bmaskarr

            #Write out the mask file as simple FITS file
            fmask = pyfits.open(_mask,'append')
            maskhdu = pyfits.PrimaryHDU(data=maskarr)
            fmask.append(maskhdu)

            #Close files
            fmask.close()
            del fmask
        except:
            return None


    # Check for existance of input .c1h file for use in making inmask file
    if fileutil.findFile(dqfile) != True:
        print 'DQ file ',dqfile,' NOT found...'
        print 'Copying ',_mask,'to ',maskname,' as input mask file.'
        # Now, copy template mask file to output file, if necessary
        fileutil.copyFile(_mask,maskname,replace=True)
    elif bitvalue == None:
        # If bitvalue was not set, then do not use anything but shadow mask
        fileutil.copyFile(_mask,maskname,replace=True)
    else:
        #
        # Build full mask based on .c1h and shadow mask
        #
        fdq = fileutil.openImage(dqfile)
        #fsmask = pyfits.open(_mask,memmap=1,mode='readonly')
        try:
            # Read in DQ array from .c1h and from shadow mask files
            dqarr = fdq[int(extnum)].data
            #maskarr = fsmask[0].data

            # Build mask array from DQ array
            dqmaskarr = buildMask(dqarr,bitvalue)

            #Write out the mask file as simple FITS file
            fdqmask = pyfits.open(maskname,'append')
            maskhdu = pyfits.PrimaryHDU(data=dqmaskarr)
            fdqmask.append(maskhdu)

            #Close files
            fdqmask.close()
            del fdqmask
            fdq.close()
            del fdq

        except:
            fdq.close()
            del fdq
            # Safeguard against leaving behind an incomplete file
            if fileutil.findFile(maskname):
                os.remove(maskname)
            _errstr = "\nWarning: Problem creating DQMASK file for "+rootname+".\n"
            #raise IOError, _errstr
            print _errstr
            return None


    # Return the name of the mask image written out
    return maskname
