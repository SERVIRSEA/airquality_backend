# -*- coding: utf-8 -*-
"""
Created on Tue Oct 10 08:54:54 2023

@author: asayeed

Updated by Githika Tondapu on Oct 03, 2024
"""
from datetime import datetime
from os import path
import json
import numpy as np
import warnings
import os, sys
import matplotlib.pyplot as plt
import matplotlib as mpl
import keras as k
import keras.losses
import cartopy.crs as ccrs
import xarray as xr
import pandas as pd
from copy import deepcopy as dc
import cartopy.feature as cfeature
import time
import logging
import shutil

logging.getLogger("tensorflow").setLevel(logging.ERROR)
warnings.filterwarnings('ignore')
pd.set_option('display.float_format', lambda x: '%.5f' % x)

f = open('downloadGEOSDataParams.json')
# load config params
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

def logDebug(message):
    logging.debug(str(datetime.now())[:19]+' '+message)

def logError(message):
    logging.error(str(datetime.now())[:19]+' '+message)

def remove_directory(directory):
    logInfo('Deleting files from '+directory+' directory')
    try:
        shutil.rmtree(directory)
    except:
        logError('Error while deleting directory: ' +directory)



date_str = sys.argv[1]
date_obj = datetime.strptime(date_str, '%Y%m%d')
datestr = date_obj.strftime('%Y-%m-%d')


### Function to calculate Index of Agrrement
def IOA(o, p):
    ia = 1 - (np.sum((o - p) ** 2)) / (np.sum((np.abs(p - np.mean(o)) + np.abs(o - np.mean(o))) ** 2))
    return ia


# %%
### Customized loss defined using index of agreement
def customLoss1(o, p):
    ioa = 1 - (k.sum((o - p) ** 2)) / (k.sum((k.abs(p - k.mean(o)) + k.abs(o - k.mean(o))) ** 2))
    return (-ioa)


keras.losses.customLoss1 = customLoss1


# %%
### Function to normlize each column between 0&1
def normalize(DF, mx, mn):
    range1 = (mx.values - mn.values)
    d = pd.DataFrame(((DF.values - mn.values) / range1), columns=DF.columns, index=DF.index)
    return d


# %%

def bias_correction(fn):
    ds = xr.open_dataset(fn).sel(lon=slice(91.8,141.6), lat=slice(-11.25,28.5))
    df = ds.to_dataframe().reset_index()
    df['BCSMASS'] = (df['BCSMASS'] * 1000000000.0)
    df['DUSMASS25'] = (df['DUSMASS25'] * 1000000000.0)
    df['OCSMASS'] = (df['OCSMASS'] * 1000000000.0)
    df['SO2SMASS'] = (df['SO2SMASS'] * 1000000000.0)
    df['SO4SMASS'] = (df['SO4SMASS'] * 1000000000.0)
    df['SSSMASS25'] = (df['SSSMASS25'] * 1000000000.0)
    df['NISMASS25'] = df['NISMASS25']*1e9
    df['GEOSPM25'] = df.DUSMASS25 + df.SSSMASS25 + df.NISMASS25 + df.BCSMASS + (df.OCSMASS * 1.6) + (df.SO4SMASS * 1.375)
    date1 = (pd.to_datetime(fn[-11:-3]) + pd.Timedelta(0, unit='D')).strftime('%Y%m%d')
    date2 = (pd.to_datetime(fn[-11:-3]) + pd.Timedelta(1, unit='D')).strftime('%Y%m%d')
    date3 = (pd.to_datetime(fn[-11:-3]) + pd.Timedelta(2, unit='D')).strftime('%Y%m%d')
    df["Date"] = df['time'].dt.strftime('%Y%m%d')
    df1 = df[df.Date == date1]
    df2 = df[df.Date == date2]
    df3 = df[df.Date == date3]

    for fold in range(10):

        model1 = keras.models.load_model(model_path + "v1_4_dnn_bias_Correction_day1_fold" + str(fold).zfill(2) + ".h5",
                                         custom_objects={'customLoss1': customLoss1})
        
        temp = normalize(df1[feature_columns], mx.T[feature_columns], mn.T[feature_columns])
        temp[temp < 0] = np.nan

    
        df1["DNN_" + str(fold).zfill(2)] = model1.predict(temp,
                                                          steps=2,
                                                          # batch_size=1024,
                                                          verbose=0)
        model2 = keras.models.load_model(model_path + "v1_4_dnn_bias_Correction_day2_fold" + str(fold).zfill(2) + ".h5",
                                         custom_objects={'customLoss1': customLoss1})
        temp = normalize(df2[feature_columns], mx.T[feature_columns], mn.T[feature_columns])
        temp[temp < 0] = np.nan
        df2["DNN_" + str(fold).zfill(2)] = model2.predict(temp, steps=2,
                                                          # batch_size=1024,
                                                          verbose=0)

        temp = normalize(df3[feature_columns], mx.T[feature_columns], mn.T[feature_columns])
        temp[temp < 0] = np.nan
        model3 = keras.models.load_model(model_path + "v1_4_dnn_bias_Correction_day3_fold" + str(fold).zfill(2) + ".h5",
                                         custom_objects={'customLoss1': customLoss1})
        df3["DNN_" + str(fold).zfill(2)] = model3.predict(temp, steps=2,
                                                          # batch_size=1024,
                                                          verbose=0)
        

    model1 = keras.models.load_model(model_path + "v1_4_day1_dnn_bias_Correction_ensemble.h5",
                                     custom_objects={'customLoss1': customLoss1})
    temp = normalize(df1[feature_columns2], mx.T[feature_columns2], mn.T[feature_columns2])
    temp[temp < 0] = np.nan
    df1["BC_DNN_PM25"] = model1.predict(temp, steps=2,
                                        # batch_size=1024,
                                        verbose=0)

    model2 = keras.models.load_model(model_path + "v1_4_day2_dnn_bias_Correction_ensemble.h5",
                                     custom_objects={'customLoss1': customLoss1})
    temp = normalize(df2[feature_columns2], mx.T[feature_columns2], mn.T[feature_columns2])
    temp[temp < 0] = np.nan
    df2["BC_DNN_PM25"] = model2.predict(temp, steps=2,
                                        # batch_size=1024,
                                        verbose=0)

   
    model3 = keras.models.load_model(model_path + "v1_4_day3_dnn_bias_Correction_ensemble.h5",
                                     custom_objects={'customLoss1': customLoss1})
    temp = normalize(df3[feature_columns2], mx.T[feature_columns2], mn.T[feature_columns2])
    temp[temp < 0] = np.nan
    df3["BC_DNN_PM25"] = model3.predict(temp, steps=2,
                                        # batch_size=1024,
                                        verbose=0)
    df = pd.concat((df1, df2, df3), axis=0)[out_cols]

    out_df = df.set_index(['lat', 'lon', 'time'])
    out_xarray = xr.Dataset.from_dataframe(out_df)

    out_xarray = out_xarray.astype("float32")
    out_xarray.to_netcdf(out_bc_path + outfn_bc, mode='w', format='NETCDF4',
                         encoding={'lat': {"_FillValue": None, 'zlib': True, 'dtype': 'float32'},
                                   'lon': {"_FillValue": None, 'zlib': True, 'dtype': 'float32'},
                                   'time': {"_FillValue": None, 'zlib': True, 'dtype': 'float32'},
                                   'GEOSPM25': {"_FillValue": -999, 'zlib': True, 'dtype': 'float32'},
                                   # 'BC_MLPM25':{"_FillValue":-999,'zlib': True,'dtype':'float32'},
                                   'BC_DNN_PM25': {"_FillValue": -999, 'zlib': True, 'dtype': 'float32'}})
    return out_xarray


def downscale(ds):
    model = keras.models.load_model(model_path + "model_downscale_v1.h5", custom_objects={'customLoss1': customLoss1})
    lat = np.arange((ds.lat.min() - 0.1), (ds.lat.max() + 0.15), 0.05)
    lon = np.arange((ds.lon.min() - 0.125), (ds.lon.max() + 0.1875), 0.0625)
    # ds=ds
    pm25 = ds.variables['GEOSPM25'].values
    pm25 = np.moveaxis(pm25, -1, 0)
    testX = dc(pm25)
    geos = model.predict(testX, steps=1, verbose=0)[:, :, :, 0]
    geos = np.moveaxis(geos, 0, -1)

    pm25 = ds.variables['BC_DNN_PM25'].values
    pm25 = np.moveaxis(pm25, -1, 0)
    testX = dc(pm25)
    dnn = model.predict(testX, steps=1, verbose=0)[:, :, :, 0]
    dnn = np.moveaxis(dnn, 0, -1)

    out_ds = xr.Dataset(
        data_vars=dict(
            DS_GEOSPM25=(["lat", "lon", "time"], geos),
            DS_BC_DNN_PM25=(["lat", "lon", "time"], dnn),
        ),
        coords=dict(
            lon=(["lon"], lon),
            lat=(["lat"], lat),
            time=ds['time'],
        ),
        attrs=dict(description="Downscaled PM2.5"),
    )
    out_ds.to_netcdf(out_ds_path + outfn_ds, mode='w', format='NETCDF4',
                     encoding={'lat': {"_FillValue": None, 'zlib': True, 'dtype': 'float32'},
                               'lon': {"_FillValue": None, 'zlib': True, 'dtype': 'float32'},
                               'time': {"_FillValue": None, 'zlib': True, 'dtype': 'float32'},
                               'DS_GEOSPM25': {"_FillValue": -999, 'zlib': True, 'dtype': 'float32'},
                               'DS_BC_DNN_PM25': {"_FillValue": -999, 'zlib': True, 'dtype': 'float32'}})

    return out_ds


def PLOT_DS(ds, out_ds):
    lat25 = ds.lat.values
    lon25 = ds.lon.values
    lat5 = out_ds.lat.values
    lon5 = out_ds.lon.values
    for i in range(24):
        geos25 = ds['GEOSPM25'].values[:, :, i]
        dnn25 = ds['BC_DNN_PM25'].values[:, :, i]
        geos5 = out_ds['DS_GEOSPM25'].values[:, :, i]
        dnn5 = out_ds['DS_BC_DNN_PM25'].values[:, :, i]

        indt = pd.to_datetime(ds.time[0].values).strftime("%Y-%m-%d %H:%M")
        date = pd.to_datetime(ds.time[i].values).strftime("%Y-%m-%d %H:%M")
        fname = pd.to_datetime(ds.time[i].values).strftime("%Y%m%d_%H%M")

        if i < 8:
            plot_path = plots + "/Day1/"
        elif i >= 16:
            plot_path = plots + "/Day3/"
        else:
            plot_path = plots + "/Day2/"

        # date2 = pd.to_datetime(ds.time[i].values)

        # create image
        fig, axs = plt.subplots(2, 2, figsize=(40, 50), subplot_kw={'projection': projection}, frameon=True)
        fig.suptitle("Initialization Date:" + indt + "\n" +
                     "Forecast Date:" + date,
                     fontsize=60, fontweight='bold', y=.94)

        ax = axs[0, 0]
        # ax.set_extent([94, 108.5, 4, 26],crs=ccrs.PlateCarree())

        cm = ax.pcolor(lon25, lat25, geos25,
                       cmap=cmap,
                       # vmin=0, vmax=200,
                       transform=ccrs.PlateCarree(),
                       norm=norm,
                       # levels=cbarticks,
                       # plotnonfinite=False
                       )

        ax.coastlines(resolution='50m')
        states_provinces = cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines',
            scale='50m',
            facecolor='none')
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS)
        ax.add_feature(states_provinces)

        ax.set_title('GEOS 25km', fontsize=50, fontweight="bold")

        ax = axs[0, 1]
        # ax.set_extent([94, 108.5, 4, 26],crs=ccrs.PlateCarree())

        cm = ax.pcolor(lon25, lat25, dnn25,
                       cmap=cmap,
                       # vmin=0, vmax=200,
                       transform=ccrs.PlateCarree(),
                       norm=norm,
                       # levels=cbarticks,
                       # plotnonfinite=False
                       )

        ax.coastlines(resolution='50m')
        states_provinces = cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines',
            scale='50m',
            facecolor='none')
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS)
        ax.add_feature(states_provinces)

        ax.set_title('Bias Corrected 25km', fontsize=50, fontweight="bold")

        ax = axs[1, 0]
        # ax.set_extent([94, 108.5, 4, 26],crs=ccrs.PlateCarree())

        cm = ax.pcolor(lon5, lat5, geos5,
                       cmap=cmap,
                       # vmin=0, vmax=200,
                       transform=ccrs.PlateCarree(),
                       norm=norm,
                       # levels=cbarticks,
                       # plotnonfinite=False
                       )

        ax.coastlines(resolution='50m')
        states_provinces = cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines',
            scale='50m',
            facecolor='none')
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS)
        ax.add_feature(states_provinces)

        ax.set_title('GEOS 5km', fontsize=50, fontweight="bold")
        # cax = fig.add_axes([ax.get_position().x1+0.002,ax.get_position().y0,0.01,ax.get_position().height])
        # plt.colorbar(cm, cax=cax, ticks=cbarticks)#,extend='max')

        ax = axs[1, 1]
        # ax.set_extent([94, 108.5, 4, 26],crs=ccrs.PlateCarree())
        cm = ax.pcolor(lon5, lat5, dnn5,
                       cmap=cmap,
                       transform=ccrs.PlateCarree(),
                       norm=norm,
                       # levels=cbarticks,
                       # plotnonfinite=False
                       )

        ax.coastlines(resolution='50m')
        states_provinces = cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines',
            scale='50m',
            facecolor='none')
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS)
        ax.add_feature(states_provinces)

        ax.set_title('Bias Corrected 5 km', fontsize=50, fontweight="bold")
        plt.subplots_adjust(
            # left=0.1,
            # bottom=0.1,
            # right=0.9,
            # top=0.9,
            wspace=0.0,
            hspace=0.1)
        cax = fig.add_axes([ax.get_position().x1 + 0.01, ax.get_position().y0, 0.01, ax.get_position().height * 2.1])
        plt.colorbar(cm, cax=cax, ticks=cbarticks)  # ,extend='max')
        plt.savefig(plot_path + "v12_" + fname + ".png", bbox_inches='tight')
        fig.clear()
        plt.clf()


# %%
# Color Pallet for plots

plt.rcParams.update({'font.size': 50})
projection = ccrs.PlateCarree()
cbarticks = list(np.arange(0, 151, 10)) + [200, 500, 1000]
cmap = plt.cm.jet
cmaplist = [cmap(i) for i in range(cmap.N)][50:]
cmap = mpl.colors.LinearSegmentedColormap.from_list(
    'Custom cmap', cmaplist, cmap.N)

# define the bins and normalize
norm = mpl.colors.BoundaryNorm(cbarticks, cmap.N)

# %%

###
## Repalce wd with your working directory

wd = config['directory_path']
# in_files_path = wd + "\IN_NetCDF\\"
scalar_path = wd + '/Scalars//'
out_bc_path = config['dataDownloadPathBC']
out_ds_path = config['dataDownloadPathDS']
model_path = wd + "//Model//"
plots = wd + "//PLOTS//"

# flist = sorted(glob.glob(in_files_path + "*.nc"))
lst = []

# %% Global PArameters of Bias Corrections
feature_columns = ['WIND', 'PS', 'Q500',
                   'QV10M', 'T10M', 'T500',
                   'U10M', 'V10M', 'BCSMASS',
                   'DUSMASS25', 'OCSMASS', 'SO2SMASS',
                   'SO4SMASS', 'SSSMASS25', 'TOTEXTTAU']

cols = ['DNN_00', 'DNN_01', 'DNN_02', 'DNN_03', 'DNN_04', 'DNN_05', 'DNN_06', 'DNN_07', 'DNN_08', 'DNN_09']
feature_columns2 = feature_columns + cols

mx_mn = pd.read_csv(scalar_path + 'max_min4.csv', index_col=0).T
mx_mn.loc['mx', cols] = 1000.0
mx_mn.loc['mn', cols] = 0.0
mx = mx_mn.loc['mx', :]
mn = mx_mn.loc['mn', :]

out_cols = ['lat', 'lon', 'time', 'lonArray', 'latArray', 'timeArray', 'GEOSPM25', 'BC_DNN_PM25']

PLOT = False

print(config['temp_path']+ date_obj.strftime('%Y%m%d') + '.nc')

if path.exists(config['temp_path']+ date_obj.strftime('%Y%m%d') + '.nc'):
    fn = str(date_obj.strftime('%Y%m%d') + '.nc')
    outfn_bc = "v1_4_BC_"+fn[-11:]
    outfn_ds = "v1_4_DS_"+fn[-11:]
    date = fn[-11:-3]

    if not os.path.exists(out_ds_path + outfn_ds):
        try:
            t1 = time.time()
            ds = bias_correction(config['temp_path']+fn)
            out_ds = downscale(ds)
            if PLOT:
                PLOT_DS(ds, out_ds)
            print(date, " Processing time:", (time.time() - t1), " secs")
            logInfo(" Processing time: "+str(time.time() - t1)+" secs")

            if(os.path.exists(out_ds_path + outfn_ds)):
                remove_directory(config["oneHourDataPath"])
                remove_directory(config["threeHourDataPath"])
                remove_directory(config["temp_path"])

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, "Error at line: ", exc_tb.tb_lineno)
            logInfo("Processing time: "+ str(time.time() - t1)+ " secs")
