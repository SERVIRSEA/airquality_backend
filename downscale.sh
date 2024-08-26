#!/bin/bash
#Download all the forecast files by running the following python script
#. /home/miniconda/etc/profile.d/conda.sh

source /home/ubuntu/anaconda3/bin/activate env_nco

datapath=/home/ubuntu/GEOS5/downscale_process/tempfiles/
scriptpath=/home/ubuntu/GEOS5/downscale_process/

cd $scriptpath
logfile=/home/ubuntu/GEOS5/downscale_process/GEOSDataDownload.log
timestamp=$(date +%Y%m%d%H%M%S)
today=$(date +"%Y%m%d")
echo "-----------------------------------------">> $logfile
echo "Starting script downscale.sh">> $logfile
echo "-----------------------------------------">> $logfile

if [ $# -eq 0 ]
then
      echo "Date is not passed as an argument..proceeding to download today's data" >> $logfile
      python downloadGEOSData.py
else
      python downloadGEOSData.py "$1"
      today=$(date -d "$1" +"%Y%m%d")
      echo "Date is passed as an argument..proceeding to download $today data" >> $logfile
fi
#echo "Working on $today" >> $logfile
#paths to today's 1hour and 3hour .nc files
slv_path=/home/ubuntu/data/geos_tavg1_2d_slv_Nx/$today.nc
aer_path=/home/ubuntu/data/geos_tavg3_2d_aer_Nx/$today.nc
#path to temporarily store intermediate .nc files while processing


if [ -d "$datapath" ]; then
    cd "$datapath"
else
    echo "Directory does not exist: $datapath"
fi

if [ -f final_combined.nc ]
then 
   rm final_combined.nc
fi
if [ -f slv_subset_file.nc ]
then 
   rm slv_subset_file.nc
fi
if [ -f aer_subset_file.nc ]
then 
   rm aer_subset_file.nc
fi

#echo $slv_path
#if slv .nc file exists, get the variables that are required
if [ -f $slv_path ]
then
    ncks -O -v QV10M,Q500,Q850,T10M,T500,T850,U10M,V10M,lat,lon,PS $slv_path slv_subset_file.nc
fi
#if aer .nc file exists, get the variables that are required
#echo $aer_path
if [ -f $aer_path ]
then
    ncks -O -v BCSMASS,DUSMASS25,OCSMASS,SO2SMASS,SO4SMASS,SSSMASS25,TOTEXTTAU,NISMASS25 $aer_path aer_subset_file.nc
#    echo "combine slv and aer .nc files" >> $logfile
    ncks -A aer_subset_file.nc slv_subset_file.nc
#    echo "calculate wind variable" >> $logfile
    ncap2 -s 'WIND=sqrt(U10M*U10M+V10M*V10M)' slv_subset_file.nc final_combined.nc
#    echo "get time array to the final .nc" >> $logfile
    ncap2 -O -s 'timeArray[$time,$lat,$lon]=time' final_combined.nc final_combined.nc
#    echo "get latitude array to the final .nc" >> $logfile
    ncap2 -O -s 'latArray[$time,$lat,$lon]=lat' final_combined.nc final_combined.nc
#    echo "get longitude array to the final .nc" >> $logfile
    ncap2 -O -s 'lonArray[$time,$lat,$lon]=lon' final_combined.nc $today.nc
fi
#echo "Processing $today.nc file..." >> $logfile
#if the final combined .nc file exists, it means the processing and combining was successful, so run the machine learning script using process.py
if [ -f $today.nc ]
then
#  echo "combined file exists, passing argument $today" >> $logfile
  cd $scriptpath
  echo  "--------------------------START DOWNSCALING----------------------------------" >> $logfile

  python downscale.py $today
  if [ $? -eq 0 ]
  then

    echo "Output files should be available in BC and DS directories" >> $logfile
    echo "--------------------------END DOWNSCALING------------------------------------" >> $logfile


  else
     echo "Could not run downscale.py because of errors" >> $logfile
     echo "--------------------------END DOWNSCALING------------------------------------" >> $logfile

  fi
  else
    echo "***Input netCDF file could not be obtained from download script***"
fi
echo "----------------------------------------------------------------------------" >> $logfile
echo "Script completed running" >> $logfile
echo "----------------------------------------------------------------------------" >> $logfile
