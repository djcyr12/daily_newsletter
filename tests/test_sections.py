from datetime import date, timedelta
import json
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
from unittest.mock import patch

import daily_sections as sections
import newsletter as n


def forecast(day):
    return {'daily': {'time': [day.isoformat()], 'weather_code': [61],
                      'temperature_2m_max': [63.4], 'temperature_2m_min': [45.1],
                      'precipitation_probability_max': [70], 'wind_speed_10m_max': [18.3],
                      'sunrise': [day.isoformat() + 'T07:04'],
                      'sunset': [day.isoformat() + 'T17:50']}}


class SectionTests(unittest.TestCase):
    def test_weather_values_and_box_alignment(self):
        today = date(2026, 10, 22)
        urls = []
        def fetch(url):
            urls.append(url)
            return json.dumps(forecast(today)).encode()
        lines = sections.weather_lines({}, fetch, today)
        rendered = '\n'.join(lines)
        for value in ('[///]', '63 F', '45 F', '70%', '18 mph', '07:04', '17:50', 'Open-Meteo'):
            self.assertIn(value, rendered)
        self.assertEqual({len(line) for line in lines[:-1]}, {82})
        self.assertIn('temperature_unit=fahrenheit', urls[0])
        self.assertIn('timezone=America%2FNew_York', urls[0])
        self.assertEqual(sections.condition(95), ('[ZAP]', 'Thunderstorms'))
        self.assertEqual(sections.condition(999), ('[?]', 'Conditions unavailable'))

    def test_stale_weather_rejected_and_missing_values_labeled(self):
        today = date(2026, 10, 22)
        old = forecast(today - timedelta(days=1))
        with self.assertRaises(ValueError):
            sections.weather_lines({}, lambda url: json.dumps(old), today)
        data = forecast(today)
        data['daily']['temperature_2m_max'] = [None]
        lines = sections.weather_lines({}, lambda url: json.dumps(data), today)
        self.assertIn('HIGH --', '\n'.join(lines))

    def test_daily_rotation_and_required_content(self):
        day = date(2026, 10, 22)
        text = sections.daily_extras(day)
        self.assertEqual(text, sections.daily_extras(day))
        self.assertNotEqual(text, sections.daily_extras(day + timedelta(days=1)))
        self.assertTrue(any('Example:' in line for line in text))
        self.assertTrue(any('Source:' in line for line in text))
        self.assertIn('A MOMENT OF PERSPECTIVE', text)
        self.assertIn('WORD OF THE DAY | LSAT READING', text)
        self.assertIn('BENEATH THE SURFACE', text)

    def test_full_issue_section_limits_and_pdf_extraction(self):
        config = n.ROOT / 'config.json'
        today = date.today()
        long_articles = [(f'Headline {i} ' + 'world story ' * 30, 'A news summary ' * 40) for i in range(10)]
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(n, 'fetch_feed', return_value=long_articles) as feeds, patch.object(n, 'fetch_bytes', return_value=json.dumps(forecast(today))):
                path = n.generate(config, Path(directory))
            self.assertEqual(feeds.call_count, 2)
            pdf = path.read_bytes()
            self.assertIn(b'/Count 1', pdf)
            for heading in (b'AROUND THE WORLD', b'BOSTON & NEARBY', b'WORD OF THE DAY', b'BENEATH THE SURFACE'):
                self.assertIn(heading, pdf)
            self.assertNotIn(b'4. Headline', pdf)
            if shutil.which('pdftotext'):
                result = subprocess.run(['pdftotext', '-layout', str(path), '-'], capture_output=True, text=True, check=True)
                self.assertIn('HIGH 63 F', result.stdout)
                self.assertIn('A MOMENT OF PERSPECTIVE', result.stdout)

    def test_missing_local_news_and_weather_do_not_erase_world(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(n, 'fetch_feed', side_effect=[[('World headline', 'Summary')], OSError('offline'), OSError('offline')]), patch.object(n, 'fetch_bytes', side_effect=OSError('offline')):
                path = n.generate(n.ROOT / 'config.json', Path(directory))
            pdf = path.read_bytes()
            self.assertIn(b'World headline', pdf)
            self.assertIn(b'Forecast unavailable', pdf)
            self.assertIn(b'News unavailable', pdf)
            self.assertIn(b'WORD OF THE DAY', pdf)


if __name__ == '__main__':
    unittest.main()
