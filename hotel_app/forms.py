import os
from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from .models import Department, UserProfile, Voucher, Guest, Location, RequestType, Checklist, Complaint, Review
from django.conf import settings


class UserCreationForm(BaseUserCreationForm):
    full_name = forms.CharField(max_length=160, required=False)
    phone = forms.CharField(max_length=15, required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    role = forms.CharField(max_length=100, required=False)
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank to auto-generate a password"
    )

    class Meta:
        model = User
        fields = ("username", "email", "password")
        
    def save(self, commit=True):
        user = super().save(commit=False)
        # If no password was provided, set a random one
        if not self.cleaned_data.get('password'):
            user.set_password(User.objects.make_random_password())
        if commit:
            user.save()
        return user


# class VoucherForm(forms.ModelForm):
#     generate_qr = forms.BooleanField(required=False, label="Generate QR Code")

#     class Meta:
#         model = Voucher
#         fields = ['guest_name', 'room_number', 'expiry_date']

#     def save(self, commit=True):
#         voucher = super().save(commit=commit)
        
#         if commit and self.cleaned_data.get('generate_qr'):
#             from .utils import generate_voucher_qr_base64, generate_voucher_qr_data
            
#             # Generate QR code with larger size for better visibility
#             voucher.qr_image = generate_voucher_qr_base64(voucher, size='xxlarge')
#             voucher.save()
        
#         return voucher


# class VoucherScanForm(forms.Form):
#     """Form for manual voucher scanning/validation"""
#     voucher_code = forms.CharField(
#         max_length=100,
#         label="Voucher Code",
#         help_text="Enter the voucher code to validate",
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Enter voucher code',
#             'autofocus': True
#         })
#     )
#     notes = forms.CharField(
#         required=False,
#         widget=forms.Textarea(attrs={
#             'rows': 2,
#             'class': 'form-control',
#             'placeholder': 'Optional notes about this scan'
#         }),
#         label="Notes"
#     )


class GuestForm(forms.ModelForm):
    class Meta:
        model = Guest
        fields = ['full_name', 'phone', 'email', 'room_number', 'checkin_date', 'checkout_date', 'breakfast_included', 'package_type']
        widgets = {
            'checkin_date': forms.DateInput(attrs={'type': 'date'}),
            'checkout_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        checkin_date = cleaned_data.get('checkin_date')
        checkout_date = cleaned_data.get('checkout_date')

        if checkin_date and checkout_date and checkout_date <= checkin_date:
            raise forms.ValidationError('Checkout date must be after check-in date.')

        return cleaned_data


class UserForm(forms.ModelForm):
    full_name = forms.CharField(max_length=160, required=False)
    phone = forms.CharField(max_length=15, required=False)
    title = forms.CharField(max_length=120, required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    role = forms.CharField(max_length=100, required=False)  # Change to CharField to avoid choice validation
    profile_picture = forms.ImageField(required=False, label="Profile Picture")

    class Meta:
        model = User
        fields = ['username', 'email', 'is_active']
        # Add widgets for better styling
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                profile = self.instance.userprofile
                self.fields['full_name'].initial = profile.full_name
                self.fields['phone'].initial = profile.phone
                self.fields['title'].initial = profile.title
                self.fields['department'].initial = profile.department
                # Set initial role based on user's groups
                user_groups = self.instance.groups.values_list('name', flat=True)
                if user_groups:
                    self.fields['role'].initial = user_groups[0]  # Take the first group as the role
            except UserProfile.DoesNotExist:
                pass

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Only check for existing email if it's different from the current user's email
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Only check for existing username if it's different from the current user's username
        if username and User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            # Check file size (limit to 5MB)
            if profile_picture.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image file too large ( > 5MB )")
            
            # Check file extension
            ext = os.path.splitext(profile_picture.name)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if ext not in valid_extensions:
                raise forms.ValidationError("Unsupported file extension. Please upload a JPG, JPEG, PNG, or GIF image.")
        return profile_picture

    def save(self, commit=True):
        user = super().save(commit=False)
        if not self.instance.pk:  # Set a default password for new users
            user.set_password('password123')  # You should have a more secure way to handle this
        if commit:
            user.save()
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.full_name = self.cleaned_data.get('full_name', '')
            profile.phone = self.cleaned_data.get('phone', '')
            profile.title = self.cleaned_data.get('title', '')
            profile.department = self.cleaned_data.get('department', None)
            
            # Handle profile picture upload
            profile_picture = self.cleaned_data.get('profile_picture')
            if profile_picture:
                # Create user directory if it doesn't exist
                user_dir = os.path.join(settings.MEDIA_ROOT, 'users', str(user.pk))
                os.makedirs(user_dir, exist_ok=True)
                
                # Save the file
                filename = f"profile_picture{os.path.splitext(profile_picture.name)[1]}"
                file_path = os.path.join(user_dir, filename)
                
                # Save the file to disk
                with open(file_path, 'wb+') as destination:
                    for chunk in profile_picture.chunks():
                        destination.write(chunk)
                
                # Update avatar_url in profile (use URL-style join to avoid backslashes on Windows)
                # Ensure MEDIA_URL is used as a URL prefix (e.g. '/media/'), then append user path
                media_url = settings.MEDIA_URL or '/media/'
                if not media_url.endswith('/'):
                    media_url = media_url + '/'
                profile.avatar_url = f"{media_url}users/{user.pk}/{filename}"
            
            profile.save()
            
            # Handle role assignment
            role = self.cleaned_data.get('role')
            if role:
                try:
                    group = Group.objects.get(name=role)
                    user.groups.set([group])  # Assign the user to the selected group
                except Group.DoesNotExist:
                    # If the group doesn't exist, don't assign any role
                    user.groups.clear()
        return user

class DepartmentForm(forms.ModelForm):
    logo = forms.ImageField(required=False, label="Department Logo")

    class Meta:
        model = Department
        fields = ['name', 'description', 'logo']
        
    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            # Check file size (limit to 5MB)
            if logo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image file too large ( > 5MB )")
            
            # Check file extension
            ext = os.path.splitext(logo.name)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg']
            if ext not in valid_extensions:
                raise forms.ValidationError("Unsupported file extension. Please upload a JPG, JPEG, PNG, GIF, or SVG image.")
        return logo

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'description']

class RequestTypeForm(forms.ModelForm):
    class Meta:
        model = RequestType
        fields = ['name', 'description']

class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ['name', 'description']

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['guest', 'subject', 'description', 'status']

# class BreakfastVoucherForm(forms.ModelForm):
#     class Meta:
#         model = BreakfastVoucher
#         fields = ['guest', 'room_no', 'location', 'qty', 'valid_from', 'valid_to', 'status']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['guest', 'rating', 'comment']
        widgets = {
            'guest': forms.Select(attrs={
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'
            }),
            'rating': forms.Select(attrs={
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500',
                'rows': 4,
                'placeholder': 'Share your experience with us...'
            }),
        }


# class GymMemberForm(forms.ModelForm):
#     class Meta:
#         model = GymMember
#         fields = ['full_name', 'email', 'address', 'city', 'phone', 'start_date', 'end_date']
#         widgets = {
#             'start_date': forms.DateInput(attrs={'type': 'date'}),
#             'end_date': forms.DateInput(attrs={'type': 'date'}),
#         }
    
#     def clean(self):
#         cleaned_data = super().clean()
#         start_date = cleaned_data.get('start_date')
#         end_date = cleaned_data.get('end_date')
        
#         if start_date and end_date and end_date < start_date:
#             raise forms.ValidationError('End date must be after start date.')
        
#         return cleaned_data
    
#     def save(self, commit=True):
#         instance = super().save(commit=False)
#         # Combine first and last names into full_name
#         first_name = self.cleaned_data.get('first_name', '')
#         last_name = self.cleaned_data.get('last_name', '')
#         instance.full_name = f"{first_name} {last_name}".strip()
        
#         if commit:
#             instance.save()
#         return instance
class FeedbackForm(forms.ModelForm):
    """Form for adding new feedback/reviews"""
    class Meta:
        model = Review
        fields = ['guest', 'rating', 'comment']
        widgets = {
            'guest': forms.Select(attrs={
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500',
                'placeholder': 'Select guest'
            }),
            'rating': forms.Select(attrs={
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500',
                'rows': 4,
                'placeholder': 'Share your experience with us...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add empty choice for guest
        self.fields['guest'].queryset = Guest.objects.all().order_by('full_name')
        self.fields['guest'].empty_label = "Select a guest (optional)"
        
        # Customize rating choices to be more descriptive
        self.fields['rating'].choices = [
            (1, '1 Star - Poor'),
            (2, '2 Stars - Fair'),
            (3, '3 Stars - Average'),
            (4, '4 Stars - Good'),
            (5, '5 Stars - Excellent')
        ]

# dashboard/forms.py

from django import forms
from .models import GymMember

class GymMemberForm(forms.ModelForm):
    class Meta:
        model = GymMember
        fields = ['full_name', 'email', 'phone', 'address', 'city', 'start_date', 'end_date']

        # Add consistent styling to all form fields to match the template
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500',
                'placeholder': 'e.g. John Doe'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500',
                'placeholder': 'e.g. john@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500',
                'placeholder': 'e.g. +1234567890'
            }),
            'address': forms.Textarea(attrs={
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500',
                'rows': 3,
                'placeholder': 'e.g. 123 Main St'
            }),
            'city': forms.TextInput(attrs={
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500',
                'placeholder': 'e.g. New York'
            }),
            # Keep the type attribute for HTML5 date picker
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-sky-500 focus:ring-sky-500'
            }),
        }

    # IMPROVEMENT: Attach the validation error directly to the 'end_date' field
    def clean_end_date(self):
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')

        # Ensure both dates are present before comparing
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be before the start date.")

        return end_date

    # The custom save() method was redundant and has been removed.
    # The default ModelForm.save() will be used, which is correct.
