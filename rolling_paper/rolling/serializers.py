#rolling_api/serializers.py
from rest_framework import serializers
from .models import Rolling


class RollingSerializer(serializers.ModelSerializer) :
    class Meta:
        model = Rolling        # product 모델 사용
        fields = '__all__'            # 모든 필드 포함