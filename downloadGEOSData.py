# Author: Githika Tondapu

#from bs4 import BeautifulSoup
import re
import urllib

import requests
import os.path
import os
import xarray as xr
from pathlib import Path
from datetime import datetime,timedelta
import logging
import json
import os
import sys
import shutil
f = open('downloadGEOSDataParams.json')
config = json.load(f)
if config["logMode"] == "DEBUG":
   logging.basicConfig(level=logging.DEBUG,
                        filename=config["logFile"],
                        format='%(message)s')
if config["logMode"] == "INFO":
   logging.basicConfig(level=logging.INFO,
                        filename=config["logFile"],
                        format='%(message)s')

#get current year, month and day
currentDay = datetime.now().strftime('%d')
currentMonth = datetime.now().strftime('%m')
currentYear = datetime.now().strftime('%Y')
yesterday = datetime.now() - timedelta(days = 1)

if len(sys.argv)==2:
    date_str = sys.argv[1]
    try:
       date_obj = datetime.strptime(date_str, '%Y-%m-%d')
       currentDay = date_obj.strftime('%d')
       currentMonth = date_obj.strftime('%m')
       currentYear = date_obj.strftime('%Y')
       yesterday = date_obj - timedelta(days = 1)
    except:
       print('Please enter date in YYYY-MM-DD format')
       logging.error('Date was not in YYYY-MM-DD format')
       sys.exit()

yDay=yesterday.strftime("%Y%m%d")
datestr=currentYear+currentMonth+currentDay

#bounds to subset the region
lat_bnds, lon_bnds = [5, 40], [59, 110]

def logInfo(message):
    logging.info(str(datetime.now())[:19]+' '+message)

def logDebug(message):
    logging.debug(str(datetime.now())[:19]+' '+message)

def logError(message):
    logging.error(str(datetime.now())[:19]+' '+message)

logInfo(' --------------------------START DOWNLOAD----------------------------------')
logInfo('Downloading data for '+currentYear+'_'+currentMonth+'_'+currentDay)

#all the directories that are required
url = config["url"]+"/Y"+currentYear+"/M"+currentMonth+"/D"+currentDay+"/H00/"

direc3 =config["threeHourDataPath"]+currentYear+'//'+currentMonth+'//'+currentDay
direc1 = config["oneHourDataPath"]+currentYear+'//'+currentMonth+'//'+currentDay
combined1= config["combinedDataPath1hour"]
combined3= config["combinedDataPath3hour"]

#Download all the 3 hour data for 3 days forecast
def download_files(links):
    logInfo('Downloading files from ' + url)

    count=0
    dates1=[]
    dates3=[]
    #GEOS.fp.fcst.tavg1_2d_slv_Nx.20191004_00+20191004_0030.V01.nc4
    logInfo("Starting to download tavg3_2d_aer_Nx and tavg1_2d_slv_Nx data")
    for link in links:
       if 'tavg3_2d_aer_Nx' in link and yDay+'_2230' not in link:
           d1=urllib.parse.unquote(link.split('.')[-3]) #20191004_00+20191004_0030
           d2=d1.split('+')[1]    #20191004_0030
           d3=d2.split('_')       #20191004
           dates1.append(d3[0])
           unique= set(dates1)
           if(len(unique)<=3):

               try:
                   logDebug('Downlaoding '+ link+'...')
                   r = requests.get(url+link,timeout=10)
                   with open(direc3+'/'+str(link), 'wb') as f:
                       f.write(r.content)
                   os.chmod(direc3+'/'+str(link), 0o777)
               except:
                   logError('Error while downloading '+link)
       if ('tavg1_2d_slv_Nx' in link and currentYear+currentMonth+currentDay+'_0030' not in link):
           d1=urllib.parse.unquote(link.split('.')[-3])  #20191004_00+20191004_0030
           d2=d1.split('+')[1]     #20191004_0030
           d3=d2.split('_')        #20191004
           dates3.append(d3[0])
           unique= set(dates3)
           if(len(unique)<=3):
              if count%3==0:
                  try:
                      logDebug('Downloading '+ link+'...')
                      r = requests.get(url+link,timeout=10)
                      with open(direc1+'/'+str(link), 'wb') as f:
                          f.write(r.content)
                      os.chmod(direc1+'/'+str(link), 0o777)
                  except:
                      logError('Error while downloading '+link)
              count=count+1
#Get all the files that are available on https://portal.nccs.nasa.gov/datashare/gmao/geos-fp/forecast/
def find_files():
    logInfo('Getting the links of files available...')
    #link should contain GEOS.fp.fcst
    hrefs = []
    HTML_TAG_REGEX = re.compile(r'<a[^<>]+?href=([\'\"])(.*?)\1', re.IGNORECASE)
    print(url)
    #soup = BeautifulSoup(requests.get(url).text,'html.parser')
    atags=[match[1] for match in HTML_TAG_REGEX.findall(requests.get(url).text)]
    for a in atags:
        try:
            if 'GEOS.fp.fcst' in str(a):
            	hrefs.append(a)
        except Exception as e:
            logError(str(e))
    return hrefs

#Subset the dataset and remove unnecessary fields for 1 hour data
def process_1hour(ds):
    ds = xr.open_dataset(ds['lat'].encoding['source'])
    out = ds.sel(lat=slice(*lat_bnds), lon=slice(*lon_bnds))
    try:
        variables=config["oneHourDropVariables"]
        for field in variables:
            out = out.drop_vars(field)
    except Exception as e:
        logError(str(e))
        logError('Error while processing 1 hour data')
    finally:
        out.close()
        ds.close()
    return out

#Subset the dataset and remove unnecessary fields for 3 hour data
def process_3hour(ds):
    ds = xr.open_dataset(ds['lat'].encoding['source'])
    out = ds.sel(lat=slice(*lat_bnds), lon=slice(*lon_bnds))
    try:
        variables=config["threeHourDropVariables"]
        for field in variables:
            out = out.drop_vars(field)
    except:
        logError('Error while processing 3 hour data')
    finally:
        out.close()
        ds.close()
    return out

#combine data after processing
def combine_data(path_to_data,path_to_combined_file,preprocessing_function):
    logInfo('Combining files from '+path_to_data+' directory')

    input = Path(path_to_data)
    try:
        m_files = [x for x in input.iterdir() if x.is_file()]
        xd =xr.open_mfdataset(sorted(m_files),preprocess=preprocessing_function)
        xd.to_netcdf(path_to_combined_file)
    except Exception as e:
         logError('Error while combining data: '+str(e))

def remove_directory(directory):
    logInfo('Deleting files from '+directory+' directory')
    try:
       shutil.rmtree(directory)
    except:
        logError('Error while deleting directory: ' +directory)

if not os.path.exists(direc3):
    os.makedirs(direc3)
if not os.path.exists(direc1):
    os.makedirs(direc1)
if not os.path.exists(combined1):
    os.makedirs(combined1)
if not os.path.exists(combined3):
    os.makedirs(combined3)

if not os.path.exists(config['dataDownloadPathDS']):
    os.makedirs(config['dataDownloadPathDS'])
if not os.path.exists(config['dataDownloadPathBC']):
    os.makedirs(config['dataDownloadPathBC'])
if not os.path.exists(config['temp_path']):
    os.makedirs(config['temp_path'])

logInfo('Created directories for '+direc3+'---'+direc1+'---'+combined1+'---'+combined3+'---'+config['dataDownloadPathBC']+'---'+config['dataDownloadPathDS']+'---'+config['temp_path'])


list_of_links = find_files()


download_files(list_of_links)


combine_data(direc3,os.path.join(combined3,datestr+'.nc'),process_3hour)


combine_data(direc1,os.path.join(combined1,datestr+'.nc'),process_1hour)


remove_directory(config["oneHourDataPath"])

remove_directory(config["threeHourDataPath"])

remove_directory(config["temp_path"])

logInfo('---------------------------END DOWNLOAD---------------------------------')
