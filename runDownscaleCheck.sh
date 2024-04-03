#!/bin/bash

# Path to the directory with geos data files.
data_path="/home/ubuntu/data/geos5km"
process_path="/home/ubuntu/GEOS5/downscale_process"
script_to_execute="$process_path/downscale.sh"

# Get dates for the last 7 days in YYYYMMDD format.
lastWeek=($(date +"%Y%m%d") $(date -d '-1 day' '+%Y%m%d') $(date -d '-2 day' '+%Y%m%d') \
$(date -d '-3 day' '+%Y%m%d') $(date -d '-4 day' '+%Y%m%d') $(date -d '-5 day' '+%Y%m%d') \
$(date -d '-6 day' '+%Y%m%d'))

# Loop through each date in the last week.
for date in "${lastWeek[@]}"; do
    file_path="$data_path/${date}.nc"
    
    # Check if file does NOT exist for the date.
    if [ ! -f "$file_path" ]; then
        echo "No file for $date, executing script."
        # Execute the script with the corresponding date in YYYY-MM-DD format.
        bash "$script_to_execute" "$(date -d "$date" +'%Y-%m-%d')"
    else
        echo "File for $date exists, skipping."
    fi
done
