import xarray as xr
import pandas as pd
import numpy as np
from os import path
import warnings
import glob
from sklearn.externals import joblib
from helper import *
from datetime import datetime,timedelta
import json
import logging
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

warnings.filterwarnings('ignore')
f = open('downloadGEOSDataParams.json')
#load config params
config = json.load(f)
if config["logMode"] == "DEBUG":
   logging.basicConfig(level=logging.DEBUG,
                        filename=config["logFile"],
                        format='%(message)s')
if config["logMode"] == "INFO":
   logging.basicConfig(level=logging.INFO,
                        filename=config["logFile"],
                        format='%(message)s')
def logInfo(message):
    logging.info(str(datetime.now())[:19]+' '+message)

#method that uses machine learning algorithm. Make sure models folder exists with the 10 .pkl files
#this method uses the data frmae that is generated after adding and scaling the variables in the combined file.
def ensemble(dataframe, models_folder_path):
  df_master = dataframe
  index=np.where(np.isnan(df_master['T850'].values))
  print(df_master.max())
  col = ['Lat',	'Lon', 'PS', 'QV10M', 'Q500', 'Q850', 'T10M',	'T500',	'T850',	'WIND',	'BCSMASS',
        'DUSMASS25',	'OCSMASS',	'SO2SMASS',	'SO4SMASS',	'SSSMASS25',	'TOTEXTTAU',	'Date_Time']
  prediction = []
  count =0
  #loop through models
  for m_path in glob.glob('{}/*.pkl'.format(models_folder_path)):
    print('[INFO]  Loading model : ', m_path[len(models_folder_path)+1:])
    print(m_path)
    count += 1
    m = joblib.load(m_path)
    if len(prediction) != 0:
      pred = m.predict(df_master[col])
      prediction = prediction + pred
      df_master[m_path[len(models_folder_path)+1:-4]] = pred
    else:
      prediction = m.predict(df_master[col])
      df_master[m_path[len(models_folder_path)+1:-4]] = prediction
  #Get eman ensemble prediction
  df_master['Ensemble'] = (prediction/10)
  return df_master
logInfo('Process.py triggered')
date_str = sys.argv[1]
date_obj = datetime.strptime(date_str, '%Y%m%d')
datestr = date_obj.strftime('%Y-%m-%d')

#datestr='20191201'
logInfo('Downloading data for '+datestr)



if path.exists('final_combined.nc'):
    logInfo('Combined file available, processing....')
    # Read in to xarray
    forcing=xr.open_dataset('final_combined.nc')
    # Convert to a pandas data frame
    df=forcing.to_dataframe()
    # Create DateTimeIndex for accessing/manipulating the time data.
    dt=pd.DatetimeIndex(df.timeArray)
    # Compute fractional julian day
    jday = dt.dayofyear +  (dt.hour*60.0*60.0 + dt.minute*60.0 + dt.second)/86400.0
    # Scale and store variables in the data frame
    df['Date_Time']=jday
    df['QV10M']=(1000.*df['QV10M'])
    df['Q500']=(1000.*df['Q500'])
    df['Q850']=(1000.*df['Q850'])
    df['Lon']=df['lonArray']
    df['Lat']=df['latArray']
    df['BCSMASS']=(df['BCSMASS']*1000000000.0)
    df['DUSMASS25']=(df['DUSMASS25']*1000000000.0)
    df['OCSMASS']=(df['OCSMASS']*1000000000.0)
    df['SO2SMASS']=(df['SO2SMASS']*1000000000.0)
    df['SO4SMASS']=(df['SO4SMASS']*1000000000.0)
    df['SSSMASS25']=(df['SSSMASS25']*1000000000.0)
    # Get index where values are missing.
    
    index=np.where(np.isnan(df['T850'].values))
    logInfo('Calling machine learning scripts....')

   # Call machine learning code for each prediction
    df_master=ensemble(df.fillna(-9999.0), 'models')
    #prediction[index]=np.nan
    df_master.iloc[index[0],:]=np.nan
    prediction=df_master['Ensemble']
   
    # Now we need to write the data to the netcdf file.
    # "prediciton" should be an array (or data frame with values that are an array) with NX*NY*24 elements
    model_prediction = (prediction.values.reshape(141,164,24).transpose((2,0,1)))
    print(model_prediction)
    model1_prediction = df_master['model_1'].values.reshape(141,164,24).transpose((2,0,1))
    model2_prediction = df_master['model_2'].values.reshape(141,164,24).transpose((2,0,1))
    model3_prediction = df_master['model_3'].values.reshape(141,164,24).transpose((2,0,1))
    model4_prediction = df_master['model_4'].values.reshape(141,164,24).transpose((2,0,1))
    model5_prediction = df_master['model_5'].values.reshape(141,164,24).transpose((2,0,1))
    model6_prediction = df_master['model_6'].values.reshape(141,164,24).transpose((2,0,1))
    model7_prediction = df_master['model_7'].values.reshape(141,164,24).transpose((2,0,1))
    model8_prediction = df_master['model_8'].values.reshape(141,164,24).transpose((2,0,1))
    model9_prediction = df_master['model_9'].values.reshape(141,164,24).transpose((2,0,1))
    model10_prediction = df_master['model_10'].values.reshape(141,164,24).transpose((2,0,1))
    logInfo('Reshaping....')

    # Put this data back into the xarray dataset since all the coordinates are already defined there.
    forcing['PM25']=xr.DataArray((np.where(model_prediction< 40, (model_prediction-2.5+(0.11 * model_prediction)), (model_prediction-2.5+(0.20 * model_prediction)))),dims=("time","lat","lon"))
    forcing['model_1']=xr.DataArray(model1_prediction,dims=("time","lat","lon"))
    forcing['model_2']=xr.DataArray(model2_prediction,dims=("time","lat","lon"))
    forcing['model_3']=xr.DataArray(model3_prediction,dims=("time","lat","lon"))
    forcing['model_4']=xr.DataArray(model4_prediction,dims=("time","lat","lon"))
    forcing['model_5']=xr.DataArray(model5_prediction,dims=("time","lat","lon"))
    forcing['model_6']=xr.DataArray(model6_prediction,dims=("time","lat","lon"))
    forcing['model_7']=xr.DataArray(model7_prediction,dims=("time","lat","lon"))
    forcing['model_8']=xr.DataArray(model8_prediction,dims=("time","lat","lon"))
    forcing['model_9']=xr.DataArray(model9_prediction,dims=("time","lat","lon"))
    forcing['model_10']=xr.DataArray(model10_prediction,dims=("time","lat","lon"))
    #forcing['BC_MLPM25']=(forcing['PM25']-2.5+(0.11 * forcing['PM25']))
    forcing['BC_MLPM25']=(forcing['PM25'])
    forcing['BCSMASS']=(forcing['BCSMASS']*1000000000.0)
    forcing['DUSMASS25']=(forcing['DUSMASS25']*1000000000.0)
    forcing['OCSMASS']=(forcing['OCSMASS']*1000000000.0)
    forcing['SO2SMASS']=(forcing['SO2SMASS']*1000000000.0)
    forcing['SO4SMASS']=(forcing['SO4SMASS']*1000000000.0)
    forcing['SSSMASS25']=(forcing['SSSMASS25']*1000000000.0)
    forcing['GEOSPM25']=(1.375*forcing['SO4SMASS']+1.8*forcing['OCSMASS']+forcing['BCSMASS']+forcing['DUSMASS25']+forcing['SSSMASS25'])
    logInfo('Added data to final netcdf....')

    # Add metadata to variable, you may do it here.    
    forcing['PM25'].attrs = { 'long_name':'air_quality_index_pm25','units':'my_units','description':'ensemble ML model' }
    # Now write this data to file.
    logInfo("Place netCDF in the GEOS folder if it exists....")

    if not os.path.exists(config['dataDownloadPath']):
       os.makedirs(config['dataDownloadPath'])
    forcing_df=forcing.to_dataframe()
    forcing_xr=forcing_df.to_xarray()
    forcing_xr['PM25'].attrs = { 'long_name':'PM2.5','units':'\u03BCg/m\u00b3','description':'ML model PM2.5' }
    forcing_xr['BC_MLPM25'].attrs = { 'long_name':'BC_ML_PM2.5','units':'\u03BCg/m\u00b3','description':'Bias corrected ML model PM2.5' }
    forcing_xr['GEOSPM25'].attrs = { 'long_name':'GEOS PM2.5','units':'\u03BCg/m\u00b3','description':'GEOS PM2.5' }
    forcing_xr['WIND'].attrs = { 'long_name':'WIND','units':'m/s','description':'WIND' }
    forcing_xr['T10M'].attrs = { 'long_name':'T10M','units':'kelvin','description':'T10M' }
    forcing_xr['SSSMASS25'].attrs = { 'long_name':'SSSMASS25','units':'\u03BCg/m\u00b3','description':'SSSMASS25' }
    forcing_xr['SO4SMASS'].attrs = { 'long_name':'SO4SMASS','units':'\u03BCg/m\u00b3','description':'SO4SMASS' }
    forcing_xr['SO2SMASS'].attrs = { 'long_name':'SO2SMASS','units':'\u03BCg/m\u00b3','description':'SO2SMASS' }
    forcing_xr['DUSMASS25'].attrs = { 'long_name':'DUSMASS25','units':'\u03BCg/m\u00b3','description':'DUSMASS25' }
    forcing_xr['TOTEXTTAU'].attrs = { 'long_name':'TOTEXTTAU','units':'\u03BCg/m\u00b3','description':'TOTEXTTAU' }
    forcing_xr['BCSMASS'].attrs = { 'long_name':'BCSMASS','units':'\u03BCg/m\u00b3','description':'BCSMASS' }
    forcing_xr.to_netcdf(path=config['dataDownloadPath']+date_str+'.nc')
    downscale(forcing_xr)
    os.chmod(config['dataDownloadPath']+date_str+'.nc',0o777)
    logInfo("Delete unnecessary directories")

    if os.path.exists('slv_subset_file.nc'):
        os.remove('slv_subset_file.nc')
    if os.path.exists('aer_subset_file.nc'):
        os.remove('aer_subset_file.nc')
    if os.path.exists('final_combined.nc'):
        os.remove('final_combined.nc')
else:
    logInfo("Combined file does not exist, cannot process data for "+datestr+".")
    print("Combined file does not exist, cannot process data for "+datestr+".")