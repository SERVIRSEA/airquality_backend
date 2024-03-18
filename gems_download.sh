
#!/bin/bash
. /home/miniconda/etc/profile.d/conda.sh
conda activate geosdatadownlo

logfile=/home/ubuntu/gems_process/gems_run.log

datapath=/home/ubuntu/data/gems/
scriptpath=/home/ubuntu/gems_process/
cd $scriptpath

echo "-----------------------------------------">> $logfile
echo "Starting download GEMS data">> $logfile

python GEMS_hourlydownload.py

echo "Starting reprojection GEMS NetCDF file">> $logfile

python GEMS_NetCDF_reprojection.py

echo "Completed running" >> $logfile
echo "----------------------------------------------------------------------------" >> $logfile

