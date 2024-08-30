import re
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from django import forms

from .models import Category, Activity

class UserLoginForm(AuthenticationForm):
    pass

class SignupForm(UserCreationForm):

    username = forms.CharField(max_length=100)
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=100)
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="*Your password can't be too similar to your other personal information;\
                    Your password must contain at least 8 characters\
                    Your password can't be entirely numeric"
        )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name', 'color']
        labels = {
            'category_name': 'Name',
            'color': 'Color',
        }
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_category_name(self):
        category_name = self.cleaned_data['category_name']
        if Category.objects.filter(category_name=category_name, user=self.user).exists():
            raise forms.ValidationError('This category already exists for you')
        return category_name

    def clean_color(self):
        color = self.cleaned_data.get('color')
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise forms.ValidationError('Enter a valid color')
        return color
    
class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        exclude = ['state']
        fields = ['activity_name', 'date', 'start_time', 'end_time', 'category', 'notes', 'state']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'cols': 15}),
            'category': forms.RadioSelect(),
        }
        labels = {
            'activity_name': 'Activity',
            'date': 'Select Date',
            'start_time': 'Select Start Time',
            'end_time': 'Select End Time',
            'notes': 'Add Notes',
            'category': 'Select Category'
        }

        def clean(self):
            cleaned_data = super().clean()
            start_time = cleaned_data.get('start_time')
            end_time = cleaned_data.get('end_time')
            date = cleaned_data.get('date')
            user = cleaned_data.get('user')

            overlapping_activities = Activity.objects.filter(
                user=user,
                date=date,
                end_time__gt=start_time,
                start_time__lt=end_time,
            ).exclude(pk=self.instance.pk)

            if overlapping_activities.exists():
                self.add_error(None, "There is an overlap of activities")
                
class ActivityPopupForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['activity_name', 'date', 'start_time', 'end_time', 'category', 'notes', 'state']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'cols': 15}),
            'category': forms.Select(),
        }
        labels = {
            'activity_name': 'Activity',
            'date': 'Select Date',
            'start_time': 'Select Start Time',
            'end_time': 'Select End Time',
            'notes': 'Add Notes',
            'category': 'Select Category',
            'state': 'Select State'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            user_categories = Category.objects.filter(user=user).exclude(category_name="Google Calendar")
            default_categories = Category.objects.filter(user__isnull=True).exclude(category_name="Google Calendar")
            self.fields['category'].queryset = user_categories | default_categories

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date = cleaned_data.get('date')
        user = self.instance.user

        overlapping_activities = Activity.objects.filter(
            user=user,
            date=date,
            end_time__gt=start_time,
            start_time__lt=end_time,
        ).exclude(pk=self.instance.pk)

        if overlapping_activities.exists():
            self.add_error(None, "There is an overlap of activities")
        return cleaned_data
