from datetime import datetime
import os
import hashlib
from urllib.request import urlopen
import json
from send_email import send_email
import glob
import re
import yaml
import db_conn

def get_root_dirs(rootDir, instr, utDate):
    """
    Gets the various rootDir subdirectories of interest

    @param rootDir: root directory for data processing
    @type rootDir: string
    @param instr: instrument name
    @type instr: string
    @param utDate: UT date (yyyy-mm-dd)
    @type utDate: string
    """

    instr = instr.upper()
    ymd = utDate
    ymd = ymd.replace('-', '')
    ymd = ymd.replace('/', '')

    dirs = {}
    dirs['stage']   = ''.join((rootDir, '/stage/', instr, '/', ymd))
    dirs['process'] = ''.join((rootDir, '/', instr))
    dirs['output']  = ''.join((rootDir, '/', instr, '/', ymd))
    dirs['lev0']    = ''.join((rootDir, '/', instr, '/', ymd, '/lev0'))
    dirs['lev1']    = ''.join((rootDir, '/', instr, '/', ymd, '/lev1'))
    dirs['anc']     = ''.join((rootDir, '/', instr, '/', ymd, '/anc'))
    dirs['udf']     = ''.join((dirs['anc'], '/udf'))

    return dirs




def make_dir_md5_table(readDir, endswith, outfile, fileList=None, regex=None):

    #ensure path ends in slash since we rely on that later here
    if not readDir.endswith('/'): readDir += '/'

    #get file list either direct or using 'endswith' search
    files = []
    if fileList:
        files = fileList
    else:        
        for dirpath, dirnames, filenames in os.walk(readDir):
            for f in filenames:
                if not dirpath.endswith('/'): dirpath += '/'
                match = False
                if endswith and f.endswith(endswith): match = True
                elif regex and re.search(regex, f): match = True
                if match:
                    files.append(dirpath + f)
        files.sort()
        
    #write out table
    with open(outfile, 'w') as fp:
        for file in files:
            md5 = hashlib.md5(open(file, 'rb').read()).hexdigest()
            bName = file.replace(readDir, '')
            fp.write(md5 + '  ' + bName + '\n')



def removeFilesByWildcard(wildcardPath):
    for file in glob.glob(wildcardPath):
        os.remove(file)



def get_api_data(url, getOne=False, isJson=True):
    '''
    Gets data for common calls to url API requests.

    #todo: add some better validation checks and maybe some options (ie getOne, typeCast)
    '''
    
    try:
        data = urlopen(url)
        data = data.read().decode('utf8')
        if isJson: data = json.loads(data)

        if getOne and len(data) > 0: 
            data = data[0]

        return data

    except Exception as e:
        return None



def do_fatal_error(msg, instr=None, utDate=None, failStage=None, log=None):

    #read config vars
    with open('config.live.ini') as f: config = yaml.safe_load(f)
    adminEmail = config['REPORT']['ADMIN_EMAIL']
    
    #form subject
    subject = 'DEP ERROR: ['
    if (instr)     : subject += instr     + ' '
    if (utDate)    : subject += utDate    + ' '
    if (failStage) : subject += failStage + ' '
    subject += ']'

    #always print
    print (subject + ' ' + msg)

    #if log then log
    if log: log.error(subject + ' ' + msg)

    #if admin email and not dev then email
    if (adminEmail != ''):
        send_email(adminEmail, adminEmail, subject, msg)



def update_koatpx(instr, utDate, column, value, log=''):
    """
    Sends command to update KOA data

    @param instrObj: the instrument object
    @param column: column to update in koa.koatpx
    @type column: string
    @param value: value to update column to
    @type value: string
    """
    db = db_conn.db_conn('config.live.ini', configKey='DATABASE')

    # If entry not in database, create it
    query = f'select count(*) as num from koatpx where instr="{instr}" and utdate="{utDate}"'
    check = db.query('koa', query, getOne=True)
    if check is False:
        if log: log.error(f'update_koatpx failed for: {instr}, {utDate}, {column}, {value}')
        return False
    if int(check['num']) == 0:
        query = f'insert into koatpx set instr="{instr}", utdate="{utDate}"'
        if log: log.info(query)
        check = db.query('koa', query)
        if check is False or int(check) == 0:
            if log: log.error(f'update_koatpx failed for: {instr}, {utDate}, {column}, {value}')
            return False

    # Now update it
    query = f'update koatpx set {column}="{value}" where instr="{instr}" and utdate="{utDate}"'
    if log: log.info(query)
    check = db.query('koa', query)
    if check is False:
        if log: log.error(f'update_koatpx failed for: {instr}, {utDate}, {column}, {value}')
        return False

    return True


def get_directory_size(dir):
    """
    Returns the directory size in MB

    @param dir: directory to determine size for
    @type dir: string
    """

    #directory doesn't exist
    if not os.path.isdir(dir):
        return 0

    #walk through and sum up size
    total = 0
    for dirpath, dirnames, filenames in os.walk(dir):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return str(total/1000000.0)


def get_prog_inst(semid, default=None, log=None, isToO=False):
    """
    Query the proposalsAPI and get the program institution

    @type semid: string
    @param semid: the program ID - consists of semester and progname (ie 2017B_U428)
    """

    api = get_proposal_api()
    url = api + 'ktn='+semid+'&cmd=getAllocInst&json=True'
    data = get_api_data(url)
    if not data or not data.get('success'):
        if log: log.error('Unable to query API: ' + url)
        return default
    else:
        val = data.get('data', {}).get('AllocInst', default)
        return val

def get_prog_pi(semid, default=None, log=None):
    """
    Query for program's PI last name

    @type semid: string
    @param semid: the program ID - consists of semester and progname (ie 2017B_U428)
    """
    db = db_conn.db_conn('config.live.ini', configKey='DATABASE')
    query = ( 'select pi.pi_lastname, pi.pi_firstname '
              ' from koa_program as p, koa_pi as pi '
             f' where p.semid="{semid}" and p.piID=pi.piID')
    data = db.query('koa', query, getOne=True)
    if not data or 'pi_lastname' not in data:
        if log: log.error(f'Unable to get PI name for semid {semid}')
        return default
    else:
        val = data['pi_lastname'].replace(' ','')
        return val


def get_prog_title(semid, default=None, log=None):
    """
    Query the DB and get the program title

    @type semid: string
    @param semid: the program ID - consists of semester and progname (ie 2017B_U428)
    """
    db = db_conn.db_conn('config.live.ini', configKey='DATABASE')
    query = f'select progtitl from koa_program where semid="{semid}"'
    data = db.query('koa', query, getOne=True)

    if not data or 'progtitl' not in data:
        if log: log.error(f'Unable to get title for semid {semid}')
        return default
    else:
        return data['progtitl']


def is_progid_valid(progid):

    if not progid: return False

    #get valid parts
    if   progid.count('_') > 1 : return False    
    elif progid.count('_') == 1: sem, progid = progid.split('_')
    else                       : sem = False

    #checks
    if len(progid) <= 2:      return False
    if len(progid) >= 6:      return False
    if " " in progid:         return False
    if "PROGID" in progid:    return False
    if sem and len(sem) != 5: return False

    return True


def get_progid_assign(assigns, utc):
    '''
    Get fits progid assignment by time based on config option string that 
    must be formatted with comma-separated split times like the follwoing examples:
     "U205"
     "U205,10:21:00,C251"
     "U205,10:21:00,C251,13:45:56,N123"
    '''
    parts = assigns.split(',')
    assert len(parts) % 2 == 1, "ERROR: Incorrect use of ASSIGN_PROGNAME"
    if len(parts) == 1: return parts[0]

    fitsTime = datetime.strptime(utc, '%H:%M:%S.%f')
    for i in range(1, len(parts), 2):
        progid = parts[i-1]
        t = parts[i]
        splitTime = datetime.strptime(t, '%H:%M:%S')
        if fitsTime <= splitTime:
            return progid
    return parts[-1]


def get_proposal_api():
    '''
    Returns the proposal API url from the config file
    '''
    with open('config.live.ini') as f: config = yaml.safe_load(f)
    return config.get('API', {}).get('PROPAPI')

