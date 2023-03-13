from enum import Enum

USERNAME = None
PASSWORD = None
EMAIL_APPCODE = None

DF_PATH = r'.\backup.pkl'
FORBIDDEN_CODE = 403
SERVICE_UNAVAILABLE = 503

NUMBER_REVIEWERS = 50
NUMBER_PAPERS = 550
REQUIRED_BIDS = 1

BID_EXTRACTION_INTERVAL = 10  # Seconds
IPRICE_UPDATE_INTERVAL = 30 * 60  # Seconds
DF_BACKUP_INTERVAL = 60 * 60  # 1 Hours
DF_BACKUP_PATH = 'bids_backup.pkl'

REQUIRED_POINTS = 2000

SAVE_BIDS = True
SAVE_IPRICES = True

class Bids(Enum):
    PINCH = '3'
    WILLING = '4'
    EAGER = '5'


USERS = ['royfa@post.bgu.ac.il',
 'reshefm@ie.technion.ac.il',
 'her.shira@campus.technion.ac.il',
 'gili.bielous@campus.technion.ac.il',
 'marwa@campus.technion.ac.il',
 'moran.ze@campus.technion.ac.il',
 'yosi7700@campus.technion.ac.il',
 'itay.yacov@campus.technion.ac.il',
 'zaoui@campus.technion.ac.il',
 'abramowitz@campus.technion.ac.il',
 'renaswaid@campus.technion.ac.il',
 'asmaa.ma@campus.technion.ac.il',
 'henor@campus.technion.ac.il',
 'yarakhateeb@campus.technion.ac.il',
 'dmitryk@campus.technion.ac.il',
 'esraa.sirhan@campus.technion.ac.il',
 'lirontyomkin@campus.technion.ac.il',
 'diran.t@campus.technion.ac.il',
 'saherkhoury@campus.technion.ac.il',
 'adilevi@campus.technion.ac.il',
 'hilamalka@campus.technion.ac.il',
 'lyanasla@campus.technion.ac.il',
 'shams.eg@campus.technion.ac.il',
 'michael.ukh@campus.technion.ac.il',
 'aviv-zi@campus.technion.ac.il',
 'karinsukonik@campus.technion.ac.il',
 'rula.egbaria@campus.technion.ac.il',
 'bachrachj@campus.technion.ac.il',
 'amitfrangi@campus.technion.ac.il',
 'mor.levinbuk@campus.technion.ac.il',
 'kamilyaziyan@campus.technion.ac.il',
 'idanetgar@campus.technion.ac.il',
 'yael-k@campus.technion.ac.il',
 'hillysegal@campus.technion.ac.il',
 'yuval-lee@campus.technion.ac.il',
 'khsaleem@campus.technion.ac.il',
 'ozhuly@campus.technion.ac.il',
 'meital.abadi@campus.technion.ac.il',
 'inbar.nac@campus.technion.ac.il',
 'tzufbechor@campus.technion.ac.il',
 'alonaricha@campus.technion.ac.il',
 'salma.ali@campus.technion.ac.il',
 'noam.zel@campus.technion.ac.il',
 'eyalmarantz@campus.technion.ac.il',
 'awatef.marie@campus.technion.ac.il',
 'mawada.omar@campus.technion.ac.il',
 'arianna.abis@campus.technion.ac.il',
 'ceciliac@campus.technion.ac.il',
 'guy.wolf@campus.technion.ac.il',
 'yairzick@gmail.com',
 'p.turrini@warwick.ac.uk',
 'perrault.17@osu.edu',
 'argyrios.deligkas@rhul.ac.uk']
