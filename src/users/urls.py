from django.urls import path

from users import views

app_name = 'users'

urlpatterns = [
    path('', views.CreateUserView.as_view(), name='create'),
    path('login/', views.LoginUserView.as_view(), name='login'),
    path('me/', views.ManageUserView.as_view(), name='me')
]
