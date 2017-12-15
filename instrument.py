'''
The parent class for all the instruments to streamline big picture things
Contains basic keyword values common across all the instruments
Children will contain the instrument specific values

12/14/2017 M. Brown - Created initial file
'''

import datetime as dt
import calendar as cal

class Instrument:
    def __init__(self):
        self.instr = 'INSTRUME'
        self.utc = 'UTC'
        self.semester = 'SEMESTER'
        self.fileRoot = 'OUTFILE'        # Can be DATAFILE or ROOTNAME for specific instruments
        self.frameno = 'FRAMENO'     # Can be IMGNUM, FRAMENUM, FILENUM1, FILENUM2
        self.koaid = 'KOAID'
        self.outdir = 'OUTDIR'
        self.prefix = ''
        self.stageDir = ''
        self.ancDir = ''
        self.path = '/s/sdata'
        self.date = datetime.datetime()
        self.reducedDate = self.date.strftime('%Y%m%d')
