# Configuration file. Basic configuration variables.
"""
DATA_DIR: local directory on the server, containing writable sub-folders for each Parameter to hold the combined/combined.nc files
These files are written when a chart is generated for a specific point or polygon.
For a DATA_DIR base named /srv/aqx, with the parameters fire, aod_terra and aod_aqua, the following files should exist:
  /srv/aqx/fire/combined/combined.nc
  /srv/aqx/aod_aqua/combined/combined.nc
  /srv/aqx/aod_terra/combined/combined.nc
"""
"""
  Import thredds configurations - CATALOG, WMS URL PATH, POSTGRESQL define in settings
"""
from django.conf import settings

DATA_DIR = 'static/aq_dir/'

LOG_DIR = 'static/log/'

"""
THREDDS_CATALOG: Indicates the base URL for the directory containing the different Parameters
  This is a publicly accessible THREDDS server (not necessarily residing in the same server or even on the same network)
"""

THREDDS_CATALOG = settings.THREDDS_CATALOG

THREDDS_OPANDAP = settings.THREDDS_OPANDAP

"""
THREDDS_wms: Indicates the basic form of WMS requests to the server
  This is a publicly accessible THREDDS server (not necessarily residing in the same server or even on the same network)
"""

THREDDS_wms = settings
connection = [{'host': settings.POSTGRES_HOST},
              {'user': settings.POSTGRES_USER},
              {'password': settings.POSTGRES_PASS},
              {'dbname': settings.POSTGRES_DB}]

HDF5_USE_FILE_LOCKING=False