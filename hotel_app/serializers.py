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


# class BreakfastVoucherSerializer(serializers.ModelSerializer):
#     qr_absolute_url = serializers.SerializerMethodField()

#     class Meta:
#         model = Voucher
#         fields = [
#             'id', 'voucher_code', 'guest_name', 'phone_number', 'country_code',
#             'room_no', 'check_in_date', 'check_out_date', 'adults', 'kids',
#             'include_breakfast', 'qr_code_image', 'qr_absolute_url'
#         ]

#     def get_qr_absolute_url(self, obj):
#         request = self.context.get('request')
#         if obj.qr_code_image and request:
#             return request.build_absolute_uri(obj.qr_code_image.url)
#         return None
from rest_framework import serializers
from .models import Voucher

class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = "__all__"
        read_only_fields = ["voucher_code", "quantity", "created_at", "scan_count", "redeemed", "redeemed_at", "valid_dates", "scan_history"]

# serializers.py
from rest_framework import serializers
from .models import GymMember, GymVisit
import base64

class GymMemberSerializer(serializers.ModelSerializer):
    qr_code_base64 = serializers.SerializerMethodField()

    class Meta:
        model = GymMember
        fields = "__all__"

    def validate(self, data):
        """Prevent member creation when password ≠ confirm_password"""
        if data.get("password") != data.get("confirm_password"):
            raise serializers.ValidationError("❌ Password and Confirm Password do not match.")
        return data

    def get_qr_code_base64(self, obj):
        """Return Base64 QR image string"""
        try:
            if obj.qr_code_image:
                with obj.qr_code_image.open('rb') as image_file:
                    encoded = base64.b64encode(image_file.read()).decode('utf-8')
                    return f"data:image/png;base64,{encoded}"
        except Exception:
            return None
        return None


class GymVisitSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)
    member_code = serializers.CharField(source="member.customer_code", read_only=True)

    class Meta:
        model = GymVisit
        fields = "__all__"
