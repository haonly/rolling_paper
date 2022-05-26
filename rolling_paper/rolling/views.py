from django.shortcuts import render
from rest_framework.response import Response
from .models import Rolling
from rest_framework.views import APIView
from .serializers import RollingSerializer


class RollingAPI(APIView):
    def get(self, request):
        queryset = Rolling.objects.all()
        print(queryset)
        serializer = RollingSerializer(queryset, many=True)
        return Response(serializer.data)

# Create your views here.
