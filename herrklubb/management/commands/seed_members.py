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
                "first_name": "Johan",
                "last_name": "Siedberg",
                "nickname": "Szabo",
                "email": "johan.siedberg@gmail.com",
                "old_emails": ["johan.siedberg@siedberg.se", "johan@siedberg.se"]
            },
            {
                "first_name": "Mikael",
                "last_name": "Dahl",
                "nickname": "Dahl",
                "email": "mikaeld81@gmail.com",
                "old_emails": ["mikael@dahl.se"]
            },
            {
                "first_name": "Andreas",
                "last_name": "Larsson",
                "nickname": "Lage",
                "email": "senasa9@gmail.com",
                "old_emails": ["andreas@larsson.se"]
            },
            {
                "first_name": "Johan",
                "last_name": "Svensson",
                "nickname": "Svensson",
                "email": "svenjohansvensson@gmail.com",
                "old_emails": ["johan@svensson.se"]
            },
            {
                "first_name": "Johan",
                "last_name": "Meldo",
                "nickname": "Meldo",
                "email": "jmeldo@gmail.com",
                "old_emails": ["johan@meldo.se"]
            },
            {
                "first_name": "Erik",
                "last_name": "Svensson",
                "nickname": "Erik",
                "email": "erik.sve@hotmail.com",
                "old_emails": ["erik@svensson.se"]
            },
            {
                "first_name": "Christoffer",
                "last_name": "Ericsson",
                "nickname": "Coffe",
                "email": "coff_erics@yahoo.se",
                "old_emails": ["christoffer@ericsson.se"]
            },
            {
                "first_name": "Martin",
                "last_name": "Gustafson",
                "nickname": "Göransson",
                "email": "martin.gustafson1@gmail.com",
                "old_emails": ["martin@gustafsson.se", "martin.gustafsson@gmail.com", "martin@gustafson.se", "martin.gustafsson@gustafsson.se"],
                "old_last_names": ["Gustafsson"]
            },
            {
                "first_name": "Tommy",
                "last_name": "Lycen",
                "nickname": "Lycet",
                "email": "t.lycen@gmail.com",
                "old_emails": ["tommy@lycen.se", "tommy.lycen@lycen.se"]
            },
            {
                "first_name": "Tommy",
                "last_name": "Källberg",
                "nickname": "Käbbe",
                "email": "anymaztic@hotmail.com",
                "old_emails": ["tommy@kallberg.se", "tommy@kaellberg.se"]
            },
            {
                "first_name": "Martin",
                "last_name": "Krantz",
                "nickname": "Krantz",
                "email": "martin@meritel.se",
                "old_emails": ["martin@krantz.se"]
            }
        ]

        created_count = 0
        updated_count = 0
        active_member_user_ids = []

        for p in personas:
            first_name = p['first_name']
            last_name = p['last_name']
            nickname = p.get('nickname')
            email = p['email'].strip().lower()
            surname_clean = last_name.lower().replace('ä', 'a').replace('å', 'a').replace('ö', 'o').replace(' ', '')
            username = email
            password = f"{surname_clean}2026"

            q = Q(email__iexact=email) | Q(username__iexact=email) | Q(first_name__iexact=first_name, last_name__iexact=last_name)
            for old_e in p.get('old_emails', []):
                q |= Q(email__iexact=old_e) | Q(username__iexact=old_e)
            for old_ln in p.get('old_last_names', []):
                q |= Q(first_name__iexact=first_name, last_name__iexact=old_ln)

            user = User.objects.filter(q).first()

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
            if nickname:
                profile.nickname = nickname
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
