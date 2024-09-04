from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Visitor
from django.utils import timezone
from rest_framework import status
from .serializers import RequestDataSerializer

class RequestDataAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RequestDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Data received'}, status=201)
        else:
            return Response(serializer.errors, status=400)

class VisitorCountView(APIView):
    def get(self, request):
        ip_address = request.META.get('REMOTE_ADDR')
        visitor, created = Visitor.objects.get_or_create(ip_address=ip_address)
        
        if not created:
            visitor.visit_count += 1
            visitor.last_visit = timezone.now()
            visitor.save()

        total_visitors = Visitor.objects.count()
        return Response({"total_visitors": total_visitors}, status=status.HTTP_200_OK)
