from django import forms
from .models import Batch, Trainer, Course, Module, Topic, UserProfile
from django.contrib.auth.models import User


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['name', 'course', 'trainer', 'start_date', 'end_date', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter batch name'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'trainer': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active trainers and courses
        self.fields['trainer'].queryset = Trainer.objects.filter(is_active=True)
        self.fields['course'].queryset = Course.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError("End date must be after start date")

        return cleaned_data


class TrainerForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Trainer
        fields = ['username', 'first_name', 'last_name', 'password', 'confirm_password', 'phone', 'specialization',
                  'experience_years', 'bio', 'is_active']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        # Check if username already exists
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with this username already exists.")

        # Create user first
        user_data = {
            'username': username,
            'first_name': self.cleaned_data['first_name'],
            'last_name': self.cleaned_data['last_name'],
            'email': '',  # Empty email for now
        }

        user = User.objects.create_user(**user_data)
        user.set_password(self.cleaned_data['password'])
        user.save()

        # Create trainer profile
        trainer = super().save(commit=False)
        trainer.user = user
        if commit:
            trainer.save()
        return trainer


class CourseCreateForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description', 'total_duration_hours', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'total_duration_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ModuleCreateForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['name', 'description', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TopicCreateForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['name', 'description', 'duration_hours', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role', 'phone', 'department']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
        }