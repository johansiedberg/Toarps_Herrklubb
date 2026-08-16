from django.core.management.base import BaseCommand
from herrklubb.models import BucketCategory, BucketItem

class Command(BaseCommand):
    help = "Seeds initial Herrklubben Bucket List categories and suggested events without modifying user votes or dreams."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Herrklubben Bucket List suggested events...")

        categories_data = [
            {
                "name": "Sport & Stora Evenemang",
                "icon": "⚽",
                "order": 1,
                "items": [
                    ("Fotbollsresa: Serie A (Italien)", "T.ex. Milano-derby eller Rom-resa för klassisk italiensk läktarkultur."),
                    ("Fotbollsresa: Premier League (England)", "London eller Manchester – äkta brittisk fotbollspub och matchdag."),
                    ("Fotbollsresa: Bundesliga (Tyskland)", "Dortmund / Gelbe Wand eller München med episkt arrangemang."),
                    ("Fotbollsresa: Old Firm (Skottland)", "Celtic vs Rangers i Glasgow – ett av världens mäktigaste derbyn."),
                    ("Fotbollsresa: EM eller VM", "Landslagsturnering live från läktaren."),
                    ("Stockholmsderby", "AIK, Hammarby eller Djurgården i ett kokande allsvenskt derby."),
                    ("Formel 1-lopp", "Live Grand Prix med motorljud och VIP-stämning."),
                    ("NHL-match & Nordamerika", "Ishockeyresa till USA/Kanada för NHL i världsklass."),
                    ("Tennis Grand Slam & Event", "Franska Öppna (Paris), Australian Open eller Tennisveckan i Båstad."),
                    ("Övrig Elitsport", "Hockey-VM eller Handboll i Kiel."),
                ]
            },
            {
                "name": "Äventyr, Natur & Vinter",
                "icon": "🏔️",
                "order": 2,
                "items": [
                    ("Norgeresa till Coffe", "Vandring, fjäll & storslagna norska äventyr."),
                    ("Island", "Vulkaner, gejsrar, varma källor & naturupplevelser."),
                    ("Bestiga Kebnekaise", "Utmaning och toppbestigning på Sveriges högsta berg."),
                    ("Svensk Hajk & Friluftsliv", "Övernattning i vildmarken, fiske och lägereld."),
                    ("Skidresa", "Alperna eller klassiska fjällen för skidåkning & after-ski."),
                ]
            },
            {
                "name": "Temaresor: Mat, Dryck & Kultur",
                "icon": "🍺",
                "order": 3,
                "items": [
                    ("Oktoberfest i München", "Lederhosen, ölsejdlar och stämning i bayerska tält."),
                    ("Skottland: Whiskyresa", "Destilleriturer, provningar och skotsk kultur."),
                    ("Toscana: Vin- & Matresa", "Matlagningskurser, vingårdar och italiensk njutning."),
                    ("Sunkiga hak i Göteborg", "Klassisk barrunda och pubkväll bland Göteborgs legendariska och opretentiösa hak."),
                ]
            },
            {
                "name": "Storstadsresor & Weekend",
                "icon": "🏙️",
                "order": 4,
                "items": [
                    ("Europa Storstad", "Weekend i Prag, Warszawa, Budapest, Bukarest eller Florens."),
                    ("Nordisk Weekend", "Oslo, Gotland eller Tylösand."),
                    ("Sydeuropa & Sol", "Barcelona, Sicilien eller 1 vecka sol & charter."),
                    ("Las Vegas & Kuba", "Långväga äventyr – casino i Vegas eller Kuba-resa."),
                ]
            },
            {
                "name": "Gemenskap & Snabba Event",
                "icon": "🎉",
                "order": 5,
                "items": [
                    ("Hyra Hus tillsammans", "Gemensam hussemester vid havet eller sjö."),
                    ("Konsert & Live-event", "Storkonsert eller festival tillsammans."),
                    ("Helg-Pokerkväll", "Klassisk pokerturnering med middag & god dryck."),
                ]
            }
        ]

        total_items_created = 0
        total_items_updated = 0

        for cat_info in categories_data:
            cat, _ = BucketCategory.objects.get_or_create(
                name=cat_info["name"],
                defaults={"icon": cat_info["icon"], "order": cat_info["order"]}
            )
            cat.icon = cat_info["icon"]
            cat.order = cat_info["order"]
            cat.save()

            for item_title, item_desc in cat_info["items"]:
                item, created = BucketItem.objects.get_or_create(
                    title=item_title,
                    defaults={"description": item_desc, "category": cat}
                )
                if not created and item.category != cat:
                    item.category = cat
                    item.description = item_desc
                    item.save()
                    total_items_updated += 1
                elif created:
                    total_items_created += 1

        total_items = BucketItem.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded categories and suggested events ({total_items_created} created, {total_items_updated} updated). Total events in database: {total_items}."
        ))
