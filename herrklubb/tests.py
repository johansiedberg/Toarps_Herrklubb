from django.test import TestCase
from django.contrib.auth.models import User
from herrklubb.models import (
    BucketCategory, BucketItem, BucketVote, BucketDream, UserProfile
)

class HerrklubbTestCase(TestCase):
    def setUp(self):
        # Create a test member
        self.member = User.objects.create_user('john', 'john@test.com', 'password', first_name='John', last_name='Doe')
        self.member.profile.is_herrklubb_member = True
        self.member.profile.save()

        # Create category & item
        self.cat = BucketCategory.objects.create(name='Resor', icon='✈️', order=1)
        self.item1 = BucketItem.objects.create(title='Serie A Fotbollsresa', category=self.cat)
        self.item2 = BucketItem.objects.create(title='Formel 1', category=self.cat)

    def test_marker_point_values(self):
        BucketVote.objects.create(user=self.member, item=self.item1, marker='SVART')
        self.assertEqual(self.item1.total_points, 100)
        self.assertEqual(self.item1.vote_count, 1)
        self.assertFalse(self.item1.is_planerad)

    def test_majority_threshold_to_planerad(self):
        # Create 6 distinct members and vote on item1
        for i in range(6):
            u = User.objects.create_user(f'user_{i}', f'u{i}@test.com', 'password')
            u.profile.is_herrklubb_member = True
            u.profile.save()
            BucketVote.objects.create(user=u, item=self.item1, marker='ROD')

        self.assertEqual(self.item1.vote_count, 6)
        self.assertTrue(self.item1.is_planerad)

    def test_freed_votes_on_completion(self):
        vote = BucketVote.objects.create(user=self.member, item=self.item1, marker='SVART')
        self.item1.is_completed = True
        self.item1.save()

        # Active votes count for uncompleted items
        active_votes = BucketVote.objects.filter(user=self.member, item__is_completed=False)
        self.assertEqual(active_votes.count(), 0)

    def test_herrklubb_access_control(self):
        # External user should be blocked from /herrklubb/
        external = User.objects.create_user('external', 'ext@test.com', 'password')
        self.client.login(username='external', password='password')
        response = self.client.get('/herrklubb/')
        self.assertEqual(response.status_code, 302) # redirected to SSO predictions login
        self.assertIn('/predictions/login/', response.url)

    def test_wan_https_access(self):
        # Simulate request over WAN via Caddy HTTPS reverse proxy on port 1981
        self.client.login(username='john', password='password')
        response = self.client.get(
            '/hub/',
            HTTP_HOST='217.31.171.173:1981',
            HTTP_X_FORWARDED_PROTO='https',
            secure=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Toarps HK Herrklubb')

