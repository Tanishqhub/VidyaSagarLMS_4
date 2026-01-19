from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Custom authentication views
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # Dashboard URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('trainer/dashboard/', views.trainer_dashboard, name='trainer_dashboard'),

    # Batch management URLs
    path('batches/', views.batch_list, name='batch_list'),
    path('trainer/batches/', views.trainer_batch_list, name='trainer_batch_list'),
    path('batch/<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('batch/create/', views.create_batch, name='create_batch'),
    path('progress/<int:progress_id>/', views.mark_topic_complete, name='mark_topic_complete'),

    # Trainers management
    path('trainers/', views.trainer_list, name='trainer_list'),
    path('trainer/create/', views.create_trainer, name='create_trainer'),

    # Courses management
    path('courses/', views.course_list, name='course_list'),
    path('course/create/', views.create_course, name='create_course'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('course/<int:course_id>/add-module/', views.add_module, name='add_module'),
    path('module/<int:module_id>/edit/', views.edit_module, name='edit_module'),
    path('module/<int:module_id>/delete/', views.delete_module, name='delete_module'),
    path('module/<int:module_id>/add-topic/', views.add_topic, name='add_topic'),
    path('topic/<int:topic_id>/edit/', views.edit_topic, name='edit_topic'),
    path('topic/<int:topic_id>/delete/', views.delete_topic, name='delete_topic'),

    # Team management URLs
    path('team/', views.team_management, name='team_management'),
    path('team/create/', views.create_team_member, name='create_team_member'),
    path('team/<int:user_id>/update-role/', views.update_team_member_role, name='update_team_member_role'),
]