from enum import Enum

USERNAME = None
PASSWORD = None

DF_PATH = r'.\backup.pkl'
FORBIDDEN_CODE = 403

NUMBER_REVIEWERS = 4
NUMBER_PAPERS = 8
REQUIRED_BIDS = 1

BID_EXTRACTION_INTERVAL = 10  # Seconds
IPRICE_UPDATE_INTERVAL = 10  # Seconds
DF_BACKUP_INTERVAL = 60 * 60  # 1 Hours
DF_BACKUP_PATH = 'bids_backup.pkl'

REQUIRED_POINTS = 2000

SAVE_BIDS = False
SAVE_IPRICES = False

class Bids(Enum):
    PINCH = '3'
    WILLING = '4'
    EAGER = '5'