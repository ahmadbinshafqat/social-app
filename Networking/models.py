from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, F
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db import transaction


class User(AbstractUser):
    ROLE_CHOICES = (
        ('read', 'Read'),
        ('write', 'Write'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(unique=True, max_length=255)
    bio = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='read')  # Role field

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    # def save(self, *args, **kwargs):
    #     # Update the search vector field on save
    #     self.search_vector = SearchVector('username')
    #     super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    # Get friends method
    def get_friends(self):
        friendships = Friendship.objects.filter(
            (Q(from_user=self) | Q(to_user=self)) & Q(is_accepted=True)
        )
        return [f.to_user if f.from_user == self else f.from_user for f in friendships]


class FriendshipManager(models.Manager):
    def send_request(self, from_user, to_user):
        if from_user == to_user:
            raise ValidationError("You cannot send a friend request to yourself.")

        # Check if there is a blocked relationship
        if self.filter(from_user=from_user, to_user=to_user, is_blocked=True).exists() or \
                self.filter(from_user=to_user, to_user=from_user, is_blocked=True).exists():
            raise ValidationError("Cannot send the request because the profile is blocked.")

        if self.filter(from_user=from_user, to_user=to_user).exists():
            raise ValidationError("Friend request already sent.")
        if self.filter(from_user=to_user, to_user=from_user).exists():
            raise ValidationError("The other user has already sent a friend request.")

        with transaction.atomic():
            friendship = self.create(from_user=from_user, to_user=to_user, is_accepted=False)
            UserActivity.objects.create(user=from_user, activity_type='FRIEND_REQUEST_SENT', target_user=to_user)
            return friendship

    def accept_request(self, request_id):
        try:
            friend_request = self.get(id=request_id)
            friend_request.accept()
        except Friendship.DoesNotExist:
            raise ValidationError("Friend request not found.")

    def reject_request(self, request_id):
        try:
            friend_request = self.get(id=request_id)
            friend_request.reject()
        except Friendship.DoesNotExist:
            raise ValidationError("Friend request not found.")

    def block_user(self, from_user, to_user):
        friendship, created = self.get_or_create(from_user=from_user, to_user=to_user)
        friendship.block()

    def unblock_user(self, from_user, to_user):
        try:
            friendship = self.get(from_user=from_user, to_user=to_user)
            if friendship.is_blocked:
                friendship.unblock()
        except Friendship.DoesNotExist:
            raise ValidationError("Friendship does not exist or user is not blocked.")


# Friendship model
class Friendship(models.Model):
    from_user = models.ForeignKey(User, related_name='friend_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='friend_requests_received', on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = FriendshipManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['from_user', 'to_user'], name='unique_friendship')
        ]

    def accept(self):
        self.is_accepted = True
        self.save()

        cache.delete(f'friends_list_{self.from_user.id}')
        cache.delete(f'friends_list_{self.to_user.id}')

        self.update_cache_for_users()
        UserActivity.objects.create(user=self.to_user, activity_type='FRIEND_REQUEST_ACCEPTED', target_user=self.from_user)

    def update_cache_for_users(self):
        # Helper function to refresh the cache for both users
        from .serializers import FriendSerializer

        for user in [self.from_user, self.to_user]:
            friendships = Friendship.objects.filter(
                (Q(from_user=user) | Q(to_user=user)) & Q(is_accepted=True)
            ).select_related('from_user', 'to_user')

            friends = [
                friendship.to_user if friendship.from_user == user else friendship.from_user
                for friendship in friendships
            ]

            serializer = FriendSerializer(friends, many=True)
            cache.set(f'friends_list_{user.id}', serializer.data, timeout=3600)

    def reject(self):
        self.delete()
        UserActivity.objects.create(user=self.to_user, activity_type='FRIEND_REQUEST_REJECTED', target_user=self.from_user)


    def block(self):
        self.is_blocked = True
        self.save()
        UserActivity.objects.create(user=self.to_user, activity_type='USER_BLOCKED', target_user=self.from_user)


    def unblock(self):
        self.is_blocked = False
        self.save()
        UserActivity.objects.create(user=self.to_user, activity_type='USER_UNBLOCKED', target_user=self.from_user)



class UserActivity(models.Model):
    ACTIVITY_CHOICES = (
        ('FRIEND_REQUEST_SENT', 'Friend request sent'),
        ('FRIEND_REQUEST_ACCEPTED', 'Friend request accepted'),
        ('FRIEND_REQUEST_REJECTED', 'Friend request rejected'),
        ('USER_BLOCKED', 'Blocked'),
        ('USER_UNBLOCKED', 'Unblocked'),
    )

    user = models.ForeignKey(User, related_name='activities', on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    target_user = models.ForeignKey(User, related_name='targeted_activities', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (f"From User : {self.user.email}, \n"
                f"Action : {self.activity_type}, \n"
                f"To User :  {self.target_user.email}")