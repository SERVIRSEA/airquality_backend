### 
# Author: Beomgeun Jang 
# Usage: reproject GEMS data and clipping with south east asia boundary; python GEMS_NetCDF_reprojection.py
# Modified date: 2024-03-18 
###
import os
import numpy as np
from netCDF4 import Dataset
from pathlib import Path
import rasterio
from rasterio.mask import mask
from scipy.interpolate import NearestNDInterpolator
import fiona
from datetime import datetime
import shutil

start_time = datetime.now()
now_datetime = datetime.utcnow()
yy = now_datetime.year %100
mm = now_datetime.month
dd = now_datetime.day

rootdir = '/home/ubuntu/gems_process/GEMS_process'
region_shp = f'{rootdir}/sea_region/SouthEastAsia_shapefile.shp'
mmdir = f'{rootdir}/L2_NO2/20{yy:02d}/{mm:02d}/{dd:02d}'
outdir = f'/home/ubuntu/data/gems/'

def dec2bin_bitwise(x):
    shp = x.shape
    return np.fliplr((x.ravel()[:,None] & (1 << np.arange(15,-1,-1))) > 0)\
        .astype(np.uint8).reshape((*shp, 16))

for yy in range(24,25):            
    for mm in range(1, 13):
        for dd in range(1, 30):
            for tt in range(0, 7):
                region = ['FC','FW']
                for rg in region:
                    input_file = f'{rootdir}/L2_NO2/20{yy:02d}/{mm:02d}/{dd:02d}/GK2_GEMS_L2_20{yy:02d}{mm:02d}{dd:02d}_{tt:02d}45_NO2_{rg}_DPRO_ORI.nc'
                    output_file = f'{outdir}/GEMS_NO2_20{yy:02d}{mm:02d}{dd:02d}_{tt:02d}45_{rg}_SERVIRSEA10.nc'
  
                    GEMS_datetime = datetime(2000 + yy, mm, dd, tt, 45, 0)
                    # print(GEMS_datetime)

                    if os.path.exists(input_file):
                        print(input_file)
                        nc_file = Dataset(input_file, mode='r')
                        lon = nc_file.groups['Geolocation Fields'].variables['Longitude']
                        fillvalue = lon._FillValue
                        lon = np.array(lon)
                        lon[lon == fillvalue] =  0 #np.nan
                        lat = nc_file.groups['Geolocation Fields'].variables['Latitude']
                        fillvalue = lat._FillValue
                        lat = np.array(lat)
                        lat[lat == fillvalue] = 0 #np.nan
                        time = nc_file.groups['Geolocation Fields'].variables['Time']
                        fillvalue = time._FillValue
                        time = np.array(time)
                        time[time == fillvalue] = 0 #np.nan
                        NO2 = nc_file.groups['Data Fields'].variables['ColumnAmountNO2Trop']
                        fillvalue = NO2._FillValue
                        NO2 = np.array(NO2)
                        NO2[NO2 == fillvalue] = 0 #np.nan

                        Flag = nc_file.groups['Data Fields'].variables['FinalAlgorithmFlags']
                        fillvalue = 0 #Flag._FillValue
                        Flag = np.array(Flag)
                        
                        NO2[(Flag != 0) & (Flag != 1)] =  0 #np.nan

                        NO2_round = NO2 / (6.022*(10**27)) ## molcules/cm2 to mol/m2 conversion

                        interpolatorB2 = NearestNDInterpolator(list(zip(lon.flatten(), lat.flatten())), NO2_round.flatten())
                        rep_lon_1d = np.arange(90.0, 138.0, step=0.08)
                        rep_lat_1d = np.arange(29.0, -5.0, step=-0.02)
                        rep_lon, rep_lat = np.meshgrid(rep_lon_1d, rep_lat_1d)
                        interpolatedB2 = interpolatorB2(rep_lon.flatten(), rep_lat.flatten()).reshape(rep_lon.shape)

                        # plt.figure(figsize=(10,25))
                        # plt.imshow(interpolatedB2, cmap='jet')  # You can change the colormap ('viridis', 'jet', etc.)
                        # plt.colorbar(label='mol/m2')  # Add colorbar with label
                        # plt.title('columnNO2Trop')  # Add title
                        # plt.show()

                        with fiona.open(region_shp, "r") as shapefile:
                            roi = [feature["geometry"] for feature in shapefile]
                        
                        masked_data = np.copy(interpolatedB2)
                        for feature in roi:
                            mask = rasterio.features.geometry_mask([feature], out_shape=masked_data.shape,
                                                                  transform=rasterio.transform.from_origin(rep_lon.min(), rep_lat.max(), 0.08, 0.02),
                                                                  invert=False)
                            masked_data = np.ma.masked_array(masked_data, mask=mask)
                        
                        #### For regional Masking and statistics ####
                        
                        # with fiona.open("bangkok_shapefile.shp", "r") as shapefile:
                        #     Bangkok_shapefile = [feature["geometry"] for feature in shapefile]

                        # Bangkok_masked_data = np.copy(interpolatedB2)
                        # for feature in Bangkok_shapefile:
                        #     mask = rasterio.features.geometry_mask([feature], out_shape=masked_data.shape,
                        #                                           transform=rasterio.transform.from_origin(rep_lon.min(), rep_lat.max(), 0.08, 0.02),
                        #                                           invert=False)
                        #     Bangkok_masked_data = np.ma.masked_array(Bangkok_masked_data, mask=mask)
                            
                        # Bangkok_mean = np.nanmean(Bangkok_masked_data)

                        ####
                        
                        nc_output = Dataset(output_file, 'w', format='NETCDF4')
                        
                        nc_output.createDimension('lon', rep_lon.shape[1])
                        nc_output.createDimension('lat', rep_lat.shape[0])
                        nc_output.createDimension('time', None)

                        nc_lon = nc_output.createVariable('longitude', 'f8', ('lat', 'lon'))
                        nc_lat = nc_output.createVariable('latitude', 'f8', ('lat', 'lon'))
                        nc_NO2 = nc_output.createVariable('ColumnAmountNO2Trop', 'f8', ('time', 'lat', 'lon'))
                        nc_time = nc_output.createVariable('time', 'f8', ('time',))

                        nc_lon.units = 'degree'
                        nc_lat.units = 'degree'
                        nc_NO2.units = 'mol m-2'
                        nc_time.units = f'hours since {GEMS_datetime}'

                        nc_lon[:] = rep_lon
                        nc_lat[:] = rep_lat
                        nc_NO2[0,:,:] = masked_data.filled(fill_value=np.nan)
                        nc_time[0] = GEMS_datetime.timestamp()
                        nc_time.calendar = 'proleptic_gregorian'

                        nc_output.close()

end_time = datetime.now()
print('Duration: {}'.format(end_time - start_time))