from django import forms
from .models import Order
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name',
                'required': 'required',  # Add this
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter your last name',
                'required': 'required',  # Add this
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'required': 'required',  # Add this
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number',
                'required': 'required',  # Add this
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your full address',
                'required': 'required',  # Add this
            }),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required
        for field in self.fields.values():
            field.required = True


class CustomUserCreationForm(UserCreationForm):
    """
    Enhanced user registration form with additional fields
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize username field
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        
        # Customize password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    """
    Enhanced login form with better styling
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize username field
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'autocomplete': 'username'
        })
        
        # Customize password field
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })

    def confirm_login_allowed(self, user):
        """
        Add custom login validation if needed
        """
        super().confirm_login_allowed(user)
        
        # You can add custom checks here, for example:
        # if not user.is_active:
        #     raise forms.ValidationError("This account is inactive.")

class CustomPasswordResetForm(forms.Form):
    """
    Custom password reset form for the modal
    """
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        })
    )

    def clean_email(self):
        """
        Validate that the email exists in the system
        """
        email = self.cleaned_data['email']
        
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "No user is registered with this email address."
            )
        
        return email




# # forms.py
# from django import forms
# from .models import UserProfile
   
# class UserProfileForm(forms.ModelForm):
#        class Meta:
#            model = UserProfile
#            fields = ['phone', 'date_of_birth', 'gender', 'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country']

