import json, os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tournament.models import UserProfile

class Command(BaseCommand):
    help = "Seeds the initial 11 members of Toarps Herrklubb into the database with default passwords [surname]2026."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Toarps Herrklubb members...")

        personas_path = os.path.join('tournament', 'editorial_engine', 'player_personas.json')
        if not os.path.exists(personas_path):
            self.stdout.write(self.style.ERROR(f"Personas file not found at {personas_path}"))
            return

        with open(personas_path, 'r', encoding='utf-8') as f:
            personas = json.load(f)

        created_count = 0
        updated_count = 0

        for p in personas:
            full_name = p['full_name']
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else name_parts[0]

            surname_clean = last_name.lower().replace('ä', 'a').replace('å', 'a').replace('ö', 'o').replace(' ', '')
            password = f"{surname_clean}2026"
            username = full_name.lower().replace(' ', '.').replace('ä', 'a').replace('å', 'a').replace('ö', 'o')
            email = f"{username}@toarpsherrklubb.se"

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'is_active': True,
                }
            )

            user.set_password(password)
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.is_herrklubb_member = True
            profile.save()

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully processed {len(personas)} members ({created_count} created, {updated_count} passwords updated)."
        ))
