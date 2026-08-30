from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Profilbild / Avatar")
    is_herrklubb_member = models.BooleanField(default=False, help_text="True if user is one of the 11 original Herrklubben members")

    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return None

    def __str__(self):
        display_name = self.user.get_full_name() or self.user.email
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
            'text': self.title,
            'dates': f"{start_str}/{end_str}",
            'details': "\n\n".join(desc_parts),
            'location': self.location or "",
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
            'subject': self.title,
            'startdt': start_str,
            'enddt': end_str,
            'allday': is_allday,
            'body': "\n\n".join(desc_parts),
            'location': self.location or "",
        }
        return f"https://outlook.live.com/calendar/0/deeplink/compose?{urlencode(params)}"
