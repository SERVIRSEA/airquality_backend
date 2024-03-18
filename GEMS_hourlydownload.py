### 
# Author: Beomgeun Jang 
# Usage: download hourly GEMS data;  python GEMS_hourlydownload.py
# Modified date: 2024-03-18 
###

import paramiko
import os
from datetime import datetime, timedelta

start_time = datetime.now()

host = '<HOST>'
port = '<PORT>'
username = '<USERNAME>'
password = '<PASSWORD>'

transport = paramiko.Transport((host, port))
transport.connect(username=username, password=password)
sftp = paramiko.SFTPClient.from_transport(transport)

now_datetime = datetime.utcnow()
yy = now_datetime.year %100
mm = now_datetime.month
dd = now_datetime.day

rootdir = '/Users/thannarot/servir/01-airQuality/dev/backend/GEMS_process'
mmdir = f'{rootdir}/L2_NO2/20{yy:02d}/{mm:02d}/{dd:02d}'

if not os.path.exists(mmdir):
    os.makedirs(mmdir)

for tt in range(0,8):
    region = ['FC','FW']
    for rg in region:
        remotepath = f'/L2_NO2/V2.0/20{yy:02d}{mm:02d}/{dd:02d}/GK2_GEMS_L2_20{yy:02d}{mm:02d}{dd:02d}_{tt:02d}45_NO2_{rg}_DPRO_ORI.nc'
        localpath = f'{rootdir}/L2_NO2/20{yy:02d}/{mm:02d}/{dd:02d}/GK2_GEMS_L2_20{yy:02d}{mm:02d}{dd:02d}_{tt:02d}45_NO2_{rg}_DPRO_ORI.nc'
        if os.path.exists(localpath):
            #print(f"{localpath} aready exists")
            continue
        else:
            try:
                sftp.stat(remotepath)
            except IOError:
                #print(f"{remotepath} No such file")
                continue

            sftp.get(remotepath, localpath)
            print(f"{remotepath} downloaded")

end_time = datetime.now()
print('Duration: {}'.format(end_time - start_time))