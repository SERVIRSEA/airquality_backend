# -*- coding: utf-8 -*-
import os
from requests.auth import HTTPBasicAuth
import requests
from datetime import date, timedelta, datetime

class UploadTiffFile():

    # GEOSEVER URL. 
    REST_URL = 'http://216.218.240.247:8000/geoserver/rest'
    USER = 'servirsea'
    PWD = 'PWD'

    HEADERS = {
        'content-type': 'application/json'
    }

    def __init__(self, files):
        self.base = '/opt/geoserver/data_dir/aq_data/geos5/'
        self.workspace = 'aq'
        self.files = files
        self.crs = "EPSG:4326"  # Coordinate Reference System (CRS) code
        self.style_name = 'raster'
 
    def upload_tiff(self):
        for file in self.files:
            file_path = os.path.join(self.base, file)
            print(file_path)
            store_name = str(file.split('.tif')[0])
            layer_name = store_name  # Name for your GeoTIFF layer

            # Create a GeoTIFF store payload
            store_url = f"{UploadTiffFile.REST_URL}/workspaces/{self.workspace}/coveragestores"
            payload = {
                "coverageStore": {
                    "name": store_name,
                    "workspace": self.workspace,
                    "type": "GeoTIFF",
                    "enabled": True,
                    "url": "file:" + file_path.replace("\\","/")  # Update with your directory path
                }
            }

            # Set up the URL for creating a layer
            layer_url = f"{UploadTiffFile.REST_URL}/workspaces/{self.workspace}/coveragestores/{store_name}/coverages"

            # Create a GeoTIFF layer payload
            payloadLayer = {
                "coverage": {
                    "name": layer_name,
                    "title": layer_name,
                    "enabled": True,
                    "nativeName": layer_name,
                    "projectionPolicy": "REPROJECT_TO_DECLARED",
                    "enabled": True,

                    "nativeFormat": "GeoTIFF",
                    
                    "supportedFormats": {
                        "string": [ "GEOTIFF", "Gtopo30", "ArcGrid", "GeoPackage (mosaic)", "NetCDF", "ImageMosaic", "GIF", "PNG", "JPEG", "TIFF" ]
                    },
                    "interpolationMethods": {
                        "string": [ "nearest neighbor", "bilinear", "bicubic" ]
                    },
                    "defaultInterpolationMethod": "bilinear",

                    "requestSRS": {
                        "string": [ "EPSG:4326", "EPSG:3857"]
                    },
                    "responseSRS": {
                        "string": [ "EPSG:4326", "EPSG:3857"]
                    },
                    "srs": self.crs,
                    "metadata": {
                        "time": {"enabled": True}  # Adjust metadata structure as needed
                    },
                    "defaultStyle": {
                        "name": self.style_name,
                    }
                }
            }

            auth = HTTPBasicAuth(UploadTiffFile.USER, UploadTiffFile.PWD)
            auth_response = requests.get(UploadTiffFile.REST_URL, auth=auth)

            if auth_response.status_code == 200:
                #print("Authentication successful!")

                # Create the GeoTIFF store
                store_response = requests.post(store_url, auth=auth, json=payload)

                if store_response.status_code == 201:
                    print(f"GeoTIFF store '{store_name}' created successfully!")

                    # Create the GeoTIFF layer
                    layer_response = requests.post(layer_url, auth=auth, json=payloadLayer)

                    if layer_response.status_code == 201:
                        print(f"GeoTIFF layer '{layer_name}' created successfully!")
                    else:
                        print(f"Error creating GeoTIFF layer: {layer_response.text}")
                        
                else:
                    print(f"Error creating GeoTIFF store: {store_response.text}")
            else:
                print("Authentication failed. Please check your credentials.")
                #print(auth_response.text)

def main():
    # Today's date
    today = datetime.now() + timedelta(days=3)
    print(today)
    # Create a list of dates 30 days before today, formatted as YYYYMMDD
    date_array = [(today - timedelta(days=i)).strftime('%Y%m%d') for i in range(7)]

    for d in date_array:
        filterKey = 'geos_'+ d
        files = [x for x in os.listdir("/home/ubuntu/geoserver_data/aq_data/geos5/") if x.endswith(".tif") and x.startswith(filterKey)]
        if(files):
            upload = UploadTiffFile(files)
            upload.upload_tiff()
    print("Successfully upload rasters into Geoserver")

if __name__ == "__main__":
    main()
