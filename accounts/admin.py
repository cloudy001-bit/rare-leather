# from django.contrib import admin

# # accounts/admin.py
# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from .models import User

# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     model = User
#     list_display = ('email', 'full_name', 'is_active', 'is_staff', 'created_at')
#     list_filter = ('is_active', 'is_staff', 'is_superuser')
#     ordering = ('-created_at',)
#     search_fields = ('email', 'full_name')
#     readonly_fields = ('created_at',)

#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         ('Personal Info', {'fields': ('full_name',)}),
#         ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#         ('Important Dates', {'fields': ('last_login', 'created_at')}),
#     )

#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'full_name', 'password1', 'password2', 'is_active', 'is_staff')}
#         ),
#     )


# # Register your models here.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from .models import User


# Custom user creation form for the admin
class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'full_name')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# Custom user admin panel
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    model = User

    list_display = ('email', 'full_name', 'is_active', 'is_staff', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    ordering = ('-created_at',)
    search_fields = ('email', 'full_name')
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {'fields': ('last_login', 'created_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'full_name',
                'password1',
                'password2',
                'is_active',
                'is_staff',
                'is_superuser',
            ),
        }),
    )

