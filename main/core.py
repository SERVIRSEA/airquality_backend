import glob
import os
import requests
import re
import shapely.geometry
import shapely
import netCDF4
import time
import json
import calendar
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from collections import defaultdict
from PIL import Image
import numpy as np
from django.http import HttpResponse
from shapely.geometry import shape, Polygon
import logging
from datetime import datetime, timedelta
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from django.conf import settings
import xarray as xr
from django.db import connections
from django.views.decorators.csrf import csrf_exempt
from geopy.distance import great_circle
from geopy.distance import geodesic
from itertools import *
from main.config import DATA_DIR, LOG_DIR

THREDDS_CATALOG = settings.THREDDS_CATALOG
THREDDS_OPANDAP = settings.THREDDS_OPANDAP
THREDDS_wms = settings.THREDDS_WMS_URL

def generate_variables_meta():
    """Generate Variables Metadata from the Var Info text"""
    db_file = os.path.join(settings.BASE_DIR, 'static/data/var_info.txt')
    variable_list = []
    with open(db_file, mode='r') as f:
        f.readline()  # Skip first line

        lines = f.readlines()

    for line in lines:
        if line != '':
            line = line.strip()
            linevals = line.split('|')
            variable_id = linevals[0]
            category = linevals[1]
            display_name = linevals[2]
            units = linevals[3]
            vmin = linevals[4]
            vmax = linevals[5]

            try:
                variable_list.append({
                    'id': variable_id,
                    'category': category,
                    'display_name': display_name,
                    'units': units,
                    'min': vmin,
                    'max': vmax,
                })
            except Exception:
                continue
    return variable_list


def gen_thredds_options():
    """Generate THREDDS options for the dropdowns"""
    catalog_url = THREDDS_CATALOG

    catalog_wms = THREDDS_wms
    tinf = defaultdict()
    json_obj = {}


    if catalog_url[-1] != "/":
        catalog_url = catalog_url + '/'

    if catalog_wms[-1] != "/":
        catalog_wms = catalog_wms + '/'
    catalog_xml_url = catalog_url + 'catalog.xml'
    cat_response = requests.get(catalog_xml_url, verify=False)
    cat_tree = ET.fromstring(cat_response.content)
    currentDay = datetime.now().strftime('%d')
    currentMonth = datetime.now().strftime('%m')
    currentYear = datetime.now().strftime('%Y')
    d=currentYear+currentMonth+currentDay
    for elem in cat_tree.iter():
        for k, v in elem.attrib.items():
            if 'title' in k and ("geos" in v or "fire" in v or "aod" in v):
                run_xml_url = catalog_url + str(v) +'/catalog.xml'
                run_response = requests.get(run_xml_url, verify=False)
                run_tree = ET.fromstring(run_response.content)
                for ele in run_tree.iter():
                    for ke, va in ele.attrib.items():
                        if 'urlPath' in ke:
                            if va.endswith('.nc') and d in va  and "geos" in va:
                                tinf.setdefault(v, {}).setdefault('3daytoday', []).append(va)
                                tinf.setdefault(v, {}).setdefault('3dayrecent', []).append(va)
                            elif va.endswith('.nc') and d not in va and "geos" in va:
                                tinf.setdefault(v, {}).setdefault('3dayrecent', []).append(va)
                            elif va.endswith('.nc') and "geos" not in va:
                                tinf.setdefault(v, {}).setdefault('monthly', []).append(va)
                        if 'title' in ke and ("combined" in va):
                            mo_xml_url = catalog_url + str(v) + '/'+str(va)+'/catalog.xml'
                            mo_response = requests.get(mo_xml_url, verify=False)
                            mo_tree = ET.fromstring(mo_response.content)
                            for el in mo_tree.iter():
                                for key, val in el.attrib.items():
                                    if 'urlPath' in key:
                                        tinf.setdefault(v, {}).setdefault(va, []).append(val)
    json_obj['catalog'] = tinf
    return json_obj

def get_styles():
    """Returns a list of style tuples"""
    date_obj = {}

    color_opts = [
        {'Rainbow': 'rainbow'},
        {'TMP 1': 'tmp_2maboveground'},
        {'TMP 2': 'dpt_2maboveground'},
        {'SST-36': 'sst_36'},
        {'Greyscale': 'greyscale'},

        {'OCCAM': 'occam'},
        {'OCCAM Pastel': 'occam_pastel-30'},
        {'Red-Blue': 'redblue'},
        {'NetCDF Viewer': 'ncview'},
        {'ALG': 'alg'},
        {'ALG 2': 'alg2'},
        {'Ferret': 'ferret'},
        {'Reflectivity': 'enspmm-refc'},
        {'PM25': 'pm25'},
        {'Browse Color Scale': 'browse'},
        # ('Probability', 'prob'),
        # ('White-Blue', whiteblue'),
        # ('Grace', 'grace'),
    ]

    date_obj = color_opts

    return color_opts

def get_time(freq, run_type, run_date):
    # Empty list to store the timeseries values
    ts = []
    json_obj = {}

    try:
        # Make sure you have this path for all the run_types (/home/tethys/aq_dir/fire/combined/combined.nc)
        # infile = os.path.join(DATA_DIR, run_type, run_date)
        infile = os.path.join(THREDDS_OPANDAP, run_type, run_date)
        nc_fid = netCDF4.Dataset(infile, 'r')  # Reading the netCDF file
        lis_var = nc_fid.variables
        time = nc_fid.variables['time'][:]

        for timestep, v in enumerate(time):
            dt_str = netCDF4.num2date(lis_var['time'][timestep], units=lis_var['time'].units,
                                      calendar=lis_var['time'].calendar)

            dt_str = datetime.strptime(dt_str.isoformat(), "%Y-%m-%dT%H:%M:%S")

            time_stamp = calendar.timegm(dt_str.utctimetuple()) * 1000
            ts.append(datetime.strftime(dt_str, '%Y-%m-%dT%H:%M:%SZ'))

        ts.sort()
        json_obj["status"] = 'Success'
        json_obj["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        json_obj["message"] = 'Data retrieval successful'
        json_obj["data"] = {"times": ts}

    except Exception as e:
        json_obj["status"] = 'Error'
        json_obj["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        json_obj["message"] = f'Error: {str(e)}'
        json_obj["data"] = {"times": []}

    return json_obj

def get_pt_values(s_var, geom_data, freq, run_type, run_date):
    """Helper function to generate time series for a point"""
    # logger.info("PARAMETERS : ['" + s_var + "','" + geom_data + "','" + freq + "','" + run_type + "','" + run_date+"']")
    # Empty list to store the timeseries values
    ts_plot = []
    ts_plot_pm25 = []
    ts_plot_bcpm25 = []
    ts_plot_geospm25 = []
    s_var1 = 'PM25'
    s_var2 = 'DS_BC_DNN_PM25'
    s_var3 = 'GEOSPM25'
    
    json_obj = {}
    
    # Defining the lat and lon from the coords string
    coords = geom_data.split(',')
    stn_lat = float(coords[1])
    stn_lon = float(coords[0])
    st_point=(stn_lat,stn_lon)

    try:
        if run_type == "geos" or run_type == "geos5km" or run_type == "vfei":
            """access netcdf file via Thredds server OPANDAP"""
            infile = THREDDS_OPANDAP+run_type+"/"+ run_date
        else:
            """Make sure you have this path for all the run_types(/home/tethys/aq_dir/fire/combined/combined.nc)"""
            infile = os.path.join(DATA_DIR, run_type, freq, run_date)
        nc_fid = netCDF4.Dataset(infile, 'r',)  # Reading the netCDF file
        lis_var = nc_fid.variables
        

        if run_type == "geos" and "PM25" in s_var:
            field = nc_fid.variables[s_var][:]
            lats = nc_fid.variables['lat'][:]
            lons = nc_fid.variables['lon'][:]  # Defining the longitude array
            time = nc_fid.variables['time'][:]
            abslat = np.abs(lats - stn_lat)  # Finding the absolute latitude
            abslon = np.abs(lons - stn_lon)  # Finding the absolute longitude
            lat_idx = (abslat.argmin())
            lon_idx = (abslon.argmin())
            for timestep, v in enumerate(time):
                val = field[lat_idx, lon_idx][timestep]
                if np.isnan(val) == False:
                    dt_str = netCDF4.num2date(lis_var['time'][timestep], units=lis_var['time'].units,
                                              calendar=lis_var['time'].calendar)
                    dtt = dt_str.strftime('%Y-%m-%dT%H:%M:%SZ')
                    dt = datetime.strptime(dtt, '%Y-%m-%dT%H:%M:%SZ')
                    time_stamp = calendar.timegm(dt.utctimetuple()) * 1000
                    ts_plot.append([time_stamp, round(float(val))])
            field1 = nc_fid.variables[s_var1][:]
            lats = nc_fid.variables['lat'][:]
            lons = nc_fid.variables['lon'][:]  # Defining the longitude array
            time = nc_fid.variables['time'][:]
            abslat = np.abs(lats - stn_lat)  # Finding the absolute latitude
            abslon = np.abs(lons - stn_lon)  # Finding the absolute longitude
            lat_idx = (abslat.argmin())
            lon_idx = (abslon.argmin())
            for timestep, v in enumerate(time):

                val = field1[lat_idx, lon_idx][timestep]
                if np.isnan(val) == False:
                    dt_str = netCDF4.num2date(lis_var['time'][timestep], units=lis_var['time'].units,
                                              calendar=lis_var['time'].calendar)
                    test = dt_str + timedelta(hours=7)
                    time_stamp = calendar.timegm(test.timetuple()) * 1000
                    ts_plot_pm25.append([time_stamp, round(float(val))])
            field2 = nc_fid.variables[s_var2][:]
            lats = nc_fid.variables['lat'][:]
            lons = nc_fid.variables['lon'][:]  # Defining the longitude array
            time = nc_fid.variables['time'][:]
            # Defining the variable array(throws error if variable is not in combined.nc)
            # new way to cal dist
            coordinates = list(product(lats, lons))
            dist = []
            for val in coordinates:
                distance = great_circle(val, st_point).kilometers
                dist.append(distance)
            index = np.argmin(np.array(dist))
            lat = coordinates[index][0]
            lon = coordinates[index][1]
            for l in range(len(lats)):
                if lat == lats[l]:
                    lat_idx = l
            for l in range(len(lons)):
                if lon == lons[l]:
                    lon_idx = l

            # print("nearest index of lat and lon")

            # abslat = np.abs(lats - stn_lat)  # Finding the absolute latitude
            # abslon = np.abs(lons - stn_lon)  # Finding the absolute longitude
            # lat_idx = (abslat.argmin())
            # lon_idx = (abslon.argmin())
            # new way end
            for timestep, v in enumerate(time):
                val = field2[lat_idx, lon_idx][timestep]
                if np.isnan(val) == False:
                    dt_str = netCDF4.num2date(lis_var['time'][timestep], units=lis_var['time'].units,
                                              calendar=lis_var['time'].calendar)
                    test = dt_str + timedelta(hours=7)
                    dtt = test.strftime('%Y-%m-%dT%H:%M:%SZ')
                    dt = datetime.strptime(dtt, '%Y-%m-%dT%H:%M:%SZ')
                    time_stamp = calendar.timegm(dt.timetuple()) * 1000
                    ts_plot_bcpm25.append([time_stamp, round(float(val))])
            field3 = nc_fid.variables[s_var3][:]
            lats = nc_fid.variables['lat'][:]
            lons = nc_fid.variables['lon'][:]  # Defining the longitude array
            time = nc_fid.variables['time'][:]
            coordinates = list(product(lats, lons))
            dist = []
            for val in coordinates:
                distance = great_circle(val, st_point).kilometers
                dist.append(distance)
            index = np.argmin(np.array(dist))
            lat = coordinates[index][0]
            lon = coordinates[index][1]
            for l in range(len(lats)):
                if lat == lats[l]:
                    lat_idx = l
            for l in range(len(lons)):
                if lon == lons[l]:
                    lon_idx = l
            for timestep, v in enumerate(time):

                val = field3[lat_idx, lon_idx][timestep]
                if np.isnan(val) == False:
                    dt_str = netCDF4.num2date(lis_var['time'][timestep], units=lis_var['time'].units,
                                              calendar=lis_var['time'].calendar)
                    test = dt_str + timedelta(hours=7)
                    dtt = test.strftime('%Y-%m-%dT%H:%M:%SZ')
                    dt = datetime.strptime(dtt, '%Y-%m-%dT%H:%M:%SZ')
                    time_stamp = calendar.timegm(dt.timetuple()) * 1000
                    ts_plot_geospm25.append([time_stamp, round(float(val))])
        
        elif run_type == "geos5km":
            field = nc_fid.variables[s_var][:]
            lats = nc_fid.variables['lat'][:]
            lons = nc_fid.variables['lon'][:]  # Defining the longitude array
            time = nc_fid.variables['time'][:]
            abslat = np.abs(lats - stn_lat)  # Finding the absolute latitude
            abslon = np.abs(lons - stn_lon)  # Finding the absolute longitude
            lat_idx = (abslat.argmin())
            lon_idx = (abslon.argmin())
            for timestep, v in enumerate(time):
                val = field[lat_idx, lon_idx][timestep]
                if np.isnan(val) == False:
                    dt_str = netCDF4.num2date(lis_var['time'][timestep], units=lis_var['time'].units,
                                              calendar=lis_var['time'].calendar)
                    dtt = dt_str.strftime('%Y-%m-%dT%H:%M:%SZ')
                    dt = datetime.strptime(dtt, '%Y-%m-%dT%H:%M:%SZ')
                    time_stamp = calendar.timegm(dt.utctimetuple()) * 1000
                    ts_plot.append([time_stamp, round(float(val))])
        
        elif run_type == "vfei":
            field = nc_fid.variables[s_var][:]
            lats = nc_fid.variables['lat'][:]
            lons = nc_fid.variables['lon'][:]  
            
            lat_idx = np.abs(lats - stn_lat).argmin()  
            lon_idx = np.abs(lons - stn_lon).argmin()  

            # Initialize the variable to hold the firecount value
            value_at_point = 0

            # Try to extract the firecount value at that point
            
            try:
                value_at_point = field[lat_idx]
            except IndexError:
                print("No value found at the specified point. Returning 0.")
            
            # Extract the field value at that point
            # value_at_point = field[lat_idx]
            ts_plot.append(value_at_point)
        else:
            field = nc_fid.variables[s_var][:]
            lats = nc_fid.variables['Latitude'][:]
            lons = nc_fid.variables['Longitude'][:]  # Defining the longitude array
            time = nc_fid.variables['time'][:]
            coordinates = list(product(lats, lons))
            dist = []
            for val in coordinates:
                distance = great_circle(val, st_point).kilometers
                dist.append(distance)
            index = np.argmin(np.array(dist))
            lat = coordinates[index][0]
            lon = coordinates[index][1]
            for l in range(len(lats)):
                if lat == lats[l]:
                    lat_idx = l
            for l in range(len(lons)):
                if lon == lons[l]:
                    lon_idx = l
            for timestep, v in enumerate(time):

                val = field[timestep, lat_idx, lon_idx]
                if np.isnan(val) == False:
                    dt_str = netCDF4.num2date(lis_var['time'][timestep], units=lis_var['time'].units,
                                              calendar=lis_var['time'].calendar)
                    dtt = dt_str.strftime('%Y-%m-%dT%H:%M:%SZ')
                    dt = datetime.strptime(dtt, '%Y-%m-%dT%H:%M:%SZ')
                    time_stamp = calendar.timegm(dt.utctimetuple()) * 1000
                    ts_plot.append([time_stamp, round(float(val))])
        

        ts_plot.sort()
        ts_plot_pm25.sort()
        ts_plot_bcpm25.sort()
        ts_plot_geospm25.sort()
        point = [round(stn_lat, 2), round(stn_lon, 2)]
        json_obj["plot"] = ts_plot

        # json_obj["ml_pm25"] = ts_plot_pm25
        if freq == "station":
            json_obj["bc_mlpm25"] = ts_plot_bcpm25
        # json_obj["geos_pm25"] = ts_plot_geospm25
        json_obj["geom"] = point
        # logger.info("PLOT POINT OBJECT : " + json.dumps(json_obj["plot"]))
        # logger.info(json.dumps(json_obj["geom"]))
    except Exception as e:
        return json_obj
    return json_obj

@csrf_exempt
def get_poylgon_values(s_var, geom_data, freq, run_type, run_date):
    """Helper function to generate time series for a polygon"""
    # logger.info("PARAMETERS : ['" + s_var +"','"+ geom_data +"','"+ freq +"','"+ run_type +"','"+ run_date+"']")
    # Empty list to store the timeseries values
    ts_plot = []
    json_obj_arr =[]

    if len(json.loads(geom_data)) != 5:
        geom_data=json.loads(geom_data)
        for g_data in geom_data:
            json_obj = {}
            # Defining the lat and lon from the coords string
            poly_geojson = Polygon(json.loads(json.dumps(g_data)))
            shape_obj = shape(poly_geojson)
            bounds = poly_geojson.bounds
            miny = float(bounds[0])
            minx = float(bounds[1])
            maxy = float(bounds[2])
            maxx = float(bounds[3])

            """Make sure you have this path for all the run_types(/home/tethys/aq_dir/fire/combined/combined.nc)"""
            if run_type == "geos" or run_type == "geos5" or run_type == "vfei":
                infile = THREDDS_OPANDAP+run_type+"/"+ run_date
            else:
                print("No data found")
                infile = os.path.join(DATA_DIR, run_type, freq, run_date)
            
            nc_fid = netCDF4.Dataset(infile, 'r')
            lis_var = nc_fid.variables

            if run_type == "geos" or run_type== "geos5":
                field = nc_fid.variables[s_var][:]
                lats = nc_fid.variables['lat'][:]
                lons = nc_fid.variables['lon'][:]  # Defining the longitude array
                time = nc_fid.variables['time'][:]
                # Defining the variable array(throws error if variable is not in combined.nc)

                latli = np.argmin(np.abs(lats - minx))
                latui = np.argmin(np.abs(lats - maxx))

                lonli = np.argmin(np.abs(lons - miny))
                lonui = np.argmin(np.abs(lons - maxy))
                for timestep, v in enumerate(time):
                    val = field[latli:latui,lonli:lonui,timestep]
                    val = np.mean(val)
                    if np.isnan(val) == False:
                        dt_str = netCDF4.num2date(lis_var['time'][timestep], units=lis_var['time'].units,
                                                  calendar=lis_var['time'].calendar)
                        test = dt_str + timedelta(hours=7)
                        dtt = test.strftime('%Y-%m-%dT%H:%M:%SZ')
                        dt = datetime.strptime(dtt, '%Y-%m-%dT%H:%M:%SZ')
                        time_stamp = calendar.timegm(dt.timetuple()) * 1000
                        ts_plot.append([time_stamp, round(float(val))])
            
            elif run_type == "vfei":
                field = nc_fid.variables[s_var][:]
                lats = nc_fid.variables['lat'][:]
                lons = nc_fid.variables['lon'][:]
                latli = np.argmin(np.abs(lats - minx))
                latui = np.argmin(np.abs(lats - maxx))

                lonli = np.argmin(np.abs(lons - miny))
                lonui = np.argmin(np.abs(lons - maxy))
                val = field[latli:latui,lonli:lonui]
                val = np.mean(val)
                ts_plot.append(val)
            else:
                """Reading variables from combined.nc"""
                lats = nc_fid.variables['Latitude'][:]  # Defining the latitude array
                lons = nc_fid.variables['Longitude'][:]  # Defining the longitude array
                field = nc_fid.variables[s_var][:]  # Defning the variable array(throws error if variable is not in combined.nc)
                time = nc_fid.variables['time'][:]

                latli = np.argmin(np.abs(lats - minx))
                latui = np.argmin(np.abs(lats - maxx))

                lonli = np.argmin(np.abs(lons - miny))
                lonui = np.argmin(np.abs(lons - maxy))
                for timestep, v in enumerate(time):
                    vals = field[timestep, latli:latui, lonli:lonui]
                    if run_type == 'fire':
                        val = np.sum(vals)
                    else:
                        val = np.mean(vals)
                    if np.isnan(val) == False:
                        dt_str = netCDF4.num2date(lis_var['time'][timestep], units=lis_var['time'].units,
                                                  calendar=lis_var['time'].calendar)
                        dtt = dt_str.strftime('%Y-%m-%dT%H:%M:%SZ')
                        dt = datetime.strptime(dtt, '%Y-%m-%dT%H:%M:%SZ')
                        time_stamp = calendar.timegm(dt.utctimetuple()) * 1000
                        ts_plot.append([time_stamp, float(val)])

            ts_plot.sort()

            geom = [round(minx, 2), round(miny, 2), round(maxx, 2), round(maxy, 2)]

            json_obj["plot"] = ts_plot
            json_obj["geom"] = geom
            # if len(ts_plot) == 0:
            #     logger.warn("The selected polygon has no data")
            # else:
            #     logger.info("PLOT POLYGON OBJECT : " + json.dumps(json_obj["plot"]))
            # logger.info(json.dumps(json_obj["geom"]))
            json_obj_arr.append(json_obj)
    else:
        json_obj = {}
        poly_geojson = Polygon(json.loads(geom_data))
        shape_obj = shape(poly_geojson)
        bounds = poly_geojson.bounds
        miny = float(bounds[0])
        minx = float(bounds[1])
        maxy = float(bounds[2])
        maxx = float(bounds[3])

        """Make sure you have this path for all the run_types(/home/tethys/aq_dir/fire/combined/combined.nc)"""
        if run_type == "geos" or run_type == "geos5" or run_type == "vfei":
            infile = THREDDS_OPANDAP+run_type+"/"+ run_date
        else:
            infile = os.path.join(DATA_DIR, run_type, freq, run_date)
        nc_fid = netCDF4.Dataset(infile, 'r')
        lis_var = nc_fid.variables
        
        if "geos" == run_type or run_type == "geos5":
            field = nc_fid.variables[s_var][:]
            lats = nc_fid.variables['lat'][:]
            lons = nc_fid.variables['lon'][:]  # Defining the longitude array
            time = nc_fid.variables['time'][:]
            # Defining the variable array(throws error if variable is not in combined.nc)

            latli = np.argmin(np.abs(lats - minx))
            latui = np.argmin(np.abs(lats - maxx))

            lonli = np.argmin(np.abs(lons - miny))
            lonui = np.argmin(np.abs(lons - maxy))
            for timestep, v in enumerate(time):
                val = field[latli:latui, lonli:lonui, timestep]
                val = np.mean(val)
                if np.isnan(val) == False:
                    dt_str = netCDF4.num2date(lis_var['time'][timestep], units=lis_var['time'].units,
                                              calendar=lis_var['time'].calendar)
                    test = dt_str + timedelta(hours=7)
                    dtt = test.strftime('%Y-%m-%dT%H:%M:%SZ')
                    dt = datetime.strptime(dtt, '%Y-%m-%dT%H:%M:%SZ')
                    time_stamp = calendar.timegm(dt.timetuple()) * 1000
                    ts_plot.append([time_stamp, round(float(val))])
        
        elif run_type == "vfei":
            field = nc_fid.variables[s_var][:]
            lats = nc_fid.variables['lat'][:]
            lons = nc_fid.variables['lon'][:]

            # Find the index of latitude and longitude corresponding to the bounding box
            lat_idx = np.argmin(np.abs(lats - minx))
            lon_idx = np.argmin(np.abs(lons - miny))
            
            # Filter values within the polygon
            vals_within_polygon = []
            area_value = field[lat_idx]
            vals_within_polygon.append(area_value)
            
            # Check if there are valid values within the polygon
            if len(vals_within_polygon) == 0:
                ts_plot.append("No data available within the specified polygon.")
            else:
                # Calculate the mean value within the polygon
                mean_val_within_polygon = np.mean(vals_within_polygon)
                ts_plot.append(mean_val_within_polygon)
        else:
            """Reading variables from combined.nc"""
            lats = nc_fid.variables['Latitude'][:]  # Defining the latitude array
            lons = nc_fid.variables['Longitude'][:]  # Defining the longitude array
            field = nc_fid.variables[s_var][
                    :]  # Defning the variable array(throws error if variable is not in combined.nc)
            time = nc_fid.variables['time'][:]

            latli = np.argmin(np.abs(lats - minx))
            latui = np.argmin(np.abs(lats - maxx))

            lonli = np.argmin(np.abs(lons - miny))
            lonui = np.argmin(np.abs(lons - maxy))
            for timestep, v in enumerate(time):
                vals = field[timestep, latli:latui, lonli:lonui]
                if run_type == 'fire':
                    val = np.sum(vals)
                else:
                    val = np.mean(vals)
                if np.isnan(val) == False:
                    dt_str = netCDF4.num2date(lis_var['time'][timestep], units=lis_var['time'].units,
                                              calendar=lis_var['time'].calendar)
                    dtt = dt_str.strftime('%Y-%m-%dT%H:%M:%SZ')
                    dt = datetime.strptime(dtt, '%Y-%m-%dT%H:%M:%SZ')
                    time_stamp = calendar.timegm(dt.utctimetuple()) * 1000
                    ts_plot.append([time_stamp, float(val)])

        ts_plot.sort()

        geom = [round(minx, 2), round(miny, 2), round(maxx, 2), round(maxy, 2)]

        json_obj["plot"] = ts_plot
        json_obj["geom"] = geom
        # if len(ts_plot) == 0:
        #     logger.warn("The selected polygon has no data")
        # else:
        #     logger.info("PLOT POLYGON OBJECT : " + json.dumps(json_obj["plot"]))
        # logger.info(json.dumps(json_obj["geom"]))
        return json_obj
    return json_obj_arr


def get_current_station(obs_date):
    try:
        with connections['pcd_database'].cursor() as cursor:
            sql = """
                SELECT tbl1.station_id, tbl1.rid, tbl1.datetime, tbl1.lat, tbl1.long, tbl1.pm25, tbl1.name_en, tbl2.aqi, tbl2.aqi_level
                FROM (
                    SELECT DISTINCT ON (s.station_id) s.station_id, s.rid, m.datetime, s.lat, s.long, m.pm25, s.name_en
                    FROM stations s, nrt_measurements m
                    WHERE s.station_id = m.station_id AND m.pm25 IS NOT null AND m.datetime <= %s
                    ORDER BY s.station_id, m.datetime DESC
                ) AS tbl1
                LEFT JOIN measurements tbl2 ON tbl1.station_id = tbl2.station_id AND tbl2.datetime = tbl1.datetime
            """
            
            cursor.execute(sql, [obs_date])
            data = cursor.fetchall()

            stations = []
            for row in data:
                rid = row[1]
                name = row[6]
                station_id = row[0]
                lat = row[3]
                lon = row[4]
                pm25 = row[5]
                latest_date = row[2]
                aqi = row[7]
                aqi_level = row[8]
                selected_date = datetime.strptime(obs_date, '%Y-%m-%d %H:%M:%S')
                difference = latest_date - selected_date

                if difference.days == -1 or difference.days == 0:
                    stations.append({
                        'rid': rid,
                        'station_id': str(station_id),
                        'latest_date': str(latest_date),
                        'lon': lon,
                        'lat': lat,
                        'pm25': pm25,
                        'name': name,
                        'aqi': aqi,
                        'aqi_level': aqi_level
                    })

            if not stations:
                result = {
                    'status': 'Error',
                    'message': 'No data found for the specified observation date',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': []
                }
            else:
                result = {
                    'status': 'Success',
                    'message': 'Data retrieval successful',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': stations
                }

    except Exception as e:
        result = {
            'status': 'Error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': []
        }

    return result


def get_ts(s_var, interaction, run_type, freq, run_date, geom_data):
    return_obj = {}

    try:
        if interaction == 'Point':
            graph = get_pt_values(s_var, geom_data, freq, run_type, run_date)
            return_obj["status"] = "Success"
            return_obj["message"] = "Data retrieval successful"
            return_obj["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return_obj["data"] = graph

        elif interaction == 'Polygon':
            graph = get_poylgon_values(s_var, geom_data, freq, run_type, run_date)
            return_obj["status"] = "Success"
            return_obj["message"] = "Data retrieval successful"
            return_obj["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return_obj["data"] = graph

        elif interaction == 'Station':
            x = geom_data.split(',')
            station = x[0]
            lat = x[1]
            lon = x[2]
            graph = get_pm25_data(s_var, run_type, run_date, station, lat, lon)
            return_obj["status"] = "Success"
            return_obj["message"] = "Data retrieval successful"
            return_obj["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return_obj["data"] = graph

        else:
            return_obj["status"] = "Error"
            return_obj["message"] = "Invalid interaction type"

    except Exception as e:
        return_obj["status"] = "Error"
        return_obj["message"] = f"Error processing request: {str(e)}"

    return return_obj

def gen_style_legend(style):
    style_f = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/data/palettes/'+str(style)+'.pal')
    scale = []
    if os.path.exists(style_f):
        with open(style_f, mode='r') as f:
            lines = f.readlines()
        for line in lines:
            lval = line.split()
            if len(lval)>0:
                rgb = (lval[0], lval[1], lval[2])
                scale.append(rgb)
    return scale

def get_latest_date(dataset):

    if(dataset == 'gems'):
        url = f'{THREDDS_CATALOG}ServirData/{dataset}/catalog.html'
        # Send a GET request to the URL
        response = requests.get(url)
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        links = soup.find_all('a')
        # Extract filenames from the links
        filenames = [link.get('href') for link in links if link.get('href')]

        # Filter filenames that match the date and time pattern
        date_pattern = re.compile(r'GEMS_NO2_\d{8}_\d{4}_\w+')

        dated_filenames = [filename for filename in filenames if date_pattern.search(filename)]
        if not dated_filenames:
            return None
        latest_filename = sorted(dated_filenames, key=lambda x: date_pattern.search(x).group(), reverse=True)[0]
        
        return latest_filename.split("/")[-1]
    
    elif (dataset == 'geos5km'):
        with connections['default'].cursor() as cursor:
            # Fetch all table names starting with 'th'
            cursor.execute("""
                SELECT MAX(init_date) AS latest_date
                FROM main_pm25;
            """)
            res = cursor.fetchone()

            return res[0].strftime('%Y%m%d')
    else:
        url = f'{THREDDS_CATALOG}ServirData/{dataset}/catalog.html'
        # Send a GET request to the URL
        response = requests.get(url)
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        # Find all <a> tags with 'href' attribute containing 'dataset=<dataset_name>'
        links = soup.find_all('a', href=re.compile(rf'dataset={re.escape(dataset)}'))
        # Extract the date portion from the 'href' attributes
        dates = []
        for link in links:
            file_name = link['href'].split('/')[-1]  # Get the last part of the URL
            date_match = re.search(r'(\d{8})\.nc', file_name)  # Extract 8 digits followed by '.nc'
            if date_match:
                dates.append(date_match.group(1))
        
        # Sort the list of dates in descending order and return the latest date
        if dates:
            latest_date = max(dates)
            return latest_date
        else:
            return None


def get_pcd_table_data(obs_date, obs_time):
    # obs_date and obs_time is UTC time
    # Original date and time strings
    date_str = obs_date
    time_str = obs_time

    # Combine date and time into a single datetime object
    datetime_str = date_str + " " + time_str
    datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")

    # add 7 hours because Thai PCD data is using +7UTC
    new_datetime_obj = datetime_obj + timedelta(hours=7)

    # Convert back to date and time strings
    new_date_str = new_datetime_obj.strftime("%Y-%m-%d")
    new_time_str = new_datetime_obj.strftime("%H:%M")

    try:
        with connections['pcd_database'].cursor() as cursor:
            # Fetch all table names starting with 'th'
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name LIKE 'th%'
            """)
            tables = cursor.fetchall()

            data_column = 'pm25'  # The column from which you want to fetch the data
            date_column = 'date'  # The column that contains the date
            time_column = 'time'  # The column that contains the time

            results = []
    
            for table in tables:
                table_name = table[0]
                # Dynamic SQL to fetch the data from each table for specific date and time
                query = f"""
                    SELECT s.sta_id, s.lon, s.lat, station_data.pm25, s.name, station_data.date, station_data.time
                    FROM stations AS s
                    JOIN 
                        (SELECT '{table_name}' AS station_id, t.{data_column}, t.{date_column}, t.{time_column}
                        FROM {table_name} AS t
                        WHERE t.{data_column} IS NOT NULL 
                        AND t.{data_column}::text != 'NaN' -- Exclude 'NaN' values explicitly
                        AND t.{data_column}::text ~ '^[0-9]+(\.[0-9]+)?$' -- Ensure pm25 is numeric
                        ORDER BY ABS(EXTRACT(EPOCH FROM (t.{date_column}::timestamp + t.{time_column}::time)) - 
                                    EXTRACT(EPOCH FROM ('{new_date_str}'::timestamp + '{new_time_str}'::time)))
                        LIMIT 1) AS station_data
                    ON s.sta_id = station_data.station_id;
                """

                cursor.execute(query)
                rows = cursor.fetchall()

                # Append each row's data to the results list
                for row in rows:
                    results.append(row)

            if not results:
                result = {
                    'status': 'Error',
                    'message': 'No data found for the specified observation date',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': []
                }
            else:
                result = {
                    'status': 'Success',
                    'message': 'Data retrieval successful',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': results
                }
    except Exception as e:
        result = {
            'status': 'Error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': []
        }

    return result

def get_city_pm25(forecast_date, init_date):
    try:
        with connections['default'].cursor() as cursor:

            query = """
                SELECT pm25t.id, pm25t.pm25, pm25t.idc, pm25t.forecast_time, pm25t.init_date, c.country, c.city, c.lat, c.lon, c.megacity
                FROM main_citypm25 AS pm25t
                JOIN main_city as c
                ON pm25t.idc = c.idc
                WHERE pm25t.forecast_time = '"""+ forecast_date +"""' AND pm25t.init_date = '""" + init_date + """'
                ORDER BY pm25t.pm25 desc;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            results = []

            # Append each row's data to the results list
            for row in rows:
                results.append(row)

            if not results:
                result = {
                    'status': 'Error',
                    'message': 'No data found for the specified observation date',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': []
                }
            else:
                result = {
                    'status': 'Success',
                    'data': results
                }
    except Exception as e:
        result = {
            'status': 'Error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': []
        }
    return result

def get_adm_pm25_dash(forecast_date, init_date, adm_lvl, area_id):
    cond = ""
    adm ="country"
    try:
        with connections['default'].cursor() as cursor:

            if (adm == 'country' and  area_id != ''):
                # adm == 'province'
                cond = " AND cc.adm0_id = "+ area_id
                table = 'main_province_table'
                addon = ''
                att =  'adm1_id'
                
                query = """
                SELECT pm25t.area_name, pm25t.area_id, 
                    COALESCE(NULLIF(pm25t.min, 'NaN'), 0) as min, 
                    COALESCE(NULLIF(pm25t.max, 'NaN'), 0) as max, 
                    COALESCE(NULLIF(pm25t.average, 'NaN'), 0) as average,
                    pm25t.forecast_time, pm25t.init_date, 
                    c.lat, c.lon, c.adm0_name, c.majorcity, 
                    firm24.firmcount, firm48.firmcount
                """+addon+"""
                FROM main_pm25 AS pm25t
                JOIN """+table+""" as c
                    ON pm25t.area_id = c."""+att+"""
                JOIN main_country_table as cc
                    ON c.adm0_gid = cc.adm0_gid
                LEFT JOIN main_firm24h AS firm24
                    ON pm25t.area_id = firm24.area_id 
                    AND pm25t.adm_lvl = firm24.adm_lvl 
                    AND DATE(pm25t.forecast_time) = firm24.init_date
                LEFT JOIN main_firm48h AS firm48
                    ON pm25t.area_id = firm48.area_id 
                    AND pm25t.adm_lvl = firm48.adm_lvl 
                    AND DATE(pm25t.forecast_time) = firm48.init_date
                WHERE pm25t.forecast_time = '"""+ forecast_date +"""' AND pm25t.init_date = '""" + init_date + """' AND pm25t.adm_lvl = 'province' """+cond+"""
                ORDER BY pm25t.average desc;
            """
            elif (adm == 'province' and area_id != ''):
                adm == 'province'
                cond = " AND c.adm1_id = "+ area_id
                table = 'main_province_table'
                addon = ''
                att =  'adm1_id'
                
                query = """
                SELECT pm25t.area_name, pm25t.area_id, 
                    COALESCE(NULLIF(pm25t.min, 'NaN'), 0) as min, 
                    COALESCE(NULLIF(pm25t.max, 'NaN'), 0) as max, 
                    COALESCE(NULLIF(pm25t.average, 'NaN'), 0) as average, 
                    pm25t.forecast_time, pm25t.init_date, 
                    c.lat, c.lon, c.adm0_name, c.majorcity, 
                    firm24.firmcount, firm48.firmcount
                """+addon+"""
                FROM main_pm25 AS pm25t
                JOIN """+table+""" as c
                    ON pm25t.area_id = c."""+att+"""
                JOIN main_country_table as cc
                    ON c.adm0_gid = cc.adm0_gid
                LEFT JOIN main_firm24h AS firm24
                    ON pm25t.area_id = firm24.area_id 
                    AND pm25t.adm_lvl = firm24.adm_lvl 
                    AND DATE(pm25t.forecast_time) = firm24.init_date
                LEFT JOIN main_firm48h AS firm48
                    ON pm25t.area_id = firm48.area_id 
                    AND pm25t.adm_lvl = firm48.adm_lvl 
                    AND DATE(pm25t.forecast_time) = firm48.init_date
                WHERE pm25t.forecast_time = '"""+ forecast_date +"""' AND pm25t.init_date = '""" + init_date + """' AND pm25t.adm_lvl = 'province' """+cond+"""
                ORDER BY pm25t.average desc;
            """
            else:
                if adm_lvl == 'country':
                    table = 'main_country_table'
                    addon = ''
                    att =  'adm0_id'
                    adm == 'country'
                elif adm_lvl == 'province':
                    table = 'main_province_table'
                    addon = ''
                    att =  'adm1_id'
                    adm == 'province'
                elif adm_lvl == 'district':
                    table = 'main_district_table'
                    addon = ', c.adm1_name'
                    att =  'adm2_id'
                    
                query = """
                    SELECT pm25t.area_name, pm25t.area_id, 
                    COALESCE(NULLIF(pm25t.min, 'NaN'), 0) as min, 
                    COALESCE(NULLIF(pm25t.max, 'NaN'), 0) as max, 
                    COALESCE(NULLIF(pm25t.average, 'NaN'), 0) as average, 
                    pm25t.forecast_time, pm25t.init_date, c.lat, c.lon, c.adm0_name, c.majorcity, firm24.firmcount, firm48.firmcount  """+addon+"""
                    FROM main_pm25 AS pm25t
                    JOIN """+table+""" as c
                        ON pm25t.area_id = c."""+att+"""
                    JOIN main_country_table as cc
                        ON c.adm0_gid = cc.adm0_gid
                    LEFT JOIN main_firm24h AS firm24
                        ON pm25t.area_id = firm24.area_id 
                        AND pm25t.adm_lvl = firm24.adm_lvl 
                        AND DATE(pm25t.forecast_time) = firm24.init_date
                    LEFT JOIN main_firm48h AS firm48
                        ON pm25t.area_id = firm48.area_id 
                        AND pm25t.adm_lvl = firm48.adm_lvl 
                        AND DATE(pm25t.forecast_time) = firm48.init_date
                    WHERE pm25t.forecast_time = '"""+ forecast_date +"""' AND pm25t.init_date = '""" + init_date + """' AND pm25t.adm_lvl = '"""+adm_lvl+"""' """+cond+"""
                    ORDER BY pm25t.average desc;
                """
            cursor.execute(query)
            rows = cursor.fetchall()
            results = []

            # Append each row's data to the results list
            for row in rows:
                results.append(row)

            if not results:
                result = {
                    'status': 'Error',
                    'message': 'No data found for the specified observation date',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': []
                }
            else:
                result = {
                    'status': 'Success',
                    'data': results
                }
            
    except Exception as e:
        result = {
            'status': 'Error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': []
        }
    return result

def get_pm25_province_dash(forecast_date, init_date, adm_lvl, area_id):
    cond = ""
    try:
        with connections['default'].cursor() as cursor:
            if(area_id != ''):
                cond = " AND c.adm1_id = "+ area_id
            table = 'main_province_table'
            addon = ''
            att =  'adm1_id'
            
            query = """
                SELECT pm25t.area_name, pm25t.area_id, 
                 COALESCE(NULLIF(pm25t.min, 'NaN'), 0) as min, 
                COALESCE(NULLIF(pm25t.max, 'NaN'), 0) as max, 
                COALESCE(NULLIF(pm25t.average, 'NaN'), 0) as average, 
                pm25t.forecast_time, pm25t.init_date, c.lat, c.lon, c.adm0_name, c.majorcity, firm24.firmcount, firm48.firmcount  """+addon+"""
                FROM main_pm25 AS pm25t
                JOIN """+table+""" as c
                    ON pm25t.area_id = c."""+att+"""
                JOIN main_country_table as cc
                    ON c.adm0_gid = cc.adm0_gid
                LEFT JOIN main_firm24h AS firm24
                    ON pm25t.area_id = firm24.area_id 
                    AND pm25t.adm_lvl = firm24.adm_lvl 
                    AND DATE(pm25t.forecast_time) = firm24.init_date
                LEFT JOIN main_firm48h AS firm48
                    ON pm25t.area_id = firm48.area_id 
                    AND pm25t.adm_lvl = firm48.adm_lvl 
                    AND DATE(pm25t.forecast_time) = firm48.init_date
                WHERE pm25t.forecast_time = '"""+ forecast_date +"""' AND pm25t.init_date = '""" + init_date + """' AND pm25t.adm_lvl = 'province' """+cond+"""
                ORDER BY pm25t.average desc;
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            results = []

            # Append each row's data to the results list
            for row in rows:
                results.append(row)

            if not results:
                result = {
                    'status': 'Error',
                    'message': 'No data found for the specified observation date',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': []
                }
            else:
                result = {
                    'status': 'Success',
                    'data': results
                }
            
    except Exception as e:
        result = {
            'status': 'Error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': []
        }
    return result

def get_adm_pm25(forecast_date, init_date, adm_lvl):
    if adm_lvl == 'country':
        table = 'main_country_table'
        addon = ''
        att =  'adm0_id'
    elif adm_lvl == 'province':
        table = 'main_province_table'
        addon = ', c.majorcity'
        att =  'adm1_id'
    elif adm_lvl == 'district':
        table = 'main_district_table'
        addon = ', c.adm1_name'
        att =  'adm2_id'

    try:
        with connections['default'].cursor() as cursor:
            query = """
            SELECT pm25t.area_name, pm25t.area_id, 
                    COALESCE(NULLIF(pm25t.min, 'NaN'), 0) as min, 
                    COALESCE(NULLIF(pm25t.max, 'NaN'), 0) as max, 
                    COALESCE(NULLIF(pm25t.average, 'NaN'), 0) as average,
                    pm25t.forecast_time, pm25t.init_date, 
                    c.lat, c.lon, c.adm0_name, firm24.firmcount, firm48.firmcount  """+addon+"""
            FROM main_pm25 AS pm25t
            JOIN """+table+""" as c ON pm25t.area_id = c."""+att+"""
            LEFT JOIN main_firm24h AS firm24 ON pm25t.area_id = firm24.area_id 
                AND pm25t.adm_lvl = firm24.adm_lvl 
                AND DATE(pm25t.forecast_time) = firm24.init_date
            LEFT JOIN main_firm48h AS firm48 ON pm25t.area_id = firm48.area_id 
                AND pm25t.adm_lvl = firm48.adm_lvl 
                AND DATE(pm25t.forecast_time) = firm48.init_date
            WHERE pm25t.forecast_time = '""" + forecast_date + """' 
                AND pm25t.init_date = '"""+ init_date +"""' 
                AND pm25t.adm_lvl = '"""+adm_lvl+"""'
            ORDER BY pm25t.average DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            results = []

            # Append each row's data to the results list
            for row in rows:
                results.append(row)

            if not results:
                result = {
                    'status': 'Error',
                    'message': 'No data found for the specified observation date',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': []
                }
            else:
                result = {
                    'status': 'Success',
                    'data': results
                }
            
    except Exception as e:
        result = {
            'status': 'Error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': []
        }
    return result

def get_adm_no2(forecast_date, init_date, adm_lvl):
    if adm_lvl == 'country':
        table = 'main_country_table'
        addon = ''
        att =  'adm0_id'
    elif adm_lvl == 'province':
        table = 'main_province_table'
        addon = ', c.majorcity'
        att =  'adm1_id'
    elif adm_lvl == 'district':
        table = 'main_district_table'
        addon = ', c.adm1_name'
        att =  'adm2_id'

    try:
        with connections['default'].cursor() as cursor:
            
            query = """
            SELECT no2t.area_name, no2t.area_id, no2t.min, no2t.max, no2t.average, no2t.obs_time, no2t.init_date, c.lat, c.lon, c.adm0_name, firm24.firmcount, firm48.firmcount  """+addon+"""
            FROM main_no2 AS no2t
            JOIN """+table+""" as c ON no2t.area_id = c."""+att+"""
            LEFT JOIN main_firm24h AS firm24 ON no2t.area_id = firm24.area_id 
                AND no2t.adm_lvl = firm24.adm_lvl 
                AND no2t.init_date = firm24.init_date
            LEFT JOIN main_firm48h AS firm48 ON no2t.area_id = firm48.area_id 
                AND no2t.adm_lvl = firm48.adm_lvl 
                AND no2t.init_date = firm48.init_date
            WHERE no2t.obs_time = '""" + forecast_date + """' 
                AND no2t.init_date = '"""+ init_date +"""' 
                AND no2t.adm_lvl = '"""+adm_lvl+"""'
            ORDER BY no2t.average DESC;
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            results = []

            # Append each row's data to the results list
            for row in rows:
                results.append(row)

            if not results:
                result = {
                    'status': 'Error',
                    'message': 'No data found for the specified observation date',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': []
                }
            else:
                result = {
                    'status': 'Success',
                    'data': results
                }
            
    except Exception as e:
        result = {
            'status': 'Error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': []
        }
    return result

def get_city_pm25_timeseries(area_id, init_date, adm_lvl):
    if adm_lvl == 'country':
        table = 'main_country_table'
        addon = ''
        att =  'adm0_id'
    elif adm_lvl == 'province':
        table = 'main_province_table'
        addon = ''
        att =  'adm1_id'
    elif adm_lvl == 'district':
        table = 'main_district_table'
        addon = ', c.adm1_name'
        att =  'adm2_id'

    try:
        with connections['default'].cursor() as cursor:
            query = """
            SELECT * FROM (SELECT pm25t.id, pm25t.average, pm25t.area_id, pm25t.forecast_time, pm25t.init_date
            FROM main_pm25 AS pm25t
            JOIN """+table+""" AS c ON pm25t.area_id = c."""+att+"""
            WHERE pm25t.area_id = %s AND init_date = %s
            ORDER BY pm25t.forecast_time desc
            LIMIT 200) ORDER BY forecast_time; 
            """
            # query = """
            #     SELECT pm25t.area_name, pm25t.area_id, pm25t.min, pm25t.max, pm25t.average, pm25t.forecast_time, pm25t.init_date, c.lat, c.lon, c.adm0_name """+addon+"""
            #     FROM main_pm25 AS pm25t
            #     JOIN """+table+""" as c
            #     ON pm25t.area_id = c."""+att+"""
            #     WHERE pm25t.area_id = """ + area_id + """ AND pm25t.init_date = '""" + init_date + """'
            #     ORDER BY pm25t.average desc;
            # """

            cursor.execute(query, (area_id, init_date))
            rows = cursor.fetchall()
            results = []

            # Append each row's data to the results list
            for row in rows:
                results.append(row)

            if not results:
                result = {
                    'status': 'Error',
                    'message': 'No data found for the specified observation date',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': []
                }
            else:
                result = {
                    'status': 'Success',
                    'data': results
                }
                

    except Exception as e:
        result = {
            'status': 'Error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': []
        }

    return result

# def get_city_pm25_timeseries(idc, init_date):
#     try:
#         with connections['default'].cursor() as cursor:
#             query = """
#             SELECT * FROM (SELECT pm25t.id, pm25t.pm25, pm25t.idc, pm25t.forecast_time, pm25t.init_date, c.country, c.city, c.lat, c.lon
#             FROM main_citypm25 AS pm25t
#             JOIN main_city AS c ON pm25t.idc = c.idc
#             WHERE c.idc = %s AND init_date = %s
#             ORDER BY pm25t.forecast_time desc
#             LIMIT 200) ORDER BY forecast_time; 
#             """
#             cursor.execute(query, (idc, init_date))
#             rows = cursor.fetchall()
#             results = []

#             # Append each row's data to the results list
#             for row in rows:
#                 results.append(row)

#             if not results:
#                 result = {
#                     'status': 'Error',
#                     'message': 'No data found for the specified observation date',
#                     'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                     'data': []
#                 }
#             else:
#                 result = {
#                     'status': 'Success',
#                     'data': results
#                 }
                

#     except Exception as e:
#         result = {
#             'status': 'Error',
#             'message': f'Error: {str(e)}',
#             'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#             'data': []
#         }

#     return result

def get_location():
    try:
        with connections['default'].cursor() as cursor:

            query = """
                SELECT c.country, c.city, c.lat, c.lon, c.megacity
                FROM main_city as c
                ORDER BY c.city;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            results = []

            # Append each row's data to the results list
            for row in rows:
                results.append(row)

            if not results:
                result = {
                    'status': 'Error',
                    'message': 'No data found for the specified observation date',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': []
                }
            else:
                result = {
                    'status': 'Success',
                    'data': results
                }
                

    except Exception as e:
        result = {
            'status': 'Error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': []
        }
    return result
def get_country_list():
    try:
        with connections['default'].cursor() as cursor:

            query = """
                SELECT adm0_id, adm0_name, adm0_id, adm0_name, lon, lat
                FROM main_country_table 
                ORDER BY adm0_name;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            results = []

            # Append each row's data to the results list
            for row in rows:
                results.append(row)

            if not results:
                result = {
                    'status': 'Error',
                    'message': 'No data found for the specified observation date',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': []
                }
            else:
                result = {
                    'status': 'Success',
                    'data': results
                }
                
    except Exception as e:
        result = {
            'status': 'Error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': []
        }

    return result


def get_province_list():
    try:
        with connections['default'].cursor() as cursor:

            query = """
                SELECT c.adm0_id, p.adm0_name, p.adm1_id, p.adm1_name, p.lon, p.lat
                FROM main_province_table AS p
                JOIN main_country_table AS c ON p.adm0_gid = c.adm0_gid
                ORDER BY adm1_name;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            results = []

            # Append each row's data to the results list
            for row in rows:
                results.append(row)

            if not results:
                result = {
                    'status': 'Error',
                    'message': 'No data found for the specified observation date',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': []
                }
            else:
                result = {
                    'status': 'Success',
                    'data': results
                }
                

    except Exception as e:
        result = {
            'status': 'Error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': []
        }

    return result


def get_pm25(forecast_date, init_date):
    try:
        with connections['default'].cursor() as cursor:

            query = """
                SELECT pm25t.*, c.country, c.city, c.lat, c.lon, c.megacity
                FROM main_PM25 AS pm25t
                JOIN main_city as c
                ON pm25t.idc = c.idc
                WHERE pm25t.forecast_time = '"""+ forecast_date +"""' AND pm25t.init_date = '""" + init_date + """'
                ORDER BY pm25t.pm25 desc;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            results = []

            # Append each row's data to the results list
            for row in rows:
                results.append(row)

            if not results:
                result = {
                    'status': 'Error',
                    'message': 'No data found for the specified observation date',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': []
                }
            else:
                result = {
                    'status': 'Success',
                    'data': results
                }
            
    except Exception as e:
        result = {
            'status': 'Error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': []
        }
    return result