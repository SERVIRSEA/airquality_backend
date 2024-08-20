from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import RequestDataSerializer

class RequestDataAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RequestDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Data received'}, status=201)
        else:
            return Response(serializer.errors, status=400)
