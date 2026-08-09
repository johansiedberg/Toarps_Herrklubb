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

            first_name_clean = first_name.lower().replace('ä', 'a').replace('å', 'a').replace('ö', 'o').replace(' ', '')
            surname_clean = last_name.lower().replace('ä', 'a').replace('å', 'a').replace('ö', 'o').replace(' ', '')
            
            email = f"{first_name_clean}@{surname_clean}.se"
            username = email
            password = f"{surname_clean}2026"

            user = User.objects.filter(email=email).first()
            if not user:
                old_username = full_name.lower().replace(' ', '.').replace('ä', 'a').replace('å', 'a').replace('ö', 'o')
                user = User.objects.filter(username=old_username).first()

            if not user:
                user = User.objects.create(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    is_active=True
                )
                created = True
            else:
                created = False
                user.username = username
                user.email = email
                user.first_name = first_name
                user.last_name = last_name

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
