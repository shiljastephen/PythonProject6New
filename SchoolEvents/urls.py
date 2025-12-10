from django.urls import path
from django.contrib.auth import views as auth_views
from .views import manage_participants
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('<int:event_id>/', views.event_detail, name='event_detail'),
    path('create/', views.create_event, name='create_event'),
    path('pending/', views.pending_events, name='pending_events'),
    path('<int:event_id>/approve/', views.approve_event, name='approve_event'),
    path('<int:event_id>/register/', views.register_event, name='register_event'),
    path('<int:event_id>/cancel/', views.cancel_registration, name='cancel_registration'),
    path('<int:event_id>/feedback/', views.submit_feedback, name='submit_feedback'),
    path('teacher/event/<int:event_id>/participants/', manage_participants, name='manage_participants'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('register/', views.register, name='register'),
]
