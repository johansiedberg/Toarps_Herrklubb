from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name="Smeknamn")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Profilbild / Avatar")
    is_herrklubb_member = models.BooleanField(default=False, help_text="True if user is one of the 11 original Herrklubben members")

    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return None

    def get_nickname(self):
        if self.nickname and self.nickname.strip():
            return self.nickname.strip()
        return self.user.first_name or self.user.username

    def __str__(self):
        display_name = self.get_nickname() or self.user.get_full_name() or self.user.email
        return f"Profil för {display_name} (Herrklubb: {self.is_herrklubb_member})"


@receiver(post_save, sender=User)
def auto_create_user_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)


# --- HERRKLUBBEN BUCKET LIST MODELS ---

class BucketCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default="🪣")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Bucket Category"
        verbose_name_plural = "Bucket Categories"

    def __str__(self):
        return f"{self.icon} {self.name}"

    @property
    def open_items(self):
        return self.items.filter(is_completed=False).order_by('title')


class BucketItem(models.Model):
    title = models.CharField(max_length=200)
    category = models.ForeignKey(BucketCategory, on_delete=models.CASCADE, related_name='items')
    description = models.TextField(blank=True, help_text="Valfri beskrivning av aktiviteten")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_bucket_items')
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def total_points(self):
        pts = 0
        for v in self.votes.all():
            if v.marker == 'SVART':
                pts += 100
            elif v.marker == 'GRON':
                pts += 50
            elif v.marker == 'ROD':
                pts += 25
        return pts

    @property
    def vote_count(self):
        return self.votes.values('user').distinct().count()

    @property
    def count_svart(self):
        return self.votes.filter(marker='SVART').count()

    @property
    def count_gron(self):
        return self.votes.filter(marker='GRON').count()

    @property
    def count_rod(self):
        return self.votes.filter(marker='ROD').count()

    @property
    def is_planerad(self):
        return self.vote_count >= 6 and not self.is_completed

    @property
    def dream_users(self):
        return [d.user for d in self.dreams.select_related('user').all()]


class BucketVote(models.Model):
    MARKER_CHOICES = [
        ('SVART', 'Svart Marker (100)'),
        ('GRON', 'Grön Marker (50)'),
        ('ROD', 'Röd Marker (25)'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bucket_votes')
    item = models.ForeignKey(BucketItem, on_delete=models.CASCADE, related_name='votes')
    marker = models.CharField(max_length=10, choices=MARKER_CHOICES)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bucket Vote"
        verbose_name_plural = "Bucket Votes"

    def __str__(self):
        display_name = self.user.get_full_name() or self.user.email
        return f"{display_name} -> {self.item.title} ({self.marker})"


class BucketDream(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bucket_dreams')
    item = models.ForeignKey(BucketItem, on_delete=models.CASCADE, related_name='dreams')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bucket Dream (Högsta Dröm)"
        verbose_name_plural = "Bucket Dreams (Högsta Dröm)"

    def __str__(self):
        display_name = self.user.get_full_name() or self.user.email
        return f"🪣 {display_name}'s Högsta Dröm -> {self.item.title}"


# --- HERRKLUBBEN CALENDAR AND EVENT MODELS ---

class UserUnavailability(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unavailabilities')
    start_date = models.DateField(verbose_name="Startdatum")
    end_date = models.DateField(verbose_name="Slutdatum")
    reason = models.CharField(max_length=255, blank=True, null=True, verbose_name="Anledning (Valfritt)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']
        verbose_name = "Hinder / Frånvaro"
        verbose_name_plural = "Hinder / Frånvaro"

    def __str__(self):
        display_name = self.user.get_full_name() or self.user.email
        return f"{display_name}: {self.start_date} - {self.end_date}"


class HerrklubbEvent(models.Model):
    title = models.CharField(max_length=200, verbose_name="Aktivitetsnamn")
    category = models.ForeignKey(BucketCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    description = models.TextField(blank=True, verbose_name="Beskrivning")
    event_date = models.DateField(null=True, blank=True, verbose_name="Startdatum")
    end_date = models.DateField(null=True, blank=True, verbose_name="Slutdatum")
    event_time = models.TimeField(null=True, blank=True, verbose_name="Tid")
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Plats")
    coordinators = models.ManyToManyField(User, related_name='coordinated_events', blank=True, verbose_name="Samordnare")
    participants = models.ManyToManyField(User, related_name='participating_events', blank=True, verbose_name="Deltagare (Ja)")
    participants_no = models.ManyToManyField(User, related_name='not_participating_events', blank=True, verbose_name="Deltagare (Nej)")
    bucket_items = models.ManyToManyField(BucketItem, related_name='linked_events', blank=True, verbose_name="Kopplade förslag/hinkmål")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_events')
    is_active = models.BooleanField(default=True, help_text="Visas som Nästa Event")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['event_date', '-created_at']
        verbose_name = "Herrklubb Event"
        verbose_name_plural = "Herrklubb Events"

    def __str__(self):
        return f"Event: {self.title} ({self.event_date or 'Inget datum'})"

    @property
    def google_calendar_url(self):
        if not self.event_date:
            return "#"
        from urllib.parse import urlencode
        from datetime import timedelta
        
        if self.event_time:
            start_str = f"{self.event_date.strftime('%Y%m%d')}T{self.event_time.strftime('%H%M%S')}"
            if self.end_date:
                end_str = f"{self.end_date.strftime('%Y%m%d')}T{self.event_time.strftime('%H%M%S')}"
            else:
                end_str = f"{self.event_date.strftime('%Y%m%d')}T235959"
        else:
            start_str = self.event_date.strftime('%Y%m%d')
            end_date = (self.end_date or self.event_date) + timedelta(days=1)
            end_str = end_date.strftime('%Y%m%d')
            
        desc_parts = []
        if self.category:
            desc_parts.append(f"Kategori: {self.category.name}")
        if self.description:
            desc_parts.append(self.description)
            
        params = {
            'action': 'TEMPLATE',
            'text': f"Toarps Herrklubb: {self.title}",
            'dates': f"{start_str}/{end_str}",
            'details': "\n\n".join(desc_parts),
            'location': self.location or "",
            'trp': 'true',
            'crm': 'BUSY',
        }
        return f"https://calendar.google.com/calendar/render?{urlencode(params)}"

    @property
    def outlook_calendar_url(self):
        if not self.event_date:
            return "#"
        from urllib.parse import urlencode
        from datetime import timedelta
        
        if self.event_time:
            start_str = f"{self.event_date.strftime('%Y-%m-%d')}T{self.event_time.strftime('%H:%M:%S')}"
            if self.end_date:
                end_str = f"{self.end_date.strftime('%Y-%m-%d')}T{self.event_time.strftime('%H:%M:%S')}"
            else:
                end_str = f"{self.event_date.strftime('%Y-%m-%d')}T23:59:59"
            is_allday = "false"
        else:
            start_str = self.event_date.strftime('%Y-%m-%d')
            end_date = (self.end_date or self.event_date) + timedelta(days=1)
            end_str = end_date.strftime('%Y-%m-%d')
            is_allday = "true"
            
        desc_parts = []
        if self.category:
            desc_parts.append(f"Kategori: {self.category.name}")
        if self.description:
            desc_parts.append(self.description)
            
        params = {
            'path': '/calendar/action/compose',
            'rru': 'addevent',
            'subject': f"Toarps Herrklubb: {self.title}",
            'startdt': start_str,
            'enddt': end_str,
            'allday': is_allday,
            'body': "\n\n".join(desc_parts),
            'location': self.location or "",
            'freebusy': 'busy',
        }
        return f"https://outlook.live.com/calendar/0/deeplink/compose?{urlencode(params)}"


# --- HERRKLUBBEN PHOTO SHARING & GALLERY MODELS ---

import os
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, ExifTags


class PhotoAlbum(models.Model):
    title = models.CharField(max_length=200, verbose_name="Albumnamn / Mappnamn")
    description = models.TextField(blank=True, verbose_name="Beskrivning / Notering")
    event = models.ForeignKey(HerrklubbEvent, on_delete=models.SET_NULL, null=True, blank=True, related_name='photo_albums', verbose_name="Kopplat Event")
    category = models.ForeignKey(BucketCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='photo_albums', verbose_name="Kategori")
    folder_date = models.DateField(null=True, blank=True, verbose_name="Datum för aktivitet/resa")
    cover_photo = models.ForeignKey('Photo', on_delete=models.SET_NULL, null=True, blank=True, related_name='cover_for_albums', verbose_name="Omslagsbild")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_photo_albums', verbose_name="Skapad av")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Skapat datum")

    class Meta:
        ordering = ['-folder_date', '-created_at']
        verbose_name = "Fotoalbum / Mapp"
        verbose_name_plural = "Fotoalbum & Mappar"

    def __str__(self):
        date_part = f" ({self.folder_date.strftime('%Y-%m')})" if self.folder_date else ""
        return f"📁 {self.title}{date_part}"

    @property
    def photo_count(self):
        return self.photos.count()

    def get_signature_photo(self):
        """
        Title/Signature photo of an Album is always the photo with the most tagged members.
        If there are multiple with the same count, choose the first uploaded in the album.
        """
        from django.db.models import Count
        return self.photos.annotate(
            tagged_count=Count('tagged_members')
        ).order_by('-tagged_count', 'created_at', 'id').first()

    def get_cover_url(self):
        photo = self.get_signature_photo()
        if photo:
            if photo.thumbnail:
                return photo.thumbnail.url
            if photo.image:
                return photo.image.url
        return None

    @property
    def contributors(self):
        user_ids = self.photos.values_list('uploader_id', flat=True).distinct()
        return User.objects.filter(id__in=user_ids).select_related('profile')


class Photo(models.Model):
    album = models.ForeignKey(PhotoAlbum, on_delete=models.CASCADE, related_name='photos', verbose_name="Album / Mapp")
    image = models.ImageField(upload_to='albums/%Y/%m/', verbose_name="Originalbild")
    thumbnail = models.ImageField(upload_to='albums/thumbnails/%Y/%m/', blank=True, null=True, verbose_name="Miniatyrbild")
    caption = models.CharField(max_length=255, blank=True, verbose_name="Bildtext")
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_photos', verbose_name="Uppladdad av")
    tagged_members = models.ManyToManyField(User, related_name='tagged_photos', blank=True, verbose_name="Taggade medlemmar")
    taken_at = models.DateTimeField(null=True, blank=True, verbose_name="Fotograferad tidpunkt")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Uppladdad tidpunkt")

    class Meta:
        ordering = ['-taken_at', '-created_at']
        verbose_name = "Foto"
        verbose_name_plural = "Foton"

    def __str__(self):
        uploader_name = self.uploader.profile.get_nickname() if hasattr(self.uploader, 'profile') else self.uploader.username
        return f"Foto i {self.album.title} av {uploader_name}"

    @property
    def filename(self):
        return os.path.basename(self.image.name) if self.image else ""

    @property
    def display_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        return self.image.url if self.image else ""

    @property
    def like_count(self):
        return self.likes.count()

    def is_liked_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()

    def generate_thumbnail_and_metadata(self):
        if not self.image:
            return
        try:
            self.image.seek(0)
            img = Image.open(self.image)

            # Auto-rotate image according to EXIF Orientation tag
            img = ImageOps.exif_transpose(img)

            # Extract EXIF taken_at if not already populated
            if not self.taken_at:
                try:
                    exif_data = img.getexif()
                    if exif_data:
                        date_str = exif_data.get(36867) or exif_data.get(306)
                        if date_str:
                            from datetime import datetime
                            from django.utils import timezone
                            clean_str = str(date_str).strip()[:19]
                            dt = datetime.strptime(clean_str, "%Y:%m:%d %H:%M:%S")
                            if timezone.is_naive(dt):
                                dt = timezone.make_aware(dt)
                            self.taken_at = dt
                except Exception:
                    pass

            # Generate high-quality WebP thumbnail (max 800x800 preserving aspect ratio)
            thumb_img = img.copy()
            thumb_img.thumbnail((800, 800), Image.Resampling.LANCZOS)

            # Ensure RGB mode for clean WebP compression
            if thumb_img.mode != "RGB":
                thumb_img = thumb_img.convert("RGB")

            thumb_io = BytesIO()
            thumb_img.save(thumb_io, format='WEBP', quality=85, optimize=True)
            thumb_io.seek(0)

            base_name = os.path.splitext(os.path.basename(self.image.name))[0]
            thumb_filename = f"thumb_{base_name}.webp"
            self.thumbnail.save(thumb_filename, ContentFile(thumb_io.getvalue()), save=False)
        except Exception as e:
            # Fallback gracefully if image library fails on unsupported raw formats
            pass


class PhotoLike(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photo_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('photo', 'user')
        verbose_name = "Foto-gilla"
        verbose_name_plural = "Foto-gillamarkeringar"

    def __str__(self):
        return f"{self.user.username} gillar foto #{self.photo_id}"

