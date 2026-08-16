from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from herrklubb.models import UserProfile

class Command(BaseCommand):
    help = "Seeds the initial 11 members of Toarps Herrklubb into the database with default passwords [surname]2026."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Toarps Herrklubb members...")

        personas = [
            {
                "id": 1,
                "full_name": "Johan Siedberg",
                "email": "johan.siedberg@gmail.com"
            },
            {
                "id": 2,
                "full_name": "Mikael Dahl",
                "email": "mikael@dahl.se"
            },
            {
                "id": 3,
                "full_name": "Andreas Larsson",
                "email": "andreas@larsson.se"
            },
            {
                "id": 4,
                "full_name": "Johan Svensson",
                "email": "svenjohansvensson@gmail.com"
            },
            {
                "id": 5,
                "full_name": "Johan Meldo",
                "email": "johan@meldo.se"
            },
            {
                "id": 6,
                "full_name": "Erik Svensson",
                "email": "erik.sve@hotmail.com"
            },
            {
                "id": 7,
                "full_name": "Christoffer Ericsson",
                "email": "coff_erics@yahoo.se"
            },
            {
                "id": 8,
                "full_name": "Martin Gustafsson",
                "email": "martin@gustafsson.se"
            },
            {
                "id": 9,
                "full_name": "Tommy Lycen",
                "email": "tommy@lycen.se"
            },
            {
                "id": 10,
                "full_name": "Tommy Källberg",
                "email": "anymaztic@hotmail.com"
            },
            {
                "id": 11,
                "full_name": "Martin Krantz",
                "email": "martin@krantz.se"
            }
        ]

        created_count = 0
        updated_count = 0

        for p in personas:
            full_name = p['full_name']
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else name_parts[0]

            surname_clean = last_name.lower().replace('ä', 'a').replace('å', 'a').replace('ö', 'o').replace(' ', '')
            email = p['email'].strip().lower()
            username = email
            password = f"{surname_clean}2026"

            # Match user by pk, email, or first_name & last_name
            user = (
                User.objects.filter(pk=p['id']).first() or
                User.objects.filter(email__iexact=email).first() or
                User.objects.filter(first_name=first_name, last_name=last_name).first()
            )

            if not user:
                user = User.objects.create(
                    pk=p['id'],
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
            f"Successfully processed {len(personas)} members ({created_count} created, {updated_count} updated)."
        ))
