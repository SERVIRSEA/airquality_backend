import xarray as xr
import rioxarray as rio
import pandas as pd
from datetime import datetime, timedelta
import os 

def process_netcdf(nc_file):
    try:
        # Open the NetCDF file
        ncfile = xr.open_dataset(nc_file)
    except Exception as e:
        print(f"Failed to open {nc_file}: {e}")
        return
    
    # Extract the variable
    pr = ncfile['DS_BC_DNN_PM25']

    # (Optional) convert longitude from (0-360) to (-180 to 180) (if required)
    pr.coords['lon'] = (pr.coords['lon'] + 180) % 360 - 180
    pr = pr.sortby(pr.lon)

    # Rename the latitude and longitude dimensions if necessary
    pr = pr.rename({'lat': 'latitude', 'lon': 'longitude'})

    # Define lat/long 
    pr = pr.rio.set_spatial_dims('longitude', 'latitude')

    # Check for the CRS
    pr.rio.crs

    # (Optional) If your CRS is not discovered, you should be able to add it like so:
    pr.rio.set_crs("epsg:4326")

    # Iterate over time dimension and export each time step as GeoTIFF
    for i, time in enumerate(pr.time.values):
        timestamp = pd.to_datetime(time).strftime("%Y%m%d_%H%M%S")  # Convert to datetime and format timestamp
        output_filename = f'/home/ubuntu/geoserver_data/aq_data/geos5/geos_{date}_{timestamp}.tif'  # Include timestamp in filename
        # Ensure CRS is set before exporting
        pr.isel(time=i).rio.write_crs("epsg:4326", inplace=True).rio.to_raster(output_filename)


    # Close the NetCDF file
    ncfile.close()

# Thredds NetCDF
THREDDS_OPANDAP='/home/ubuntu/data/geos5km'
# Directory containing the NetCDF files
nc_dir = THREDDS_OPANDAP
# Today's date
today = datetime.now()
# Create a list of dates 30 days before today, formatted as YYYYMMDD
date_array = [(today - timedelta(days=i)).strftime('%Y%m%d') for i in range(2)]

for date in date_array:
    ncfile = os.path.join(THREDDS_OPANDAP, date+'.nc')
    if os.path.isfile(ncfile):
        process_netcdf(ncfile)
    else:
        print('Not found ' + ncfile)

    
