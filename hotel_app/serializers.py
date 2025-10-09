from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (
    Building, Department, Floor, LocationFamily, LocationType, UserGroup, UserGroupMembership, 
    Location, ServiceRequest, Voucher, GuestComment,
    Notification
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = '__all__'

class UserGroupMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroupMembership
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class LocationFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationFamily
        fields = '__all__'

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'

class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = '__all__'

class LocationFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationFamily
        fields = '__all__'

class LocationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationType
        fields = '__all__'

class ServiceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = '__all__'

class GuestCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestComment
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'created_at']