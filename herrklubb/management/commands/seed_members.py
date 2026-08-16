from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Q
from herrklubb.models import UserProfile

class Command(BaseCommand):
    help = "Seeds the initial 11 members of Toarps Herrklubb into the database with default passwords [surname]2026."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Toarps Herrklubb members...")

        personas = [
            {
                "full_name": "Johan Siedberg",
                "email": "johan.siedberg@gmail.com"
            },
            {
                "full_name": "Mikael Dahl",
                "email": "mikael@dahl.se"
            },
            {
                "full_name": "Andreas Larsson",
                "email": "andreas@larsson.se"
            },
            {
                "full_name": "Johan Svensson",
                "email": "svenjohansvensson@gmail.com"
            },
            {
                "full_name": "Johan Meldo",
                "email": "johan@meldo.se"
            },
            {
                "full_name": "Erik Svensson",
                "email": "erik.sve@hotmail.com"
            },
            {
                "full_name": "Christoffer Ericsson",
                "email": "coff_erics@yahoo.se"
            },
            {
                "full_name": "Martin Gustafsson",
                "email": "martin@gustafsson.se"
            },
            {
                "full_name": "Tommy Lycen",
                "email": "tommy@lycen.se"
            },
            {
                "full_name": "Tommy Källberg",
                "email": "anymaztic@hotmail.com"
            },
            {
                "full_name": "Martin Krantz",
                "email": "martin@krantz.se"
            }
        ]

        created_count = 0
        updated_count = 0
        active_member_user_ids = []

        for p in personas:
            full_name = p['full_name']
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else name_parts[0]

            surname_clean = last_name.lower().replace('ä', 'a').replace('å', 'a').replace('ö', 'o').replace(' ', '')
            first_name_clean = first_name.lower().replace('ä', 'a').replace('å', 'a').replace('ö', 'o').replace(' ', '')
            email = p['email'].strip().lower()
            old_email_pattern = f"{first_name_clean}@{surname_clean}.se"
            username = email
            password = f"{surname_clean}2026"

            # Match user by exact full name or emails
            user = (
                User.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).first() or
                User.objects.filter(email__iexact=email).first() or
                User.objects.filter(username__iexact=email).first() or
                User.objects.filter(email__iexact=old_email_pattern).first() or
                User.objects.filter(username__iexact=old_email_pattern).first()
            )

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

            active_member_user_ids.append(user.id)

            if created:
                created_count += 1
            else:
                updated_count += 1

        # Ensure only the 11 active personas are flagged as Herrklubb members
        UserProfile.objects.exclude(user_id__in=active_member_user_ids).update(is_herrklubb_member=False)

        # Clean up obsolete duplicate accounts without associated data
        User.objects.filter(username='johansiedberg').exclude(id__in=active_member_user_ids).delete()

        self.stdout.write(self.style.SUCCESS(
            f"Successfully processed {len(personas)} members ({created_count} created, {updated_count} updated). Active Herrklubb members: {len(active_member_user_ids)}."
        ))
