'''
This is the class to handle all the DEIMOS specific attributes
DEIMOS specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

class Deimos(instrument.Instrument):
    def __init__(self):
        # Call the parent init to get all the shared variables
        super(Deimos, self).__init__(self)

        # DEIMOS uses DATAFILE instead of OUTFILE
        self.root = 'DATAFILE'
        # DEIMOS uses FRAMENUM instead of FRAMENO
        self.frameno = 'FRAMENUM'
        # Set the deimos specific paths to anc and stage
        self.ancDir = '/koadata29/DEIMOS/' + self.reducedDate + '/anc'
        self.stageDir = '/koadata29/stage'
        # Generate the paths to the DEIMOS datadisk accounts
        self.paths = self.getDirList()


    def getDirList(self):
        '''
        Function to generate the paths to all the DEIMOS accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata100'
        for i in range(1,4):
            path2 = path + str(i)
            for i in range(1,21):
                path3 = path2 + '/deimos' + str(i)
                dirs.append(path3)
            dirs.append(path2 + '/dmoseng')
        return dirs
