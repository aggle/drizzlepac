#
#   Authors: Christopher Hanley
#   Program: ir_input.py
#   Purpose: Class used to model IR specific instrument data.

from input_image import InputImage

class IRInputImage(InputImage):
    """
    
    IRInputImage
    ------------
    
    The IRInputImage class is the parent class for all of 
    the IR based instrument classes.

    """
    SEPARATOR = '_'


    def __init__(self,input,dqname,platescale,memmap=0,proc_unit="native"):
        """
        Constructor for IRInputImage class object.
        """
        InputImage.__init__(self,input,dqname,platescale,memmap=0,proc_unit=proc_unit)
        
    def isCountRate(self):
        """
        isCountRate: Method or IRInputObject used to indicate if the
        science data is in units of counts or count rate.  This method
        assumes that the keyword 'BUNIT' is in the header of the input
        FITS file.
        """
        
        if self.header.has_key('BUNIT'):       
            if self.header['BUINT'].find("/") != -1:
                return True
        else:
            return False

    def getsampimg(self):
        """
        
        Purpose
        =======
        Return the samp image array.  This method will return
        a ones for all detectors by default.  
                
        """
        try:
            hdulist = fileutil.openImage(self.name,mode='readonly',memmap=0)
            extnhdulist = fileutil.getExtn(hdulist,extn="SAMP")
            sampimage = extnhdulist.data[self.ltv2:self.size2,self.ltv1:self.size1]
        except:
            sampimage = 1
        return sampimage
