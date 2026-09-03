from django.contrib import admin
from django.contrib.auth.models import User
from .models import (
    UserProfile, BucketCategory, BucketItem, BucketVote, BucketDream,
    UserUnavailability, HerrklubbEvent, PhotoAlbum, Photo, PhotoLike
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_herrklubb_member')
    list_filter = ('is_herrklubb_member',)
    list_editable = ('is_herrklubb_member',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(BucketCategory)
class BucketCategoryAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'order')
    list_editable = ('order',)


@admin.register(BucketItem)
class BucketItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'get_vote_count', 'get_total_points', 'is_completed', 'created_by', 'created_at')
    list_filter = ('category', 'is_completed')
    search_fields = ('title', 'description')
    list_editable = ('is_completed',)

    @admin.display(description="Vote Count")
    def get_vote_count(self, obj):
        return obj.vote_count

    @admin.display(description="Total Points")
    def get_total_points(self, obj):
        return obj.total_points


@admin.register(BucketVote)
class BucketVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'marker', 'created_at')
    list_filter = ('marker',)
    search_fields = ('user__username', 'item__title')


@admin.register(BucketDream)
class BucketDreamAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'created_at')
    search_fields = ('user__username', 'item__title')


@admin.register(UserUnavailability)
class UserUnavailabilityAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_date', 'end_date', 'reason', 'created_at')
    list_filter = ('start_date', 'user')
    search_fields = ('user__username', 'reason')


@admin.register(HerrklubbEvent)
class HerrklubbEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'event_date', 'end_date', 'location', 'is_active', 'created_by')
    list_filter = ('is_active', 'event_date')
    search_fields = ('title', 'description', 'location')
    list_editable = ('is_active',)


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 0
    fields = ('image', 'caption', 'uploader', 'taken_at')
    readonly_fields = ('taken_at',)


@admin.register(PhotoAlbum)
class PhotoAlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'folder_date', 'get_photo_count', 'created_by', 'created_at')
    list_filter = ('category', 'folder_date')
    search_fields = ('title', 'description')
    inlines = [PhotoInline]

    @admin.display(description="Antal Foton")
    def get_photo_count(self, obj):
        return obj.photo_count


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'album', 'uploader', 'caption', 'taken_at', 'created_at')
    list_filter = ('album', 'uploader', 'created_at')
    search_fields = ('caption', 'uploader__username', 'album__title')
    filter_horizontal = ('tagged_members',)


@admin.register(PhotoLike)
class PhotoLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'photo', 'created_at')
    list_filter = ('created_at',)