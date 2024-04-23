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
            'get-pcd-data-table'
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