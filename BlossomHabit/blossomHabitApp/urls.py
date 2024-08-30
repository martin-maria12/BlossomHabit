from django.urls import path

from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('homepage/', views.homepage, name='homepage'),
    path('calendar/', views.calendar, name='calendar'),
    path('new_activity/', views.new_activity, name='new_activity'),
    path('categories/', views.categories, name='categories'),
    path('journal/', views.journal, name='journal'),
    path('statistics/', views.statistics, name='statistics'),
    path('category/', views.category, name='category'),
    path('add_new_category/', views.add_new_category, name='add_new_category'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='user_logout'),
    path('activity/complete/<int:activity_id>/', views.complete_activity, name='complete_activity'),
    path('activity/cancel/<int:activity_id>/', views.cancel_activity, name='cancel_activity'),
    path('get_emojis/', views.get_emojis, name='get_emojis'),
    path('edit_category/', views.edit_category, name='edit_category'),
    path('delete_category/<int:category_id>/', views.delete_category, name='delete_category'),
    path('edit_activity/', views.edit_activity, name='edit_activity'),
    path('activity/delete/<int:activity_id>/', views.delete_activity, name='delete_activity'),
    path('s_of_the_day/', views.s_of_the_day, name='s_of_the_day'),
    path('s_of_the_week/', views.s_of_the_week, name='s_of_the_week'),
    path('s_of_the_month/', views.s_of_the_month, name='s_of_the_month'),
    path('profile/', views.profile, name='profile'),
    path('profile/customize_avatar/', views.customize_avatar, name='customize_avatar'),
    path('profile/details/', views.details, name='details'),
    path('calendar_date/<str:selected_date>/', views.calendar_date, name='calendar_date'),
    path('rest/v1/calendar/init/', views.GoogleCalendarInitView.as_view(), name='calendar_init'),
    path('rest/v1/calendar/redirect/', views.GoogleCalendarRedirectView.as_view(), name='calendar_redirect'),

] 

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)