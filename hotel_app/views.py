import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Guest, Review
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
import json

from django.contrib.auth import login

from hotel_app.utils import  admin_required
def home(request):
    """Home page view"""
    return render(request, 'home.html')

def feedback_form(request):
    """Display the feedback form"""
    return render(request, 'feedback_form.html')

@csrf_exempt
def submit_feedback(request):
    """Handle feedback submission"""
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            # Extract guest information
            guest_name = data.get('guest_name', '')
            room_number = data.get('room_number', '')
            email = data.get('email', '')
            phone = data.get('phone', '')
            
            # Extract feedback data
            overall_rating = data.get('overall_rating', 0)
            cleanliness_rating = data.get('cleanliness_rating', 0)
            staff_rating = data.get('staff_rating', 0)
            recommend = data.get('recommend', '')
            comments = data.get('comments', '')
            
            # Create or get guest
            guest = None
            if guest_name or room_number:
                # Try to find existing guest
                try:
                    if room_number:
                        guest = Guest.objects.get(room_number=room_number)
                    else:
                        guest = Guest.objects.get(full_name=guest_name)
                except Guest.DoesNotExist:
                    # Create new guest
                    guest = Guest.objects.create(
                        full_name=guest_name,
                        room_number=room_number,
                        email=email,
                        phone=phone
                    )
            
            # Create review
            # Format all ratings into the comment field
            full_comment = comments
            if full_comment:
                full_comment += "\n\n"
            else:
                full_comment = ""
            
            full_comment += f"Overall Rating: {overall_rating}/5\n"
            full_comment += f"Cleanliness Rating: {cleanliness_rating}/5\n"
            full_comment += f"Staff Service Rating: {staff_rating}/5\n"
            full_comment += f"Recommendation: {recommend}"
            
            review = Review.objects.create(
                guest=guest,
                rating=overall_rating,
                comment=full_comment
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your feedback!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'There was an error submitting your feedback. Please try again.'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

def signup_view(request):
    """Handle user signup"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard:main')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


from rest_framework import viewsets, filters
from .models import LocationFamily, Location,Building,Floor,LocationType
from .serializers import   BuildingSerializer, FloorSerializer, LocationFamilySerializer, LocationSerializer, LocationTypeSerializer
class LocationFamilyViewSet(viewsets.ModelViewSet):
    queryset = LocationFamily.objects.all()
    serializer_class = LocationFamilySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['family_id', 'name']
    ordering = ['family_id']

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']

class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']

class FloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['floor_name']


class LocationTypeViewSet(viewsets.ModelViewSet):
    queryset = LocationType.objects.all()
    serializer_class = LocationTypeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']

# from rest_framework import viewsets, status, filters
# from rest_framework.decorators import action, api_view
# from rest_framework.response import Response
# from django.shortcuts import get_object_or_404
# from .models import Voucher
# from .serializers import BreakfastVoucherSerializer
# from django.utils import timezone

# # ------------------------------
# # Voucher CRUD + Check-in/Checkout
# # ------------------------------
# class BreakfastVoucherViewSet(viewsets.ModelViewSet):
#     queryset = Voucher.objects.all().order_by('-check_in_date')
#     serializer_class = BreakfastVoucherSerializer
#     filter_backends = [filters.SearchFilter, filters.OrderingFilter]
#     search_fields = ['guest_name', 'voucher_code', 'room_no']

#     # --------------------------
#     # Checkout Endpoint
#     # --------------------------
#     @action(detail=True, methods=['post'])
#     def checkout(self, request, pk=None):
#         voucher = self.get_object()
#         if voucher.check_out_date:
#             return Response({"detail": "Already checked out"}, status=status.HTTP_400_BAD_REQUEST)
#         voucher.check_out_date = request.data.get('check_out_date') or timezone.localdate()
#         voucher.save()
#         serializer = self.get_serializer(voucher, context={'request': request})
#         return Response(serializer.data)

# # ------------------------------
# # Validate Voucher (QR scan)
# # ------------------------------
# @api_view(['GET'])
# def validate_voucher(request):
#     code = request.GET.get('code')
#     if not code:
#         return Response({"valid": False, "message": "Voucher code missing"}, status=status.HTTP_400_BAD_REQUEST)
    
#     try:
#         voucher = Voucher.objects.get(voucher_code=code)
#         return Response({
#             "valid": True,
#             "guest_name": voucher.guest_name,
#             "room_no": voucher.room_no,
#             "check_in_date": voucher.check_in_date,
#             "check_out_date": voucher.check_out_date,
#             "include_breakfast": voucher.include_breakfast,
#             "qr_code_url": request.build_absolute_uri(voucher.qr_code_image.url) if voucher.qr_code_image else None
#         })
#     except Voucher.DoesNotExist:
#         return Response({"valid": False, "message": "Voucher not found"}, status=status.HTTP_404_NOT_FOUND)


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
    locations = locations.order_by('-location_id')
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
        families = LocationFamily.objects.prefetch_related('types').all().order_by('-family_id')
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


# @admin_required
# def bulk_import_locations(request):
#     if request.method == "POST" and request.FILES.get("csv_file"):
#         csv_file = request.FILES["csv_file"]
#         import csv
#         import io
#         decoded_file = io.TextIOWrapper(csv_file.file, encoding='utf-8')
#         reader = csv.DictReader(decoded_file)
#         for row in reader:
#             Location.objects.create(
#                 name=row.get('name'),
#                 room_no=row.get('room_no'),
#                 pavilion=row.get('pavilion'),
#                 capacity=row.get('capacity') or None,
#                 family_id=row.get('family_id') or None,
#                 type_id=row.get('type_id') or None,
#                 floor_id=row.get('floor_id') or None,
#                 building_id=row.get('building_id') or None
#             )
#         messages.success(request, "CSV imported successfully!")
#         return redirect("locations_list")
#     messages.error(request, "No file selected!")
#     return redirect("locations_list")
from io import TextIOWrapper
import csv
from django.contrib import messages
from django.shortcuts import redirect
# from .models import Location, Family, Type, Floor, Building
from .models import Location, Floor, Building

def bulk_import_locations(request):
    """Upload CSV and create Location entries"""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, "Please upload a CSV file.")
            return redirect('locations_list')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Invalid file format. Please upload a .csv file.")
            return redirect('locations_list')

        try:
            file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.DictReader(file_data)
            count = 0

            for row in reader:
                name = row.get('name')
                family_id = row.get('family_id')
                type_id = row.get('type_id')
                floor_id = row.get('floor_id')
                building_id = row.get('building_id')
                status = row.get('status', 'Active')
                description = row.get('description', '')

                if not all([name, family_id, type_id, floor_id, building_id]):
                    continue  # Skip incomplete rows

                # Create the Location object using foreign key IDs
                Location.objects.create(
                    name=name,
                    family_id=family_id,
                    type_id=type_id,
                    floor_id=floor_id,
                    building_id=building_id,
                    status=status,
                    description=description
                )
                count += 1

            messages.success(request, f"✅ Successfully imported {count} locations.")
        except Exception as e:
            messages.error(request, f"❌ Error while importing: {str(e)}")

        return redirect('locations_list')

    return redirect('locations_list')


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
    status = request.POST.get('status', 'active')  # Default to 'active' (match model storage)
    description = request.POST.get('description', '')

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
            location.status = status
            location.description = description
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
                status=status,
                    description=description,
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
    types = LocationType.objects.all().order_by('-type_id')
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
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from .models import Building, Floor

def floors_list(request):
    search_query = request.GET.get("search", "")
    
    # Start with all floors
    floors = Floor.objects.all().order_by('-floor_id')
    
    if search_query:
        floors = floors.filter(
            Q(floor_name__icontains=search_query) |
            Q(floor_number__icontains=search_query) |
            Q(building__name__icontains=search_query)
        )
    
    # Pagination: 10 floors per page
    paginator = Paginator(floors, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    buildings = Building.objects.all()  # if needed in filter dropdowns
    
    context = {
        "floors": page_obj,  # use page_obj in template
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
    buildings = Building.objects.all().order_by('-building_id')
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

import csv
from io import TextIOWrapper
from django.shortcuts import redirect
from django.contrib import messages
from .models import Building, Floor, LocationFamily, LocationType, Location


# -------------------------------
# BULK IMPORT: BUILDINGS
# -------------------------------
def bulk_import_buildings(request):
    """Upload CSV and create Building entries"""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, "Please upload a CSV file.")
            return redirect('building_cards')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Invalid file format. Please upload a .csv file.")
            return redirect('building_cards')

        try:
            file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.DictReader(file_data)
            count = 0

            for row in reader:
                name = row.get('name')
                description = row.get('description', '')
                status = row.get('status', 'Active')

                if not name:
                    continue  # Skip incomplete rows

                Building.objects.create(
                    name=name,
                    description=description,
                    status=status
                )
                count += 1

            messages.success(request, f"✅ Successfully imported {count} buildings.")
        except Exception as e:
            messages.error(request, f"❌ Error while importing buildings: {str(e)}")

        return redirect('building_cards')

    return redirect('building_cards')


# -------------------------------
# BULK IMPORT: FLOORS
# -------------------------------
def bulk_import_floors(request):
    """Upload CSV and create Floor entries"""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, "Please upload a CSV file.")
            return redirect('floors_list')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Invalid file format. Please upload a .csv file.")
            return redirect('floors_list')

        try:
            file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.DictReader(file_data)
            count = 0

            for row in reader:
                floor_name = row.get('floor_name')
                building_id = row.get('building_id')
                floor_number = row.get('floor_number') or 0
                rooms = row.get('rooms') or 0
                occupancy = row.get('occupancy') or 0
                is_active = row.get('is_active', 'True').lower() in ['true', '1', 'yes']

                if not floor_name or not building_id:
                    continue

                Floor.objects.create(
                    floor_name=floor_name,
                    floor_number=floor_number,
                    building_id=building_id,
                    rooms=rooms,
                    occupancy=occupancy,
                    is_active=is_active
                )
                count += 1

            messages.success(request, f"✅ Successfully imported {count} floors.",extra_tags="floor_import")
        except Exception as e:
            messages.error(request, f"❌ Error while importing floors: {str(e)}",extra_tags="floor_import")

        return redirect('floors_list')

    return redirect('floors_list')


# -------------------------------
# BULK IMPORT: LOCATION FAMILIES
# -------------------------------
def bulk_import_families(request):
    """Upload CSV and create LocationFamily entries"""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, "Please upload a CSV file.")
            return redirect('location_manage_view')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Invalid file format. Please upload a .csv file.")
            return redirect('location_manage_view')

        try:
            file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.DictReader(file_data)
            count = 0

            for row in reader:
                name = row.get('name')
                if not name:
                    continue

                LocationFamily.objects.create(name=name)
                count += 1

            messages.success(request, f"✅ Successfully imported {count} location families.")
        except Exception as e:
            messages.error(request, f"❌ Error while importing families: {str(e)}")

        return redirect('location_manage_view')

    return redirect('location_manage_view')


# -------------------------------
# BULK IMPORT: LOCATION TYPES
# -------------------------------
def bulk_import_types(request):
    """Upload CSV and create LocationType entries"""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, "Please upload a CSV file.")
            return redirect('types_list')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Invalid file format. Please upload a .csv file.")
            return redirect('types_list')

        try:
            file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.DictReader(file_data)
            count = 0

            for row in reader:
                name = row.get('name')
                family_id = row.get('family_id')

                if not name or not family_id:
                    continue

                LocationType.objects.create(name=name, family_id=family_id)
                count += 1

            messages.success(request, f"✅ Successfully imported {count} location types.")
        except Exception as e:
            messages.error(request, f"❌ Error while importing types: {str(e)}")

        return redirect('types_list')

    return redirect('types_list')




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
# app1/views.py (append these imports + views)
import io, base64, qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.db.models import Count, DateField
from django.db.models.functions import TruncDate, ExtractHour

from .models import Voucher

# ---------- Helper to build absolute URL ----------
def full_url(request, path):
    return request.build_absolute_uri(path)

# ---------- Reception check-in: create voucher + QR ----------
import qrcode
import io
import base64
from urllib.parse import quote
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Voucher
import qrcode
import io
import base64
from urllib.parse import quote
from datetime import datetime, timedelta
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Voucher
import datetime

def _parse_yyyy_mm_dd(s: str):
    """Return date object or None. Accepts '', None, or 'YYYY-MM-DD'."""
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        # If you prefer to show an error instead, return an error message here.
        return None
# ---------- Reception check-in: create voucher + QR ----------
import qrcode
import io
from django.core.files.base import ContentFile
from django.urls import reverse
@login_required
def create_voucher_checkin(request):
    if request.method == "POST":
        guest_name = request.POST.get("guest_name")
        room_no = request.POST.get("room_no")
        adults = int(request.POST.get("adults", 1))
        kids = int(request.POST.get("kids", 0))
        quantity = int(request.POST.get("quantity", 0))
        country_code = request.POST.get("country_code")
        phone_number = request.POST.get("phone_number")
        email = request.POST.get("email")
        check_in_date = _parse_yyyy_mm_dd(request.POST.get("check_in_date"))
        check_out_date = _parse_yyyy_mm_dd(request.POST.get("check_out_date"))
        include_breakfast = request.POST.get("include_breakfast") == "on"  # checkbox

        # ✅ Create voucher first
        voucher = Voucher.objects.create(
            guest_name=guest_name,
            room_no=room_no,
            country_code=country_code,
            phone_number=phone_number,
            email=email,
            adults=adults,
            kids=kids,
            quantity=quantity,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            include_breakfast=include_breakfast,
        )

        # Generate landing URL using voucher_code
        voucher_page_url = reverse("voucher_landing", args=[voucher.voucher_code])
        landing_url = request.build_absolute_uri(voucher_page_url)

        # Generate scan URL for QR
        scan_url = request.build_absolute_uri(reverse("scan_voucher", args=[voucher.voucher_code]))

        # Generate QR code
        qr_content = voucher.voucher_code  # you can customize
        qr = qrcode.make(qr_content)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")

        # Save QR code as base64 string
        qr_img_str = base64.b64encode(buffer.getvalue()).decode()
        voucher.qr_code = qr_img_str

        # Save QR code as image file
        file_name = f"voucher_{voucher.id}.png"
        voucher.qr_code_image.save(file_name, ContentFile(buffer.getvalue()), save=True)

        voucher.save()
        qr_image_path = voucher.qr_code_image.path  # local file path
        os.startfile(qr_image_path)
        # Absolute URL for QR sharing
        qr_absolute_url = request.build_absolute_uri(voucher.qr_code_image.url)

        return render(request, "voucher_success.html", {
            "voucher": voucher,
            "qr_absolute_url": qr_absolute_url,
            "include_breakfast": include_breakfast,
            "scan_url": scan_url,
            "landing_url": landing_url,
        })

    return render(request, "checkin_form.html")

from django.shortcuts import get_object_or_404

@login_required
def voucher_landing(request, voucher_code):
    voucher = get_object_or_404(Voucher, voucher_code=voucher_code)
    return render(request, "voucher_landing.html", {
        "voucher": voucher,
        "qr_absolute_url": request.build_absolute_uri(voucher.qr_code_image.url),
    })
  

# import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render
from .models import Voucher
from django.utils import timezone
# import pandas as pd

def breakfast_voucher_report(request):
    
    
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())  # Start of week (Monday)

    vouchers = Voucher.objects.all()

    # Calculate counts
    daily_checkins = vouchers.filter(check_in_date=today).count()
    daily_checkouts = vouchers.filter(check_out_date=today).count()
    
    weekly_checkins = vouchers.filter(check_in_date__range=[week_start, today]).count()
    weekly_checkouts = vouchers.filter(check_out_date__range=[week_start, today]).count()

    df =  pd.DataFrame(Voucher.objects.all().values())

    # ✅ Convert timezone-aware datetimes to naive datetimes
    for col in df.select_dtypes(include=['datetimetz']).columns:
        df[col] = df[col].dt.tz_localize(None)

    if request.GET.get("export") == "1":
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="vouchers.xlsx"'
        df.to_excel(response, index=False)
        return response

    return render(request, "breakfast_voucher_report.html", {"vouchers": vouchers,'daily_checkins': daily_checkins,
        'daily_checkouts': daily_checkouts,
        'weekly_checkins': weekly_checkins,
        'weekly_checkouts': weekly_checkouts,})
from django.utils import timezone
from datetime import timedelta

from django.utils.timezone import now
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.utils.timezone import now
from .models import Voucher

@login_required
def mark_checkout(request, voucher_id):
    """
    Mark a voucher as checked out (set today's date as checkout).
    """
    try:
        voucher = Voucher.objects.get(id=voucher_id)
    except Voucher.DoesNotExist:
        return HttpResponse("Voucher not found", status=404)

    voucher.check_out_date = now().date()
    voucher.save(update_fields=["check_out_date"])

    # ✅ If the test expects 200 OK, return JSON instead of redirect
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.method == "POST":
        return JsonResponse({"message": "Check-out marked successfully."}, status=200)

    # ✅ For normal browser request
    return redirect("checkin_form")

      


from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Voucher
from datetime import date

@api_view(["GET"])
def validate_voucher(request):
    """
    Validate a voucher when its QR code is scanned.
    Increments scan_count, updates redeemed flags, and
    returns status + updated fields.
    """
    code = request.GET.get("code")
    if not code:
        return Response({"message": "Voucher code is required."},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        voucher = Voucher.objects.get(voucher_code=code)
    except Voucher.DoesNotExist:
        return Response({"message": "Invalid voucher code."},
                        status=status.HTTP_404_NOT_FOUND)
    

    # 1. Expired?
    if voucher.is_expired():
        return Response({"message": "❌ Voucher has expired.","guest_name": voucher.guest_name,
    "room_no": voucher.room_no,
    "quantity": voucher.quantity,},
                        status=status.HTTP_400_BAD_REQUEST)

    # 2. Valid for today?
    if voucher.is_valid_today():
        # ✅ increment scan_count and record history
        today = date.today().isoformat()
        if today not in (voucher.scan_history or []):
            voucher.scan_history.append(today)
        voucher.scan_count = (voucher.scan_count or 0) + 1

        # ✅ mark as redeemed (if not already)
        if not voucher.redeemed:
            voucher.redeemed = True
            voucher.redeemed_at = timezone.now()

        voucher.save(update_fields=["scan_history",
                                    "scan_count",
                                    "redeemed",
                                    "redeemed_at"])

        return Response({
            "success": True,
            "message": "✅ Voucher redeemed successfully for today.",
            "scan_count": voucher.scan_count,
            "redeemed": voucher.redeemed,
            "redeemed_at": voucher.redeemed_at,
            "guest_name": voucher.guest_name,
    "room_no": voucher.room_no,
    "quantity": voucher.quantity,
        })

    # 3. Already used today or not valid
    return Response({
        "success": False,
        "message": "❌ Voucher already used today or not valid for today.",
        "scan_count": voucher.scan_count,
        "redeemed": voucher.redeemed,
        "redeemed_at": voucher.redeemed_at,
        "guest_name": voucher.guest_name,
    "room_no": voucher.room_no,
    "quantity": voucher.quantity,
    }, status=status.HTTP_400_BAD_REQUEST)

 
@login_required
def scan_voucher_page(request):
    return render(request, "scan_voucher.html")

from rest_framework import viewsets
from .models import Voucher
from .serializers import VoucherSerializer
import qrcode
import io
from django.core.files.base import ContentFile

# class VoucherViewSet(viewsets.ModelViewSet):
#     queryset = Voucher.objects.all()
#     serializer_class = VoucherSerializer

#     def perform_create(self, serializer):
#         # Save voucher first
#         voucher = serializer.save()

#         # Generate QR code
#         qr = qrcode.make(voucher.voucher_code)
#         buffer = io.BytesIO()
#         qr.save(buffer, format="PNG")
#         file_name = f"voucher_{voucher.id}.png"
#         voucher.qr_code_image.save(file_name, ContentFile(buffer.getvalue()), save=True)

#         # Optional: save QR as base64 string
#         voucher.qr_code = buffer.getvalue().hex()  # or base64 if you prefer
#         voucher.save(update_fields=["qr_code", "qr_code_image"])

# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import date, timedelta
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
import qrcode, io, base64
from .models import Voucher
from .serializers import VoucherSerializer

# -------------------
# Voucher CRUD + QR
# -------------------
class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer

    def perform_create(self, serializer):
        voucher = serializer.save()

        # Auto-calculate quantity
        voucher.quantity = (voucher.adults or 0) + (voucher.kids or 0)

        # Auto-generate valid_dates
        if voucher.check_in_date and voucher.check_out_date:
            dates = []
            current = voucher.check_in_date
            while current <= voucher.check_out_date:
                dates.append(current.isoformat())
                current += timedelta(days=1)
            voucher.valid_dates = dates

        # Generate QR code
        qr = qrcode.make(voucher.voucher_code)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        file_name = f"voucher_{voucher.id}.png"
        voucher.qr_code_image.save(file_name, ContentFile(buffer.getvalue()), save=False)
        voucher.qr_code = base64.b64encode(buffer.getvalue()).decode()
        voucher.save()

    # -------------------
    # Scan & Validate Voucher
    # -------------------
    @action(detail=False, methods=["get"], url_path="validate")
    def validate_voucher(self, request):
        code = request.GET.get("code")
        if not code:
            return Response({"message": "Voucher code is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            voucher = Voucher.objects.get(voucher_code=code)
        except Voucher.DoesNotExist:
            return Response({"message": "Invalid voucher code."}, status=status.HTTP_404_NOT_FOUND)

        today = date.today().isoformat()
        if voucher.is_expired():
            return Response({"message": "❌ Voucher has expired."}, status=status.HTTP_400_BAD_REQUEST)

        if voucher.is_valid_today():
            if today not in (voucher.scan_history or []):
                voucher.scan_history.append(today)
            voucher.scan_count = (voucher.scan_count or 0) + 1
            if not voucher.redeemed:
                voucher.redeemed = True
                voucher.redeemed_at = timezone.now()
            voucher.save(update_fields=["scan_history","scan_count","redeemed","redeemed_at"])
            return Response({
                "success": True,
                "message": "✅ Voucher redeemed successfully for today.",
                "scan_count": voucher.scan_count,
                "redeemed": voucher.redeemed,
                "redeemed_at": voucher.redeemed_at,
                "guest_name": voucher.guest_name,
                "room_no": voucher.room_no,
                "quantity": voucher.quantity
            })
        return Response({"success": False, "message": "❌ Voucher already used today or not valid for today."}, status=status.HTTP_400_BAD_REQUEST)

    # -------------------
    # Daily/Weekly Checkin & Checkout Counts
    # -------------------
    @action(detail=False, methods=["get"], url_path="report")
    def report(self, request):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        vouchers = Voucher.objects.all()

        daily_checkins = vouchers.filter(check_in_date=today).count()
        daily_checkouts = vouchers.filter(check_out_date=today).count()
        weekly_checkins = vouchers.filter(check_in_date__range=[week_start, today]).count()
        weekly_checkouts = vouchers.filter(check_out_date__range=[week_start, today]).count()

        return Response({
            "daily_checkins": daily_checkins,
            "daily_checkouts": daily_checkouts,
            "weekly_checkins": weekly_checkins,
            "weekly_checkouts": weekly_checkouts
        })

    # -------------------
    # Mark Checkout (today)
    # -------------------
    @action(detail=True, methods=["post"], url_path="checkout")
    def checkout(self, request, pk=None):
        voucher = get_object_or_404(Voucher, id=pk)
        voucher.check_out_date = date.today()
        voucher.save(update_fields=["check_out_date"])
        return Response({"message": f"Checkout marked for voucher {voucher.voucher_code}", "check_out_date": voucher.check_out_date})

    # -------------------
    # Share via WhatsApp (returns URL)
    # -------------------
    @action(detail=True, methods=["get"], url_path="share")
    def share_whatsapp(self, request, pk=None):
        voucher = get_object_or_404(Voucher, id=pk)
        message = f"Hello {voucher.guest_name}, your voucher code is {voucher.voucher_code}. QR: {request.build_absolute_uri(voucher.qr_code_image.url)}"
        whatsapp_url = f"https://wa.me/{voucher.country_code}{voucher.phone_number}?text={message}"
        return Response({"whatsapp_url": whatsapp_url})



import io, base64, qrcode
import pandas as pd
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import GymMember
from io import BytesIO


# Generate unique code
def generate_customer_code():
    last = GymMember.objects.order_by("-member_id").first()
    if last:
        number = int(last.customer_code.replace("FGS", "")) + 1
    else:
        number = 1
    return f"FGS{number:04d}"


def add_member(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        nik = request.POST.get("nik")
        address = request.POST.get("address")
        city = request.POST.get("city")
        place_of_birth = request.POST.get("place_of_birth")
        date_of_birth = request.POST.get("date_of_birth") or None
        religion = request.POST.get("religion")
        gender = request.POST.get("gender")
        occupation = request.POST.get("occupation")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        pin = request.POST.get("pin")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            return render(
                request,
                "add_member.html",
                {"error": "Password and Confirm Password do not match."},
            )

        # Generate member code and dates
        customer_code = generate_customer_code()
        start_date = timezone.now().date()
        expiry_date = start_date + timedelta(days=90)

        # -----------------------------
        # QR-code logic (same as voucher)
        # -----------------------------
        # Content you want inside the QR
        

        # Save model first (without image file)
        member = GymMember.objects.create(
            customer_code=customer_code,
            full_name=full_name,
            nik=nik,
            address=address,
            city=city,
            place_of_birth=place_of_birth,
            date_of_birth=date_of_birth,
            religion=religion,
            gender=gender,
            occupation=occupation,
            phone=phone,
            email=email,
            pin=pin,
            password=password,
            confirm_password=confirm_password,
            start_date=start_date,
            expiry_date=expiry_date,
            status="Active",
             # store base64 string if desired
        )
        qr_content = member.customer_code

        # Generate PNG bytes
        qr_img = qrcode.make(qr_content)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")

        # Base64 string if you need it (optional)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Save actual PNG file to ImageField
        file_name = f"member_{member.member_id}.png"
        member.qr_code_image.save(file_name, ContentFile(buffer.getvalue()), save=True)
        qr_image_path = member.qr_code_image.path  # local file path
        os.startfile(qr_image_path)
        qr_absolute_url = request.build_absolute_uri(member.qr_code_image.url)

        # Landing link (optional future view)
        landing_url = request.build_absolute_uri(reverse("member_detail", args=[member.member_id]))
        return render(request, "gym_success.html", {
            "member": member,
            "qr_absolute_url": qr_absolute_url,
            "landing_url": landing_url,
        })
        return redirect("member_list")

    return render(request, "add_member.html")
def member_detail(request, member_id):
    member = member.objects.get(member_id=member_id)
    return render(request, 'members/member_detail.html', {'member': member})

def member_list(request):
    members = GymMember.objects.all().order_by("-created_at")

    search = request.GET.get("search")
    for m in members:
        if m.qr_code_image:
            m.qr_code_full_url = request.build_absolute_uri(m.qr_code_image.url)
        else:
            m.qr_code_full_url = None
    if search:
        members = members.filter(
            Q(full_name__icontains=search) | Q(customer_code__icontains=search)
        )
    entries_per_page = int(request.GET.get('entries', 10))
    paginator = Paginator(members, entries_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if request.GET.get("export") == "1":
        df = pd.DataFrame(members.values())
        for col in df.select_dtypes(include=["datetimetz"]).columns:
            df[col] = df[col].dt.tz_convert(None)
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="members.xlsx"'
        df.to_excel(response, index=False)
        return response

    return render(request, "member_list.html", {"members": members,"page_obj":page_obj,"entries":entries_per_page,"search":search})


    
# gym/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import GymMember

# @api_view(["GET"])
# def validate_member_qr(request):
#     code = (request.GET.get("code") or "").strip()
#     try:
#         member = GymMember.objects.get(customer_code=code)
#     except GymMember.DoesNotExist:
#         return Response({"message": "Invalid QR code."}, status=status.HTTP_404_NOT_FOUND)

#     if member.is_expired():
#         return Response({"message": "❌ Membership expired."}, status=status.HTTP_400_BAD_REQUEST)

#     # Try to mark scan
#     if member.mark_scanned_today(max_scans_per_day=3):
#         return Response({"success": True, "message": "✅ Entry allowed.", "scan_count": member.scan_count})

#     return Response({"success": False, "message": "❌ Daily scan limit reached."},
#                     status=status.HTTP_400_BAD_REQUEST)

# gym/views.py
from .models import GymMember, GymVisit
from django.contrib.auth.models import User

@api_view(["GET"])
def validate_member_qr(request):
    code = (request.GET.get("code") or "").strip()
    try:
        member = GymMember.objects.get(customer_code=code)
    except GymMember.DoesNotExist:
        return Response({"message": "Invalid QR code."}, status=status.HTTP_404_NOT_FOUND)

    # Check expiry
    if member.is_expired():
        return Response({"message": "❌ Membership expired."}, status=status.HTTP_400_BAD_REQUEST)

    # Try to mark scan
    if member.mark_scanned_today(max_scans_per_day=3):
        # ✅ Log into GymVisit table
        GymVisit.objects.create(
            member=member,
            checked_by_user=request.user,  # who scanned
            notes="QR Scan Entry"
        )
        return Response({
            "success": True,
            "message": "✅ Entry allowed.",
            "scan_count": member.scan_count
        })

    return Response({"success": False, "message": "❌ Daily scan limit reached."}, status=status.HTTP_400_BAD_REQUEST)

   
# gym/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def scan_gym_page(request):
    return render(request, "scan_gym.html")

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import GymMember
from django.utils import timezone
import qrcode, io, base64

# ---------- EDIT MEMBER ----------
from datetime import timedelta

def edit_member(request, member_id):
    member = get_object_or_404(GymMember, member_id=member_id)

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        address = request.POST.get("address")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        city = request.POST.get("city")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            messages.error(request, "❌ Password mismatch.")
            return render(request, "edit_member.html", {"member": member})

        # Update fields
        member.full_name = full_name
        member.address = address
        member.phone = phone
        member.email = email
        member.city = city
        if password:
            member.password = password
        
        # ✅ Extend voucher only if admin ticks/chooses "renew"
        renew = request.POST.get("renew_membership")  # from a checkbox in form
        if renew:
            if not member.is_expired():
                messages.warning(request, f"⚠️ {member.full_name} membership has not expired yet!")
                return render(request, "edit_member.html", {"member": member})
            today = timezone.now().date()
            member.start_date = today
            member.expiry_date = today + timedelta(days=90)  # 3 months
            member.qr_expired = False

            # 🔄 Re-generate QR
            qr_content = member.customer_code

        # Generate PNG bytes
            qr_img = qrcode.make(qr_content)
            buffer = io.BytesIO()
            qr_img.save(buffer, format="PNG")

        # Base64 string if you need it (optional)
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Save actual PNG file to ImageField
            file_name = f"member_{member.member_id}.png"
            member.qr_code_image.save(file_name, ContentFile(buffer.getvalue()), save=True)
            member.qr_code_full_url = request.build_absolute_uri(member.qr_code_image.url)

            

        # If inactive → expire QR
        if member.status == "Inactive":
            if member.qr_code_image:
                member.qr_code_image.delete(save=False)
            member.qr_code_image = None
            member.qr_expired = True

        member.save()
        qr_image_path = member.qr_code_image.path  # local file path
        os.startfile(qr_image_path)
        messages.success(request, f"{member.full_name} ✅ Member updated successfully.")
        qr_absolute_url = request.build_absolute_uri(member.qr_code_image.url)

        # Landing link (optional future view)
        landing_url = request.build_absolute_uri(reverse("member_detail", args=[member.member_id]))
        return render(request, "gym_success.html", {
            "member": member,
            "qr_absolute_url": qr_absolute_url,
            "landing_url": landing_url,
        })
        return redirect("member_list")

    return render(request, "edit_member.html", {"member": member})

# ---------- DELETE MEMBER ----------
def delete_member(request, member_id):
    member = get_object_or_404(GymMember, member_id=member_id)

    if request.method == "POST":
        member.delete()
        messages.success(request, "✅ Member deleted successfully.")
        return redirect("member_list")

    return render(request, "delete_member.html", {"member": member})

# gym/views.py
from django.contrib.auth.decorators import login_required
from django.db.models import Q

# @login_required
# def gym_report(request):
#     visits = GymVisit.objects.select_related("member", "visitor", "checked_by_user").order_by("-visit_at")

#     # Date filter
#     from_date = request.GET.get("from_date")
#     to_date = request.GET.get("to_date")
#     if from_date and to_date:
#         visits = visits.filter(visit_at__date__range=[from_date, to_date])

#     # Export to Excel
#     if request.GET.get("export") == "1":
#         import pandas as pd
#         df = pd.DataFrame(list(visits.values(
#             "visit_id",
#             "member__customer_code",
#             "member__full_name",
#             "visitor__full_name",
#             "visit_at",
#             "checked_by_user__username",
#         )))
#         response = HttpResponse(
#             content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#         )
#         response["Content-Disposition"] = 'attachment; filename="gym_report.xlsx"'
#         # Convert all datetime columns to timezone-naive
#         for col in df.select_dtypes(include=["datetimetz"]).columns:
#             df[col] = df[col].dt.tz_localize(None)

#         df.to_excel(response, index=False)
#         return response
    
#     return render(request, "gym_report.html", {"visits": visits})

@login_required
def gym_report(request):
    visits = GymVisit.objects.select_related("member", "visitor", "checked_by_user").order_by("-visit_at")

    # Date filter
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    
    if from_date and to_date:
        visits = visits.filter(visit_at__date__range=[from_date, to_date])

    # Export to Excel
    if request.GET.get("export") == "1":
        # Create DataFrame with filtered data
        data = []
        for visit in visits:
            data.append({
                'ID': visit.visit_id,
                'Customer ID': visit.member.customer_code if visit.member else '-',
                'Name': visit.member.full_name if visit.member else visit.visitor.full_name,
                'Date & Time': visit.visit_at.strftime("%Y-%m-%d %I:%M %p") if visit.visit_at else '',
                'Admin': visit.checked_by_user.username if visit.checked_by_user else '-',
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Gym Report')
        
        output.seek(0)
        
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="gym_report.xlsx"'
        return response
    
    # Pagination
    paginator = Paginator(visits, 10)  # 10 records per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'visits': page_obj.object_list,
        'from_date': from_date,
        'to_date': to_date,
        'total_count': paginator.count,
    }
    
    return render(request, "gym_report.html", context)
from django.shortcuts import render
from django.contrib import messages
from .models import GymMember
# from django.utils import timezone

# def data_checker(request):
#     result = None
#     if request.method == "POST":
#         member_id = request.POST.get("member_id")

#         try:
#             member = GymMember.objects.get(customer_code=member_id)
#             today = timezone.now().date()

#             if member.status == "Inactive":
#                 result = {"status": "Inactive ❌", "color_class": "success"}
#             elif member.expiry_date and member.expiry_date < today:
#                 result = {"status": "Expired ⏳", "color_class": "success"}
#             else:
#                 result = {"status": "Active ✅", "color_class": "success"}

#             result["member"] = member

#         except GymMember.DoesNotExist:
#             messages.error(request, f"No member found with ID {member_id}")

#     return render(request, "data_checker.html", {"result": result})
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from .models import GymMember  # Make sure GymMember is imported

def data_checker(request):
    result = None

    if request.method == "POST":
        member_id = request.POST.get("member_id")

        try:
            member = GymMember.objects.get(customer_code=member_id)
            today = timezone.now().date()

            # Determine member status
            if member.status == "Inactive":
                status = "Inactive ❌"
                color_class = "danger"
            elif member.expiry_date and member.expiry_date < today:
                status = "Expired ⏳"
                color_class = "warning"
            else:
                status = "Active ✅"
                color_class = "success"

            result = {
                "member": member,
                "status": status,
                "color_class": color_class,
            }

        except GymMember.DoesNotExist:
            messages.error(request, f"No member found with ID {member_id}")

    return render(request, "data_checker.html", {"result": result})


# views_api.py
import io, qrcode, pandas as pd
from datetime import timedelta
from django.utils import timezone
from django.core.files.base import ContentFile
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import GymMember, GymVisit
from .serializers import GymMemberSerializer, GymVisitSerializer


# ============================================================
# 🧍‍♂️ GYM MEMBER VIEWSET — CRUD + QR + Validation + Export
# ============================================================
class GymMemberViewSet(viewsets.ModelViewSet):
    queryset = GymMember.objects.all().order_by('-created_at')
    serializer_class = GymMemberSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        """Auto-generate code, expiry, and QR only when password validated"""
        last = GymMember.objects.order_by('-member_id').first()
        number = int(last.customer_code.replace("FGS", "")) + 1 if last else 1
        customer_code = f"FGS{number:04d}"
        start_date = timezone.now().date()
        expiry_date = start_date + timedelta(days=90)

        member = serializer.save(
            customer_code=customer_code,
            start_date=start_date,
            expiry_date=expiry_date,
            status="Active"
        )

        # Generate QR
        qr_img = qrcode.make(member.customer_code)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        filename = f"qr_codes/member_{member.member_id}.png"
        member.qr_code = member.customer_code
        member.qr_code_image.save(filename, ContentFile(buffer.read()), save=True)
        member.save()

    # =====================================================
    # GET /api/gym/members/validate/?code=FGS0001
    # =====================================================
    @action(detail=False, methods=['get'], url_path='validate')
    def validate_qr(self, request):
        code = (request.GET.get("code") or "").strip()
        try:
            member = GymMember.objects.get(customer_code=code)
        except GymMember.DoesNotExist:
            return Response({"message": "❌ Invalid QR Code"}, status=404)

        if member.is_expired():
            return Response({"message": "❌ Membership Expired"}, status=400)

        if member.mark_scanned_today(max_scans_per_day=3):
            GymVisit.objects.create(member=member, notes="QR Redeemed")
            return Response({
                "success": True,
                "message": "✅ QR Redeemed Successfully",
                "scan_count": member.scan_count,
                "member_name": member.full_name,
                "expiry_date": member.expiry_date
            })
        return Response({
            "success": False,
            "message": "❌ Daily scan limit reached"
        }, status=400)

    # =====================================================
    # GET /api/gym/members/export/
    # =====================================================
    @action(detail=False, methods=['get'], url_path='export')
    def export_excel(self, request):
        members = GymMember.objects.all().values(
            'customer_code', 'full_name', 'email', 'phone', 'status', 
            'start_date', 'expiry_date', 'scan_count'
        )
        df = pd.DataFrame(members)

        # Format date columns
        for col in ['start_date', 'expiry_date']:
            df[col] = df[col].apply(lambda x: x.strftime("%Y-%m-%d") if x else "")

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Gym Members')

        buffer.seek(0)
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="gym_members.xlsx"'
        return response



# ============================================================
# 🏋️ GYM VISIT VIEWSET — CRUD + Report
# ============================================================
class GymVisitViewSet(viewsets.ModelViewSet):
    queryset = GymVisit.objects.all().order_by('-visit_at')
    serializer_class = GymVisitSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'], url_path='report')
    def visit_report(self, request):
        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")
        visits = GymVisit.objects.select_related("member").order_by("-visit_at")

        if from_date and to_date:
            visits = visits.filter(visit_at__date__range=[from_date, to_date])

        df = pd.DataFrame(list(visits.values(
            "visit_id", "member__customer_code", "member__full_name", "visit_at"
        )))
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        )
        response["Content-Disposition"] = 'attachment; filename="gym_members.xlsx"'

        df.to_excel(response, index=False)
        return response