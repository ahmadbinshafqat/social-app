"""
URL configuration for SocialApplication project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Networking.views import *


urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    path('friend-request/send/<int:to_user_id>/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('friend-request/accept/<int:friend_request_id>/', AcceptFriendRequestView.as_view(), name='accept-friend-request'),
    path('friend-request/reject/<int:friend_request_id>/', RejectFriendRequestView.as_view(), name='reject-friend-request'),
    path('user/block/<int:user_id>/', BlockUserView.as_view(), name='block-user'),
    path('user/unblock/<int:user_id>/', UnblockUserView.as_view(), name='unblock-user'),
    path('friend-request/pending/', PendingFriendRequestListView.as_view(), name='pending-friend-requests'),
    path('friends/list/', FriendsListView.as_view(), name='friends-list'),
    path('activities/', UserActivityView.as_view(), name='user-activities'),

]