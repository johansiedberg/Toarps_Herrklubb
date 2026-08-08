import json, os
from django.db import migrations

def seed_initial_data(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('tournament', 'UserProfile')
    
    # Path to personas JSON relative to project root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    personas_path = os.path.join(base_dir, 'tournament', 'editorial_engine', 'player_personas.json')
    
    if not os.path.exists(personas_path):
        return

    with open(personas_path, 'r', encoding='utf-8') as f:
        personas = json.load(f)

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

        if hasattr(user, 'set_password'):
            user.set_password(password)
            user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_herrklubb_member = True
        profile.save()

def reverse_initial_data(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0034_matchprediction_prediction_phase_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_initial_data, reverse_initial_data),
    ]
