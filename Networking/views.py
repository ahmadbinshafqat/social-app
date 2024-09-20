from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.exceptions import TokenError
from .models import *
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from .serializers import *
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, F
from rest_framework import generics, status
from django.core.paginator import Paginator

from rest_framework.permissions import IsAuthenticated
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .permissions import IsReadOnly, IsWriter, IsAdmin
# permission_classes = [IsAuthenticated, IsWriter, IsReadOnly, IsAdmin]


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')

            if User.objects.filter(email=email).exists():
                return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.create_user(username=email, email=email, password=password)
            user.save()

            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email.lower(), password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({"error": "Invalid credentials"}, status=status.HTTP_404_NOT_FOUND)


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
            return Response({
                'access': new_access_token,
            })
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()
            return Response({"message": "Successfully logged out"}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            query = request.query_params.get('query', '')
            if not query:
                return Response({"error": "Search query is required"}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(email__iexact=query).exists():
                users = User.objects.filter(email__iexact=query)
            else:
                users = User.objects.filter(
                    Q(email__icontains=query) |
                    Q(username__icontains=query) |
                    Q(bio__icontains=query)
                ).distinct()

            paginator = PageNumberPagination()
            paginator.page_size = 10
            result_page = paginator.paginate_queryset(users, request)
            serializer = UserSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            print(e)


class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, to_user_id):
        from_user = request.user
        try:

            to_user = User.objects.get(id=to_user_id)
            if from_user == to_user:
                return Response({"error": "You cannot send a friend request to yourself."}, status=status.HTTP_400_BAD_REQUEST)

            cache_key = f"friend_req_limit_{from_user.id}"
            request_count = cache.get(cache_key, 0)

            if request_count >= 3:
                return Response({"error": "Too many friend requests. Try again later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

            cooldown_key = f"cooldown_{from_user.id}_{to_user.id}"
            cooldown_check = cache.get(cooldown_key, 0)

            if cooldown_check:
                return Response({"error": "You cannot send friend request right now. Try again later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

            with transaction.atomic():
                Friendship.objects.send_request(from_user, to_user)

                cache.set(cache_key, request_count + 1, timeout=60)

                return Response({"message": "Friend request sent successfully."}, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class AcceptFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, friend_request_id):
        try:
            with transaction.atomic():
                friend_request = Friendship.objects.get(id=friend_request_id, to_user=request.user)

                if friend_request.is_accepted:
                    return Response({"error": "Friend request is already accepted."}, status=status.HTTP_400_BAD_REQUEST)

                friend_request.accept()
                return Response({"message": "Friend request accepted successfully."}, status=status.HTTP_200_OK)

        except Friendship.DoesNotExist:
            return Response({"error": "Friend request not found."}, status=status.HTTP_404_NOT_FOUND)


class RejectFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, friend_request_id):
        try:

            friend_request = Friendship.objects.get(id=friend_request_id, to_user=request.user)

            cooldown_key = f"cooldown_{friend_request.from_user.id}_{friend_request.to_user.id}"
            cache.set(cooldown_key, True, timeout=60*60*24)  # 24 hours

            friend_request.reject()
            return Response({"message": "Friend request rejected."}, status=status.HTTP_200_OK)

        except Friendship.DoesNotExist:
            return Response({"error": "Friend request not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)


class BlockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            to_user = User.objects.get(id=user_id)

            # Block the user (or create friendship if it doesn't exist)
            Friendship.objects.block_user(request.user, to_user)
            return Response({"message": "User blocked successfully."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class UnblockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            to_user = User.objects.get(id=user_id)

            Friendship.objects.unblock_user(request.user, to_user)
            return Response({"message": "User unblocked successfully."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class PendingFriendRequestListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PendingFriendRequestSerializer

    def get_queryset(self):
        return Friendship.objects.filter(
            to_user=self.request.user,
            is_accepted=False
        ).order_by('created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        paginator = Paginator(queryset, 10)
        page_number = request.query_params.get('page', 1)
        page_obj = paginator.get_page(page_number)

        serializer = self.get_serializer(page_obj, many=True)
        return Response({
            'pending_requests': serializer.data,
            'total_pages': paginator.num_pages,
            'current_page': page_number
        }, status=status.HTTP_200_OK)


class FriendsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cache_key = f'friends_list_{request.user.id}'
        cached_friends = cache.get(cache_key)

        if cached_friends:
            return Response(cached_friends)

        friendships = Friendship.objects.filter(
            (Q(from_user=request.user) | Q(to_user=request.user)) & Q(is_accepted=True)
        ).select_related('from_user', 'to_user')

        friends = [
            friendship.to_user if friendship.from_user == request.user else friendship.from_user
            for friendship in friendships
        ]

        serializer = FriendSerializer(friends, many=True)

        cache.set(cache_key, serializer.data, timeout=3600)

        return Response(serializer.data)


class UserActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        activities = UserActivity.objects.filter(user=request.user).order_by('-created_at')
        page_size = 10  # Example page size
        page = int(request.GET.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size

        paginated_activities = activities[start:end]
        serializer = UserActivitySerializer(paginated_activities, many=True)

        return Response({
            'page': page,
            'page_size': page_size,
            'activities': serializer.data,
            'total': activities.count()
        })