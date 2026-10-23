"""Weather presentation and a small, date-rotated collection of daily reading."""
import json
from urllib.parse import urlencode

# Exact excerpts with attribution, rather than generated or anonymous quotations.
QUOTES = [
    ('Nothing can bring you peace but yourself.', 'Ralph Waldo Emerson, Self-Reliance'),
    ('Men are disturbed not by things, but by the views which they take of things.',
     'Epictetus, Enchiridion 5, trans. Elizabeth Carter'),
    ('Only that day dawns to which we are awake.', 'Henry David Thoreau, Walden, Conclusion'),
    ('No man can live happily who regards himself alone, and transforms everything into a question of his own utility.',
     'Seneca, Moral Letters 48, trans. Richard M. Gummere'),
    ('Nothing great was ever achieved without enthusiasm.', 'Ralph Waldo Emerson, Circles'),
    ('if anything is possible for man and conformable to his nature, think that this can be attained by thyself too.',
     'Marcus Aurelius, Meditations 6.19, trans. George Long (excerpt)'),
    ('Demand not that events should happen as you wish; but wish them to happen as they do happen, and you will go on well.',
     'Epictetus, Enchiridion 8, trans. Elizabeth Carter'),
]

WORDS = [
    ('equanimity', 'ee-kwuh-NIM-ih-tee', 'noun', 'Calmness and balance under pressure.',
     'She met the unexpected change with equanimity.'),
    ('salubrious', 'suh-LOO-bree-us', 'adjective', 'Promoting health or well-being.',
     'A walk along the harbor was a salubrious start to the day.'),
    ('pellucid', 'puh-LOO-sid', 'adjective', 'Clear in meaning, expression, or appearance.',
     'The teacher offered a pellucid explanation of the tides.'),
    ('eudaimonia', 'yoo-dye-MOH-nee-uh', 'noun', 'Human flourishing; living well through a life of virtue.',
     'For Aristotle, eudaimonia involves how we live, not just how we feel.'),
    ('assiduous', 'uh-SIJ-oo-us', 'adjective', 'Showing steady care, attention, and effort.',
     'Her assiduous practice made the difficult passage feel easy.'),
    ('mellifluous', 'muh-LIF-loo-us', 'adjective', 'Smooth and pleasing to hear.',
     'A mellifluous voice drifted through the open window.'),
    ('perspicacious', 'pur-spih-KAY-shus', 'adjective', 'Quick to notice and understand things clearly.',
     'The perspicacious observer spotted a seal among the rocks.'),
    ('resilience', 'rih-ZIL-yuns', 'noun', 'The ability to recover or adapt after difficulty.',
     'The community showed resilience after the storm.'),
    ('numinous', 'NOO-mih-nus', 'adjective', 'Inspiring a sense of spiritual awe or mystery.',
     'The vast night sky felt numinous.'),
    ('ameliorate', 'uh-MEEL-yuh-rayt', 'verb', 'To improve a difficult or unpleasant situation.',
     'A few thoughtful changes ameliorated the morning commute.'),
    ('convivial', 'kun-VIV-ee-ul', 'adjective', 'Friendly, lively, and sociable.',
     'The neighbors shared a convivial breakfast.'),
]

# Short educational paraphrases; source links are retained here for review.
ANIMALS = [
    ('Octopus', 'An octopus has three hearts: two pump blood to the gills, and one pumps it to the rest of the body.',
     'Smithsonian Ocean', 'https://ocean.si.edu/ocean-life/invertebrates/octopus'),
    ('Sea otter', 'Sea otters use rocks as tools to crack open hard-shelled prey such as mussels.',
     'Monterey Bay Aquarium', 'https://www.montereybayaquarium.org/animals/animals-a-to-z/sea-otter'),
    ('Seahorse', 'Male seahorses carry developing young in a brood pouch and give birth to the babies.',
     'NOAA Ocean Service', 'https://oceanservice.noaa.gov/facts/seahorse.html'),
    ('Green sea turtle', 'Green sea turtles are named for the greenish color of their fat, not their shells.',
     'NOAA Fisheries', 'https://www.fisheries.noaa.gov/species/green-turtle'),
    ('Humpback whale', 'Humpback whales sometimes cooperate to make bubble nets that concentrate fish before they feed.',
     'NOAA Fisheries', 'https://www.fisheries.noaa.gov/species/humpback-whale'),
    ('Horseshoe crab', 'Horseshoe crabs are closer relatives of spiders and scorpions than of true crabs.',
     'NOAA Ocean Service', 'https://oceanservice.noaa.gov/facts/horseshoe-crab.html'),
    ('Whale shark', 'The whale shark is the largest living fish; it feeds by filtering small animals from the water.',
     'Smithsonian Ocean', 'https://ocean.si.edu/ocean-life/sharks-rays/whale-shark'),
    ('Clownfish', 'Clownfish live among sea anemone tentacles, protected from the stings by their mucus coating.',
     'Smithsonian Ocean', 'https://ocean.si.edu/ocean-life/fish/clownfish'),
    ('Mantis shrimp', 'Mantis shrimp are crustaceans; some species strike prey with powerful club-like limbs.',
     'Smithsonian Ocean', 'https://ocean.si.edu/ocean-life/invertebrates/mantis-shrimp'),
    ('Beluga whale', 'Belugas use a wide range of whistles, clicks, and other sounds, earning the nickname sea canaries.',
     'NOAA Fisheries', 'https://www.fisheries.noaa.gov/species/beluga-whale'),
    ('Harbor seal', 'Harbor seals use sensitive whiskers to help detect prey in the water.',
     'NOAA Fisheries', 'https://www.fisheries.noaa.gov/species/harbor-seal'),
    ('Coral', 'Corals are animals. Many reef-building corals host tiny algae that provide food through photosynthesis.',
     'NOAA Ocean Service', 'https://oceanservice.noaa.gov/facts/coral.html'),
    ('Sperm whale', 'Sperm whales use clicks for echolocation to find prey in the deep ocean.',
     'NOAA Fisheries', 'https://www.fisheries.noaa.gov/species/sperm-whale'),
]


def daily_extras(today):
    index = today.toordinal()
    quote, author = QUOTES[index % len(QUOTES)]
    word, pronunciation, part, definition, example = WORDS[index % len(WORDS)]
    animal, fact, source, _ = ANIMALS[index % len(ANIMALS)]
    return [
        'A MOMENT OF PERSPECTIVE', f'"{quote}"', f'-- {author}', '',
        'WORD OF THE DAY', f'{word} ({pronunciation}) | {part}', definition,
        f'Example: {example}', '',
        'BENEATH THE SURFACE', f'{animal}: {fact}', f'Source: {source}',
    ]


def condition(code):
    if code == 0:
        return '[SUN]', 'Clear sky'
    if code in (1, 2):
        return '[SUN/CLOUD]', 'Partly cloudy'
    if code == 3:
        return '[CLOUD]', 'Overcast'
    if code in (45, 48):
        return '[~~~]', 'Fog'
    if code in (51, 53, 55, 56, 57):
        return '[...]', 'Drizzle / freezing drizzle'
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return '[///]', 'Rain / showers'
    if code in (71, 73, 75, 77, 85, 86):
        return '[***]', 'Snow'
    if code in (95, 96, 99):
        return '[ZAP]', 'Thunderstorms'
    return '[?]', 'Conditions unavailable'


def weather_lines(settings, fetch, today):
    params = urlencode({
        'latitude': settings.get('latitude', 42.3601),
        'longitude': settings.get('longitude', -71.0589),
        'timezone': settings.get('timezone', 'America/New_York'),
        'daily': 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max,sunrise,sunset',
        'temperature_unit': 'fahrenheit', 'wind_speed_unit': 'mph', 'forecast_days': 2,
    })
    data = json.loads(fetch('https://api.open-meteo.com/v1/forecast?' + params))
    daily = data['daily']
    index = daily['time'].index(today.isoformat())  # Never label yesterday's forecast as today.

    def value(key, suffix=''):
        number = daily[key][index]
        return '--' if number is None else f'{number:.0f}{suffix}'

    def clock(key):
        return (daily[key][index] or '--:--').split('T')[-1]

    icon, description = condition(daily['weather_code'][index])
    body = [
        f"{settings.get('location', 'Boston, MA').upper()} | TODAY'S WEATHER",
        f'{icon} {description}',
        f"HIGH {value('temperature_2m_max', ' F')}   LOW {value('temperature_2m_min', ' F')}   PRECIP {value('precipitation_probability_max', '%')}",
        f"MAX WIND {value('wind_speed_10m_max', ' mph')}   SUNRISE {clock('sunrise')}   SUNSET {clock('sunset')}",
        'Forecast: Open-Meteo | Times local to forecast location',
    ]
    width = 80
    return ['+' + '-' * width + '+'] + [
        '| ' + line[:width - 2].ljust(width - 2) + ' |' for line in body
    ] + ['+' + '-' * width + '+', '']
