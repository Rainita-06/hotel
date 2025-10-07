import json
import csv
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LogoutView
from django.db.models import Count
from django.views.generic import TemplateView
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from hotel_app.models import (
    User, Department, UserGroup, UserGroupMembership,
    Location, ServiceRequest, Voucher, GuestComment, Guest,
    Notification  # Add Notification model
)
from hotel_app.serializers import (
    UserSerializer, DepartmentSerializer, UserGroupSerializer,
    UserGroupMembershipSerializer, LocationSerializer,
    ServiceRequestSerializer, GuestCommentSerializer
)
from hotel_app.utils import generate_qr_code, user_in_group, group_required, admin_required, create_notification  # Add create_notification
from .forms import GuestForm
from .models import Guest
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login


# ------------------- Constants -------------------
ADMINS_GROUP = 'Admins'
USERS_GROUP = 'Users'
STAFF_GROUP = 'Staff'


# ------------------- Auth -------------------
class LoginView(TokenObtainPairView):
    """JWT login view"""
    permission_classes = [AllowAny]


class CustomLogoutView(LogoutView):
    """Allow GET request for logout (by redirecting to POST logic)."""
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect('home')


def home(request):
    is_admin = (
        request.user.is_authenticated
        and (request.user.is_superuser or user_in_group(request.user, ADMINS_GROUP))
    )
    return render(request, "home.html", {"is_admin": is_admin})


# ------------------- Helper Functions -------------------
def user_in_group(user, group_name):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name=group_name).exists())


# ------------------- Admin Mixins -------------------
class AdminOnlyView(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict access to Admin users only."""
    def test_func(self):
        return user_in_group(self.request.user, ADMINS_GROUP)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict access to Staff and Admin users only."""
    def test_func(self):
        return (user_in_group(self.request.user, ADMINS_GROUP) or 
                user_in_group(self.request.user, STAFF_GROUP))


# ------------------- API ViewSets -------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]


class UserGroupViewSet(viewsets.ModelViewSet):
    queryset = UserGroup.objects.all()
    serializer_class = UserGroupSerializer
    permission_classes = [IsAuthenticated]


class UserGroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = UserGroupMembership.objects.all()
    serializer_class = UserGroupMembershipSerializer
    permission_classes = [IsAuthenticated]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]


class ServiceRequestViewSet(viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer
    permission_classes = [IsAuthenticated]


class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    permission_classes = [IsAuthenticated]


class GuestCommentViewSet(viewsets.ModelViewSet):
    queryset = GuestComment.objects.all()
    serializer_class = GuestCommentSerializer
    permission_classes = [IsAuthenticated]


# ------------------- Dashboard APIs -------------------
class DashboardOverview(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data = {
            "complaints": ServiceRequest.objects.count(),
            "reviews": GuestComment.objects.count(),
            "vouchers": Voucher.objects.count(),
        }
        return Response(data)


class DashboardComplaints(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        total = ServiceRequest.objects.count()
        open_requests = ServiceRequest.objects.filter(status="open").count()
        closed_requests = ServiceRequest.objects.filter(status="closed").count()
        return Response({"total": total, "open": open_requests, "closed": closed_requests})


class DashboardReviews(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        total = GuestComment.objects.count()
        return Response({"total": total})


# ------------------- Voucher Management -------------------
from django.shortcuts import render
from .models import Voucher

def breakfast_vouchers(request):
    vouchers = Voucher.objects.all()
    return render(request, "dashboard/", {"vouchers": vouchers})


def issue_voucher(request, guest_id):
    """Generate voucher + QR for a guest at check-in"""
    # Check if user has permission to issue vouchers
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        raise PermissionDenied("You don't have permission to issue vouchers.")
    
    guest = get_object_or_404(Guest, id=guest_id)

    if not guest.breakfast_included:
        return render(request, "dashboard/issue_voucher.html", {"error": "Guest does not have breakfast included."})

    voucher, created = Voucher.objects.get_or_create(
        guest_name=guest.full_name,
        expiry_date=guest.checkout_date,
    )
    
    # Set the issued_by field to the current user
    voucher.issued_by = request.user

    if created or not voucher.qr_code:
        # Generate QR code with larger size for better visibility
        qr_data = f"Voucher: {voucher.voucher_code}\nGuest: {voucher.guest_name}"
        voucher.qr_image = generate_qr_code(qr_data, size='xxlarge')
    
    voucher.save()
    
    # Create a notification for the user who issued the voucher
    create_notification(
        recipient=request.user,
        title="Voucher Issued",
        message=f"Voucher for {voucher.guest_name} has been issued successfully.",
        notification_type="voucher",
        related_object=voucher
    )

    return render(request, "dashboard/voucher_detail.html", {"voucher": voucher})


@require_http_methods(["POST"])
def scan_voucher(request, code=None):
    """Validate & redeem QR voucher via POST request."""
    # Check if user has permission to scan vouchers
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)
    
    code = code or request.POST.get("voucher_code")
    try:
        voucher = Voucher.objects.get(voucher_code=code)
    except Voucher.DoesNotExist:
        return JsonResponse({"status": "invalid", "message": "Voucher not found"}, status=404)

    if not voucher.is_valid():
        return JsonResponse({"status": "expired", "message": "Voucher expired or already redeemed"})

    voucher.redeemed = True
    voucher.save()
    
    # Create a notification for the user who scanned the voucher
    create_notification(
        recipient=request.user,
        title="Voucher Scanned",
        message=f"Voucher for {voucher.guest_name} has been scanned successfully.",
        notification_type="voucher",
        related_object=voucher
    )
    
    # Create a notification for the user who issued the voucher (if different)
    if voucher.issued_by and voucher.issued_by != request.user:
        create_notification(
            recipient=voucher.issued_by,
            title="Voucher Redeemed",
            message=f"Voucher for {voucher.guest_name} has been redeemed.",
            notification_type="voucher",
            related_object=voucher
        )

    return JsonResponse({
        "status": "success",
        "guest": voucher.guest_name,
        "scan_id": voucher.id,
    })


def validate_voucher(request):
    """Validate & redeem QR voucher via GET request."""
    # Check if user has permission to validate vouchers
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)
    
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"status": "error", "message": "Code missing"}, status=400)

    try:
        voucher = Voucher.objects.get(voucher_code=code)
    except Voucher.DoesNotExist:
        return JsonResponse({"status": "invalid", "message": "Voucher not found"}, status=404)

    if not voucher.is_valid():
        return JsonResponse({"status": "expired", "message": "Voucher expired or already redeemed"}, status=400)

    # Redeem the voucher
    voucher.redeemed = True
    voucher.save()
    
    # Create a notification for the user who validated the voucher
    create_notification(
        recipient=request.user,
        title="Voucher Validated",
        message=f"Voucher for {voucher.guest_name} has been validated successfully.",
        notification_type="voucher",
        related_object=voucher
    )
    
    # Create a notification for the user who issued the voucher (if different)
    if voucher.issued_by and voucher.issued_by != request.user:
        create_notification(
            recipient=voucher.issued_by,
            title="Voucher Redeemed",
            message=f"Voucher for {voucher.guest_name} has been redeemed.",
            notification_type="voucher",
            related_object=voucher
        )

    return JsonResponse({
        "status": "success",
        "message": f"Voucher for {voucher.guest_name} validated!",
        "guest": voucher.guest_name,
    })


def voucher_report(request):
    # Check if user has permission to view reports
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        raise PermissionDenied("You don't have permission to view voucher reports.")
    
    vouchers = Voucher.objects.all().order_by("-created_at")
    return render(request, "dashboard/voucher_report.html", {"vouchers": vouchers})


def issue_voucher_list(request):
    # Check if user has permission to issue vouchers
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        raise PermissionDenied("You don't have permission to issue vouchers.")
    
    guests = Guest.objects.all()
    return render(request, "dashboard/issue_voucher.html", {"guests": guests})


def scan_voucher_page(request):
    """Render the voucher scanning page (form/QR scanner UI)."""
    # Check if user has permission to scan vouchers
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        raise PermissionDenied("You don't have permission to scan vouchers.")
    
    return render(request, "dashboard/scan_voucher.html")


# ------------------- Base Views -------------------
class BaseNavView(LoginRequiredMixin, TemplateView):
    """Shared base to ensure login and provide navigation context."""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["ADMINS_GROUP"] = ADMINS_GROUP
        context["USERS_GROUP"] = USERS_GROUP
        context["STAFF_GROUP"] = STAFF_GROUP
        context["is_admin"] = user_in_group(user, ADMINS_GROUP)
        context["is_staff"] = user_in_group(user, STAFF_GROUP)
        context["is_user"] = user_in_group(user, USERS_GROUP)
        return context


# ------------------- Template Views -------------------
class HomeView(BaseNavView):
    template_name = 'home.html'


def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log the user in after signup
            return redirect("dashboard:main")  # change to your dashboard homepage
    else:
        form = UserCreationForm()
    return render(request, "auth/signup.html", {"form": form})

class MasterUserView(AdminOnlyView, BaseNavView):
    template_name = 'screens/master_user.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.select_related('userprofile__department').all()
        return context


class MasterLocationView(AdminOnlyView, BaseNavView):
    template_name = 'screens/master_location.html'


class HotelDashboardView(BaseNavView):
    template_name = 'screens/hotel_dashboard.html'


class VoucherPageView(BaseNavView):
    template_name = 'screens/vouchers.html'


class MainDashboardView(BaseNavView):
    template_name = 'dashboard/main.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_users"] = User.objects.count()
        context["total_departments"] = Department.objects.count()
        context["total_locations"] = Location.objects.count()
        context["active_complaints"] = ServiceRequest.objects.filter(status="open").count()
        context["resolved_complaints"] = ServiceRequest.objects.filter(status="closed").count()
        context["vouchers_issued"] = Voucher.objects.count()
        context["vouchers_redeemed"] = Voucher.objects.filter(redeemed=True).count()

        complaint_trends = list(
            ServiceRequest.objects.values("status").order_by("status").annotate(count=Count("id"))
        )
        context["complaint_trends"] = json.dumps(complaint_trends)
        return context



# ------------------- Bulk Actions -------------------
@require_http_methods(['POST'])
def bulk_delete_users(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        ids = data.get('ids', [])
        if not request.user.is_authenticated or not user_in_group(request.user, ADMINS_GROUP):
            return Response({'detail': 'forbidden'}, status=403)
        User.objects.filter(id__in=ids).delete()
        return Response({'deleted': len(ids)})
    except Exception as e:
        return Response({'error': str(e)}, status=400)


def export_users_csv(request):
    if not request.user.is_authenticated or not user_in_group(request.user, ADMINS_GROUP):
        return redirect('login')

    users = User.objects.select_related('userprofile__department').all()
    resp = HttpResponse(content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="users.csv"'
    writer = csv.writer(resp)
    writer.writerow(['id', 'username', 'full_name', 'email', 'department', 'is_active'])
    for u in users:
        dept = u.userprofile.department.name if hasattr(u, 'userprofile') and u.userprofile.department else ''
        writer.writerow([u.id, u.username, u.get_full_name(), u.email, dept, u.is_active])
    return resp

def register_guest(request):
    """Enhanced guest registration with automatic voucher generation and QR code"""
    # Check if user has permission to register guests
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        raise PermissionDenied("You don't have permission to register guests.")
    
    if request.method == "POST":
        form = GuestForm(request.POST)
        if form.is_valid():
            try:
                guest = form.save()
                
                # Generate QR code for guest details
                if not guest.details_qr_code:
                    guest.generate_details_qr_code(size='xxlarge')
                
                # Check if voucher was created
                vouchers_created = guest.vouchers.count()
                
                # Create a notification for the user who registered the guest
                create_notification(
                    recipient=request.user,
                    title="Guest Registered",
                    message=f"Guest {guest.full_name} has been registered successfully.",
                    notification_type="info",
                    related_object=guest
                )
                
                return redirect('dashboard:guest_detail', guest_id=guest.id)
            except Exception as e:
                messages.error(request, f"Error registering guest: {str(e)}")
                return render(request, "dashboard/register_guest.html", {"form": form})
    else:
        form = GuestForm()
    
    return render(request, "dashboard/register_guest.html", {
        "form": form,
        "title": "Register New Guest"
    })


def guest_qr_success(request, guest_id):
    """Display guest details and QR code after successful registration"""
    guest = get_object_or_404(Guest, id=guest_id)
    
    # Generate QR code if it doesn't exist
    if not guest.details_qr_code:
        guest.generate_details_qr_code(size='xxlarge')
    
    # Get associated vouchers
    vouchers = guest.vouchers.all()
    
    # Parse QR data for display
    qr_details = None
    if guest.details_qr_data:
        try:
            qr_details = json.loads(guest.details_qr_data)
        except json.JSONDecodeError:
            qr_details = None
    
    context = {
        'guest': guest,
        'vouchers': vouchers,
        'qr_details': qr_details,
        'title': f'Guest Registration Complete - {guest.full_name}'
    }
    
    return render(request, "dashboard/guest_qr_success.html", context)


@require_http_methods(["POST"])
def generate_guest_qr(request, guest_id):
    """Generate QR code for guest details on demand"""
    # Check if user has permission to generate QR codes
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)
    
    guest = get_object_or_404(Guest, id=guest_id)
    
    try:
        success = guest.generate_details_qr_code()
        if success:
            return JsonResponse({
                'success': True,
                'message': 'QR code generated successfully',
                'qr_url': guest.get_details_qr_url(request)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to generate QR code'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error generating QR code: {str(e)}'
        })
    



from django.shortcuts import render, redirect, get_object_or_404
from .models import Location, LocationFamily, LocationType, Floor, Building
from django.db.models import Q
from django.contrib import messages

# -------------------------------
# Locations List & Filter
# -------------------------------
# def locations_list(request):
#     locations = Location.objects.all()
#     families = LocationFamily.objects.all()
#     types = LocationType.objects.all()
#     floors = Floor.objects.all()
#     buildings = Building.objects.all()

#     # Filters
#     family_filter = request.GET.get('family')
#     type_filter = request.GET.get('type')
#     floor_filter = request.GET.get('floor')
#     building_filter = request.GET.get('building')

#     if family_filter:
#         locations = locations.filter(family_id=family_filter)
#     if type_filter:
#         locations = locations.filter(type_id=type_filter)
#     if floor_filter:
#         locations = locations.filter(floor_id=floor_filter)
#     if building_filter:
#         locations = locations.filter(building_id=building_filter)

#     context = {
#         'locations': locations,
#         'families': families,
#         'types': types,
#         'floors': floors,
#         'buildings': buildings,
#         'selected_family': family_filter,
#         'selected_type': type_filter,
#         'selected_floor': floor_filter,
#         'selected_building': building_filter,
#     }
#     return render(request, 'locations_list.html', context)
from django.core.paginator import Paginator

def locations_list(request):
    locations = Location.objects.all()
    families = LocationFamily.objects.all()
    types = LocationType.objects.all()
    floors = Floor.objects.all()
    buildings = Building.objects.all()
    
    # Filters
    family_filter = request.GET.get('family')
    type_filter = request.GET.get('type')
    floor_filter = request.GET.get('floor')
    building_filter = request.GET.get('building')
    search_query = request.GET.get('search', '').strip()  # remove spaces

    # Apply filters only if values are present
    if family_filter:
        locations = locations.filter(family_id=family_filter)
    if type_filter:
        locations = locations.filter(type_id=type_filter)
    if floor_filter:
        locations = locations.filter(floor_id=floor_filter)
    if building_filter:
        locations = locations.filter(building_id=building_filter)
    if search_query:  # only filter if input is not empty
        locations = locations.filter(name__icontains=search_query)

    # Pagination
    paginator = Paginator(locations, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'locations': page_obj,
        'families': families,
        'types': types,
        'floors': floors,
        'buildings': buildings,
        'selected_family': family_filter,
        'selected_type': type_filter,
        'selected_floor': floor_filter,
        'selected_building': building_filter,
        'search_query': search_query,
        "page_obj": page_obj,
    }
    return render(request, 'dashboard/locations.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import LocationFamily, LocationType


# def location_manage_view(request, family_id):
#     """Main page to manage a single LocationFamily."""
#     family = get_object_or_404(LocationFamily, family_id=family_id)

#     all_location_types = family.types.all()
#     first_three = all_location_types[:3]
#     remaining_count = max(all_location_types.count() - 3, 0)

#     locations_with_status = [
#         {"name": loc.name, "status": "Active" if loc.is_active else "Inactive"}
#         for loc in first_three
#     ]

#     context = {
#         "family": family,
#         "locations": locations_with_status,
#         "remaining_count": remaining_count,
#         # if you store a checklist model, fetch it here.
#         "default_checklist": {"name": "Room Service"},
#     }
#     return render(request, "location_manage.html", context)


# @require_http_methods(["POST"])
# def add_family(request):
#     """
#     Create a new LocationFamily from a form or AJAX POST.
#     Expects a field 'name'.
#     """
#     name = request.POST.get("name", "").strip()
#     if not name:
#         return JsonResponse({"error": "Name is required"}, status=400)

#     family = LocationFamily.objects.create(name=name)
#     return JsonResponse({"success": True, "family_id": family.id, "family_name": family.name})


# def search_families(request):
#     """
#     Returns JSON list of families matching a ?q= search.
#     """
#     query = request.GET.get("q", "").strip()
#     results = LocationFamily.objects.filter(name__icontains=query) if query else []
#     return JsonResponse({
#         "results": [{"id": f.id, "name": f.name} for f in results]
#     })

# app1/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import LocationFamily, LocationType, Checklist
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

# app1/views.py
from django.shortcuts import render, get_object_or_404
from .models import LocationFamily, LocationType, Checklist

def location_manage_view(request, family_id=None):
    """
    If family_id is provided, show that family's details.
    Otherwise, show all families.
    """
    default_checklist = Checklist.objects.first()

    if family_id:
        family = get_object_or_404(LocationFamily, family_id=family_id)
        locations = family.types.all()  # related_name='types'
        remaining_count = max(0, locations.count() - 5)  # show "+N more" if needed
        context = {
            'families': [family],
            'locations': locations[:5],
            'remaining_count': remaining_count,
            'default_checklist': default_checklist
        }
    else:
        families = LocationFamily.objects.prefetch_related('types').all()
        context = {
            'families': families,
            'default_checklist': default_checklist
        }

    return render(request, 'location_management.html', context)



def search_locations(request):
    """
    Search for location types by name.
    Returns JSON results.
    """
    query = request.GET.get('q', '')
    results = []

    if query:
        location_types = LocationType.objects.filter(name__icontains=query)
        for loc in location_types:
            results.append({
                'id': loc.id,
                'name': loc.name,
                'family': loc.family.name,
                'status': 'Active' if loc.is_active else 'Inactive',
            })
    return JsonResponse({'results': results})


@csrf_exempt
def add_family(request):
    """
    Add a new location family via AJAX.
    """
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Name cannot be empty.'})

        family, created = LocationFamily.objects.get_or_create(name=name)
        return JsonResponse({'success': True, 'family_id': family.id})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@admin_required
def bulk_import_locations(request):
    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]
        import csv
        import io
        decoded_file = io.TextIOWrapper(csv_file.file, encoding='utf-8')
        reader = csv.DictReader(decoded_file)
        for row in reader:
            Location.objects.create(
                name=row.get('name'),
                room_no=row.get('room_no'),
                pavilion=row.get('pavilion'),
                capacity=row.get('capacity') or None,
                family_id=row.get('family_id') or None,
                type_id=row.get('type_id') or None,
                floor_id=row.get('floor_id') or None,
                building_id=row.get('building_id') or None
            )
        messages.success(request, "CSV imported successfully!")
        return redirect("locations_list")
    messages.error(request, "No file selected!")
    return redirect("locations_list")


import csv
from django.http import HttpResponse
from .models import Location

# @login_required
# def export_locations_csv(request):
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = 'attachment; filename="locations.csv"'

#     writer = csv.writer(response)
#     # Write header
#     writer.writerow(['Name', 'Room No', 'Pavilion', 'Capacity', 'Family', 'Type', 'Floor', 'Building'])

#     # Write data
#     locations = Location.objects.all()
#     for loc in locations:
#         writer.writerow([
#             loc.name,
#             loc.room_no,
#             loc.pavilion,
#             loc.capacity,
#             loc.family.name if loc.family else '',
#             loc.type.name if loc.type else '',
#             loc.floor.floor_number if loc.floor else '',
#             loc.building.name if loc.building else ''
#         ])

#     return response

@admin_required
def export_locations_csv(request):
    import csv
    from django.http import HttpResponse
    from .models import Location

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="locations.csv"'

    writer = csv.writer(response)
    # Write header
    writer.writerow(['Name', 'Room No', 'Pavilion', 'Capacity', 'Family', 'Type', 'Floor', 'Building'])

    # Write data safely
    locations = Location.objects.all()
    for loc in locations:
        writer.writerow([
            loc.name,
            loc.room_no,
            loc.pavilion,
            loc.capacity,
            getattr(loc, 'family', None) and getattr(loc.family, 'name', '') or '',
            getattr(loc, 'type', None) and getattr(loc.type, 'name', '') or '',
            getattr(loc, 'floor', None) and getattr(loc.floor, 'floor_number', '') or '',
            getattr(loc, 'building', None) and getattr(loc.building, 'name', '') or ''
        ])

    return response


# -------------------------------
# Add/Edit Location
# -------------------------------
def location_form(request, location_id=None):
    if location_id:
        location = get_object_or_404(Location, pk=location_id)
    else:
        location = None

    families = LocationFamily.objects.all()
    types = LocationType.objects.all()
    floors = Floor.objects.all()
    buildings = Building.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        family = request.POST.get('family') or None
        loc_type = request.POST.get('type') or None
        floor = request.POST.get('floor') or None
        building = request.POST.get('building') or None
        room_no = request.POST.get('room_no')
        pavilion = request.POST.get('pavilion')
        capacity = request.POST.get('capacity') or None

        if location:
            location.name = name
            location.family_id = family
            location.type_id = loc_type
            location.floor_id = floor
            location.building_id = building
            location.room_no = room_no
            location.pavilion = pavilion
            location.capacity = capacity
            location.save()
        else:
            Location.objects.create(
                name=name,
                family_id=family,
                type_id=loc_type,
                floor_id=floor,
                building_id=building,
                room_no=room_no,
                pavilion=pavilion,
                capacity=capacity
            )
        messages.success(request,f"Location {name} successfully!")
        return redirect('locations_list')

    context = {
        'location': location,
        'families': families,
        'types': types,
        'floors': floors,
        'buildings': buildings,
    }
    
    return render(request, 'location_form.html', context)


# -------------------------------
# Delete Location
# -------------------------------
def location_delete(request, location_id):
    location = get_object_or_404(Location, pk=location_id)
    location_name=location.name
    location.delete()
    messages.success(request,f"Location {location_name} deleted successfully")
    return redirect('locations_list')
# -------------------------------
# Location Families
# -------------------------------
def families_list(request):
    families = LocationFamily.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        LocationFamily.objects.create(name=name)
        messages.success(request, "Family added successfully!")
        return redirect("locations_list")
    return families

def family_delete(request, family_id):
    family = get_object_or_404(LocationFamily, pk=family_id)
    family.delete()
    messages.success(request, "Family deleted successfully!")
    return redirect("location_manage_view")


# -------------------------------
# Location Types
# -------------------------------
# def types_list(request):
#     types = LocationType.objects.all()
#     if request.method == "POST":
#         name = request.POST.get("name")
#         LocationType.objects.create(name=name)
#         messages.success(request, "Type added successfully!")
#         return render(request,"types.html",{"types":types})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import LocationType

def types_list(request):
    types = LocationType.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            LocationType.objects.create(name=name)
            messages.success(request, "Type added successfully!")
            return redirect("types_list")  # redirect after POST to avoid form resubmission
    return render(request, "types.html", {"types": types})


def type_delete(request, type_id):
    t = get_object_or_404(LocationType, pk=type_id)
    t.delete()
    messages.success(request, "Type deleted successfully!")
    return redirect("types_list")


# -------------------------------
# Floors
# -------------------------------
# def floors_list(request):
#     floors = Floor.objects.all()
#     if request.method == "POST":
#         name = request.POST.get("floor_name")
#         floor_number = request.POST.get("floor_number") or 0
#         Floor.objects.create(floor_name=name, floor_number=floor_number)
#         messages.success(request, "Floor added successfully!")
#         return redirect("locations_list")
#     return floors

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Building, Floor

def floors_list(request):
    search_query = request.GET.get("search", "")
    
    # Start with all floors
    floors = Floor.objects.all()
    
    if search_query:
        floors = floors.filter(
            Q(floor_name__icontains=search_query) |
            Q(floor_number__icontains=search_query) |
            Q(building__name__icontains=search_query)
        )
    
    buildings = Building.objects.all()  # if needed in filter dropdowns
    
    context = {
        "floors": floors,
        "search_query": search_query,
        "buildings": buildings,
    }
    return render(request, "floors.html", context)

# def floor_delete(request, floor_id):
#     f = get_object_or_404(Floor, pk=floor_id)
#     f.delete()
#     messages.success(request, "Floor deleted successfully!")
#     return redirect("locations_list")
def floor_form(request, floor_id=None):
    floor = get_object_or_404(Floor, pk=floor_id) if floor_id else None
    
    if request.method == "POST":
        name = request.POST.get("floor_name")
        floor_number = request.POST.get("floor_number") or 0
        building_id = request.POST.get("building_id")
        rooms = request.POST.get("rooms") or 0
        occupancy = request.POST.get("occupancy") or 0
        is_active = request.POST.get("is_active") == "on"

        building = get_object_or_404(Building, pk=building_id)

        if floor:
            floor.floor_name = name
            floor.floor_number = floor_number
            floor.building = building
            floor.rooms = rooms
            floor.occupancy = occupancy
            floor.is_active = is_active
            floor.save()
            messages.success(request, "Floor updated successfully!")
        else:
            Floor.objects.create(
                floor_name=name,
                floor_number=floor_number,
                building=building,
                rooms=rooms,
                occupancy=occupancy,
                is_active=is_active,
            )
            messages.success(request, "Floor added successfully!")
        return redirect("floors_list")

    buildings = Building.objects.all()
    return render(request, "floor_form.html", {"floor": floor, "buildings": buildings})


def floor_delete(request, floor_id):
    floor = get_object_or_404(Floor, pk=floor_id)
    floor.delete()
    messages.success(request, "Floor deleted successfully!")
    return redirect("floors_list")


# -------------------------------
# Buildings
# -------------------------------
def buildings_list(request):
    buildings = Building.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        Building.objects.create(name=name)
        messages.success(request, "Building added successfully!")
        return redirect("locations_list")
    return buildings

def building_delete(request, building_id):
    b = get_object_or_404(Building, pk=building_id)
    b.delete()
    messages.success(request, "Building deleted successfully!")
    return redirect("locations_list")
# -------------------------------
# Location Families
# -------------------------------
def family_form(request, family_id=None):
    if family_id:
        family = get_object_or_404(LocationFamily, pk=family_id)
    else:
        family = None

    if request.method == "POST":
        name = request.POST.get("name")

        if family:
            family.name = name
            family.save()
            messages.success(request, "Family updated successfully!")
        else:
            LocationFamily.objects.create(name=name)
            messages.success(request, "Family added successfully!")

        return redirect("location_manage_view")

    context = {"family": family}
    return render(request, "family_form.html", context)





# -------------------------------
# # Location Types
# # -------------------------------
# def type_form(request, type_id=None):
#     families = LocationFamily.objects.all() 
#     if type_id:
#         loc_type = get_object_or_404(LocationType, pk=type_id)
#     else:
#         loc_type = None

#     if request.method == "POST":
#         name = request.POST.get("name")

#         if loc_type:
#             loc_type.name = name
#             loc_type.save()
#             messages.success(request, "Type updated successfully!")
#         else:
#             LocationType.objects.create(name=name)
#             messages.success(request, "Type added successfully!")

#         return redirect("types_list")

#     context = {"loc_type": loc_type,"families":families}
#     return render(request, "type_form.html", context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import LocationType, LocationFamily

def type_form(request, type_id=None):
    # If editing
    loc_type = get_object_or_404(LocationType, pk=type_id) if type_id else None

    # All families for dropdown
    families = LocationFamily.objects.all()

    if request.method == "POST":
        name = request.POST.get("name")
        family_id = request.POST.get("family")

        if not family_id:
            messages.error(request, "Please select a family!")
            return render(request, "type_form.html", {"type": loc_type, "families": families})

        family = get_object_or_404(LocationFamily, pk=family_id)

        if loc_type:
            # Update existing
            loc_type.name = name
            loc_type.family = family
            loc_type.save()
            messages.success(request, "Type updated successfully!")
        else:
            # Create new
            LocationType.objects.create(name=name, family=family)
            messages.success(request, "Type added successfully!")

        return redirect("types_list")

    return render(request, "type_form.html", {"type": loc_type, "families": families})


# views.py
from django.shortcuts import render
from .models import Building

def building_cards(request):
    buildings = Building.objects.all()
    return render(request, 'building.html', {'buildings': buildings})




# -------------------------------
# Floors
# -------------------------------
# def floor_form(request, floor_id=None):
#     if floor_id:
#         floor = get_object_or_404(Floor, pk=floor_id)
#     else:
#         floor = None
    
#     if request.method == "POST":
#         name = request.POST.get("floor_name")
#         floor_number = request.POST.get("floor_number") or 0
#         building_id = request.POST.get('building_id')
#         building = Building.objects.get(building_id=building_id)
#         if floor:
#             floor.floor_name = name
#             floor.floor_number = floor_number
#             floor.building=building
#             floor.save()
#             messages.success(request, "Floor updated successfully!")
#         else:
#             Floor.objects.create(floor_name=name, floor_number=floor_number,building=building)
#             messages.success(request, "Floor added successfully!")

#         return redirect("locations_list")
#     buildings = Building.objects.all()
        

#     context = {"floor": floor,  'buildings': buildings}
#     return render(request, "floor_form.html", context)





# -------------------------------
# Buildings
# -------------------------------
# def building_form(request, building_id=None):
#     if building_id:
#         building = get_object_or_404(Building, pk=building_id)
        
#     else:
#         building = None

#     if request.method == "POST":
#         name = request.POST.get("name")

#         if building:
#             building.name = name
#             building.save()
#             messages.success(request, "Building updated successfully!")
#         else:
#             Building.objects.create(name=name)
#             messages.success(request, "Building added successfully!")

#         return redirect("locations_list")

#     context = {"building": building}
#     return render(request, "building_form.html", context)

def building_form(request, building_id=None):
    if building_id:
        building = get_object_or_404(Building, pk=building_id)
    else:
        building = None

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        status = request.POST.get("status", "active")
        image = request.FILES.get("image")

        if building:
            building.name = name
            building.description = description
            building.status = status
            if image:
                building.image = image
            building.save()
            messages.success(request, "Building updated successfully!")
        else:
            Building.objects.create(
                name=name, description=description, status=status, image=image
            )
            messages.success(request, "Building added successfully!")

        return redirect("building_cards")

    return render(request, "building_form.html", {"building": building})

from django.shortcuts import get_object_or_404, redirect
from .models import Building

def upload_building_image(request, building_id):
    building = get_object_or_404(Building, building_id=building_id)
    if request.method == "POST" and request.FILES.get("image"):
        building.image = request.FILES["image"]
        building.save()
        messages.success(request, "Image uploaded successfully!")
    return redirect("building_cards")  # redirect to the building cards page



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import LocationFamily, LocationType, Floor, Building
def family_add(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            LocationFamily.objects.create(name=name)
            messages.success(request, "Family added successfully!")
            return redirect("location_manage_view")
    return render(request, "family_form.html")


def family_edit(request, family_id):
    family = get_object_or_404(LocationFamily, pk=family_id)
    if request.method == "POST":
        family.name = request.POST.get("name")
        family.save()
        messages.success(request, "Family updated successfully!")
        return redirect("location_manage_view")
    return render(request, "family_form.html", {"family": family})

def type_add(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            LocationType.objects.create(name=name)
            messages.success(request, "Type added successfully!")
            return redirect("types_list")
    return render(request, "type_form.html")


def type_edit(request, type_id):
    t = get_object_or_404(LocationType, pk=type_id)
    if request.method == "POST":
        t.name = request.POST.get("name")
        t.save()
        messages.success(request, "Type updated successfully!")
        return redirect("types_list")
    return render(request, "type_form.html", {"type": t})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import LocationType, LocationFamily

def type_add(request):
    families = LocationFamily.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        family_id = request.POST.get("family")

        if name and family_id:
            family = get_object_or_404(LocationFamily, pk=family_id)
            LocationType.objects.create(name=name, family=family)
            messages.success(request, "Type added successfully!")
            return redirect("types_list")

    return render(request, "type_form.html", {"families": families})


def type_edit(request, type_id):
    t = get_object_or_404(LocationType, pk=type_id)
    families = LocationFamily.objects.all()

    if request.method == "POST":
        t.name = request.POST.get("name")
        family_id = request.POST.get("family")

        if family_id:
            t.family = get_object_or_404(LocationFamily, pk=family_id)

        t.save()
        messages.success(request, "Type updated successfully!")
        return redirect("types_list")

    return render(request, "type_form.html", {"type": t, "families": families})

def floor_add(request):
    if request.method == "POST":
        name = request.POST.get("floor_name")
        floor_number = request.POST.get("floor_number") or 0
        Floor.objects.create(floor_name=name, floor_number=floor_number)
        messages.success(request, "Floor added successfully!")
        return redirect("floors_list")
    return render(request, "floor_form.html")


def floor_edit(request, floor_id):
    floor = get_object_or_404(Floor, pk=floor_id)
    if request.method == "POST":
        floor.floor_name = request.POST.get("floor_name")
        floor.floor_number = request.POST.get("floor_number") or 0
        floor.save()
        messages.success(request, "Floor updated successfully!")
        return redirect("floors_list")
    return render(request, "floor_form.html", {"floor": floor})
def building_add(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Building.objects.create(name=name)
            messages.success(request, "Building added successfully!")
            return redirect("building_cards")
    return render(request, "building_form.html")



def building_edit(request, building_id):
    building = get_object_or_404(Building, pk=building_id)
    if request.method == "POST":
        building.name = request.POST.get("name")
        building.save()
        messages.success(request, "Building updated successfully!")
        return redirect("building_cards")
    return render(request, "building_form.html", {"building": building})


from django.shortcuts import render, redirect, get_object_or_404
from .models import RequestType, RequestFamily, WorkFamily, Workflow, Checklist
from django.contrib import messages
# -------------------------
# List Request Types
# -------------------------
def request_types_list(request):
    request_types = RequestType.objects.all()

    # Optional: filter by request_family or work_family
    family_id = request.GET.get('request_family')
    work_family_id = request.GET.get('work_family')
    request_families = RequestFamily.objects.all()

    if family_id:
        request_types = request_types.filter(request_family_id=family_id)
    if work_family_id:
        request_types = request_types.filter(work_family_id=work_family_id)

    families = RequestFamily.objects.all()
    work_families = WorkFamily.objects.all()

    context = {
        'request_types': request_types,
        'families': families,
        'work_families': work_families,
        'selected_family': family_id,
        'selected_work_family': work_family_id,
        "request_families": request_families,
    }
    return render(request, 'request_types_list.html', context)


# -------------------------
# Add Request Type
# -------------------------
def request_type_add(request):
    families = RequestFamily.objects.all()
    work_families = WorkFamily.objects.all()
    workflows = Workflow.objects.all()
    checklists = Checklist.objects.all()
    request_families = RequestFamily.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        workflow_id = request.POST.get('workflow')
        work_family_id = request.POST.get('work_family')
        request_family_id = request.POST.get('request_family')
        checklist_id = request.POST.get('checklist')
        active = True if request.POST.get('active') == 'on' else False

        workflow = Workflow.objects.get(pk=workflow_id) if workflow_id else None
        work_family = WorkFamily.objects.get(pk=work_family_id) if work_family_id else None
        request_family = RequestFamily.objects.get(pk=request_family_id) if request_family_id else None
        checklist = Checklist.objects.get(pk=checklist_id) if checklist_id else None

        RequestType.objects.create(
            name=name,
            workflow=workflow,
            work_family=work_family,
            request_family=request_family,
            checklist=checklist,
            active=active
        )
        messages.success(request,f"Request {name} is added successfully!")
        return redirect('request_types_list')

    context = {
        'families': families,
        'work_families': work_families,
        'workflows': workflows,
        'checklists': checklists,
        "request_families": request_families,
        'request_type': None
    }
    return render(request, 'request_type_form.html', context)


# -------------------------
# Edit Request Type
# -------------------------
def request_type_edit(request, request_type_id):
    request_type = get_object_or_404(RequestType, pk=request_type_id)
    families = RequestFamily.objects.all()
    work_families = WorkFamily.objects.all()
    workflows = Workflow.objects.all()
    checklists = Checklist.objects.all()
    request_families = RequestFamily.objects.all()

    if request.method == 'POST':
        request_type.name = request.POST.get('name')
        workflow_id = request.POST.get('workflow')
        work_family_id = request.POST.get('work_family')
        request_family_id = request.POST.get('request_family')
        checklist_id = request.POST.get('checklist')
        request_type.active = True if request.POST.get('active') == 'on' else False

        request_type.workflow = Workflow.objects.get(pk=workflow_id) if workflow_id else None
        request_type.work_family = WorkFamily.objects.get(pk=work_family_id) if work_family_id else None
        request_type.request_family = RequestFamily.objects.get(pk=request_family_id) if request_family_id else None
        request_type.checklist = Checklist.objects.get(pk=checklist_id) if checklist_id else None

        request_type.save()
        messages.success(request,f"Request {request_type.name} is updated successfully!")
        return redirect('request_types_list')

    context = {
        'request_type': request_type,
        'families': families,
        'work_families': work_families,
        'workflows': workflows,
        'checklists': checklists,
        "request_families": request_families,
    }
    return render(request, 'request_type_form.html', context)


# -------------------------
# Delete Request Type
# -------------------------
def request_type_delete(request, request_type_id):
    request_type = get_object_or_404(RequestType, pk=request_type_id)
    request_type_name=request_type.name
    request_type.delete()
    messages.success(request,f"Request {request_type_name} is added successfully!")
    return redirect('request_types_list')
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Checklist, ChecklistItem, Location
from django.contrib import messages
# --- Checklists ---

@admin_required
def checklist_list(request):
    checklists = Checklist.objects.annotate(
        required_items_count=Count('checklistitem', filter=Q(checklistitem__required=True))
    )

    # Active checklists are those with at least one required item
    active_checklists_count = checklists.filter(required_items_count__gt=0).count()

    return render(request, "list.html", {"checklists": checklists,"active_checklists_count":active_checklists_count})

@admin_required
def add_checklist(request):
    locations = Location.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        location_id = request.POST.get("location")
        location = Location.objects.get(pk=location_id) if location_id else None
        Checklist.objects.create(name=name, location=location)
        messages.success(request,f"Checklist {name} added successfully!")
        return redirect("checklist_list")
    return render(request, "add_edit.html", {"locations": locations})

@admin_required
def edit_checklist(request, checklist_id):
    checklist = get_object_or_404(Checklist, checklist_id=checklist_id)
    locations = Location.objects.all()
    if request.method == "POST":
        checklist.name = request.POST.get("name")
        location_id = request.POST.get("location")
        checklist.location = Location.objects.get(pk=location_id) if location_id else None
        checklist.save()
        messages.success(request,f"Checklist {checklist.name} updated successfully!")
        return redirect("checklist_list")
    return render(request, "add_edit.html", {"checklist": checklist, "locations": locations})

@admin_required
def delete_checklist(request, checklist_id):
    checklist = get_object_or_404(Checklist, checklist_id=checklist_id)
    checklist_name=checklist.name
    checklist.delete()
    messages.success(request,f"Checklist {checklist_name} added successfully!")
    return redirect("checklist_list")

# --- Checklist Items ---

@admin_required
def add_item(request, checklist_id):
    checklist = get_object_or_404(Checklist, checklist_id=checklist_id)
    if request.method == "POST":
        label = request.POST.get("label")
        required = bool(request.POST.get("required"))
        ChecklistItem.objects.create(checklist=checklist, label=label, required=required)
        messages.success(request,f"Item {label} added successfully!")
        return redirect("checklist_list")
    return render(request, "add_item.html", {"checklist": checklist})

@admin_required
def edit_item(request, item_id):
    item = get_object_or_404(ChecklistItem, item_id=item_id)
    if request.method == "POST":
        item.label = request.POST.get("label")
        item.required = bool(request.POST.get("required"))
        item.save()
        messages.success(request,f"Item {item.label} updated successfully!")
        return redirect("checklist_list")
    return render(request, "edit_item.html", {"item": item})

@admin_required
def delete_item(request, item_id):
    item = get_object_or_404(ChecklistItem, item_id=item_id)
    item_label=item.label
    item.delete()
    messages.success(request,f"Item  {item_label} deleted successfully!")
    return redirect("checklist_list")
    return render(request, "dashboard/register_guest.html", {"form": form})
