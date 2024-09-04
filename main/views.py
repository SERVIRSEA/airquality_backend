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
    # Accept only POST requests
    def post(self, request):
        ip_address = request.data.get('ip')

        if not ip_address:
            return Response({"error": "IP address is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create visitor based on IP address
        visitor, created = Visitor.objects.get_or_create(ip_address=ip_address)

        # Check if the visitor's last visit was on a different day
        if visitor.last_visit.date() < timezone.now().date():
            visitor.visit_count += 1  # Increment the visit count for a new day
            visitor.last_visit = timezone.now()  # Update the last visit time
            visitor.save()

        # Get the total number of visitors
        total_visitors = Visitor.objects.count()

        return Response({"total_visitors": total_visitors}, status=status.HTTP_200_OK)