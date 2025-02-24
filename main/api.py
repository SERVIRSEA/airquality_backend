import os, json
from django.shortcuts import render
from django.contrib.staticfiles import finders
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from .authentication import APIKeyAuthentication
from .core import *

@csrf_exempt 
@api_view(['GET'])
@authentication_classes([APIKeyAuthentication])
@permission_classes([IsAuthenticated])
# @permission_classes([AllowAny])
def api(request):
    action = request.query_params.get('action', '')

    if action:
        request_methods = [
            'get-stations',
            'get-time',
            'get-chartData',
            'get-24hstations',
            'get-latest-date',
            'get-pcd-data-table',
            'get-city-pm25',
            'get-city-pm25-timeseries',
            'get-location',
            'get-data-pm25',
            'get-data-pm25-dash',
            'get-country-list',
            'get-province-list',
            'get-data-pm25-province-dash',
            'get-data-no2',
            'get-daily-average-pm25-timeseries',
            'get-pm25-country'
        ]

        if action in request_methods:
            obs_date = request.query_params.get('obs_date', '')
            obs_time = request.query_params.get('obs_time', '')
            freq = request.query_params.get('freq', '')
            run_date = request.query_params.get('run_date', '')
            run_type = request.query_params.get('run_type', '')
            freq_chart = request.query_params.get('freq_chart', '')
            geom_data = request.query_params.get('geom_data', '')
            interaction = request.query_params.get('interaction', '')
            run_date_chart = request.query_params.get('run_date_chart', '')
            run_type_chart = request.query_params.get('run_type_chart', '')
            variable = request.query_params.get('variable', '')
            dataset = request.query_params.get('dataset', '')
            forecast_date = request.query_params.get('forecast_date', '')
            area_id = request.query_params.get('area_id', '')
            init_date = request.query_params.get('init_date', '')
            adm_lvl = request.query_params.get('adm_lvl', '')
            start_date = request.query_params.get('start_date', '')
            end_date = request.query_params.get('end_date', '')
            area_ids = request.query_params.get('area_ids', '')

            if action == 'get-stations':
                data = get_current_station(obs_date)

                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
            
            elif action == 'get-time':
                data = get_time(freq, run_type, run_date)
                
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
            
            elif action == 'get-chartData':
                data = get_ts(s_var=variable, interaction=interaction, run_type=run_type_chart, freq=freq_chart, run_date=run_date_chart, geom_data=geom_data)

                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
            
            elif action == 'get-latest-date':
                data = get_latest_date(dataset=dataset)

                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
            
            elif action == 'get-pcd-data-table':
                data = get_pcd_table_data(obs_date, obs_time)
                
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
            
            elif action == 'get-city-pm25':
                data = get_city_pm25(forecast_date, init_date)
                
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
                
            elif action == 'get-city-pm25-timeseries':
                data = get_city_pm25_timeseries(area_id, init_date, adm_lvl)
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
            
            elif action == 'get-location':
                data = get_location()
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
            
            elif action == 'get-data-pm25':
                data = get_adm_pm25(forecast_date, init_date, adm_lvl)
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
            
            elif action == 'get-data-no2':
                data = get_adm_no2(forecast_date, init_date, adm_lvl)
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
            
            elif action == 'get-data-pm25-dash':
                data = get_adm_pm25_dash(forecast_date, init_date, adm_lvl, area_id)
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
            
            elif action == 'get-data-pm25-province-dash':
                data = get_pm25_province_dash(forecast_date, init_date, adm_lvl, area_id)
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
                
            
            elif action == 'get-country-list':
                data = get_country_list()
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
            
            elif action == 'get-province-list':
                data = get_province_list()
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
                
            
            elif action == 'get-daily-average-pm25-timeseries':
                data = get_daily_pm25_time_series(start_date, end_date, area_ids)
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
            
            elif action == 'get-pm25-country':
                data = get_adm_pm25_country(forecast_date, init_date, adm_lvl, area_id)
                if data:
                    return Response(data)
                else:
                    return Response({'error': 'No data found for your request.'}, status=status.HTTP_404_NOT_FOUND)
                


