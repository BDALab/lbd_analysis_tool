from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin


# Import the auth view
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)

# Import the subjects' app views
from subjects.views import LandingPageView, SignupView, SigninView


# Define the URL patterns
urlpatterns = [
    path('', LandingPageView.as_view(), name='landing_page'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', SigninView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('reset-password/', PasswordResetView.as_view(), name='reset_password'),
    path('password-reset-done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Subjects app
    path('subjects/', include('subjects.urls', namespace='subjects')),

    # Admin
    path('admin', admin.site.urls),
]


# Add the static file-patterns into the URL patterns in a DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
