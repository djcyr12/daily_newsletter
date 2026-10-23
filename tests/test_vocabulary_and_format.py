from datetime import date, timedelta
import json
import unittest
from unittest.mock import patch

import daily_sections as s
import newsletter as n


class VocabularyAndFormatTests(unittest.TestCase):
    def test_boston_wordpress_boilerplate_and_inline_markup(self):
        raw = b'''<rss><channel><item><title>Boston's transit plan</title>
        <description>&lt;p&gt;Boston's transit plan&lt;/p&gt;&lt;p&gt;The &lt;strong&gt;MBTA&lt;/strong&gt;'s service expands.&lt;/p&gt;
        &lt;p&gt;The post Boston's transit plan appeared first on Boston.com.&lt;/p&gt;</description>
        </item></channel></rss>'''
        title, summary = n.parse_feed(raw, 1)[0]
        lines = n.story_lines(1, title, summary)
        self.assertEqual(lines, ["1. Boston's transit plan", "   The MBTA's service expands.", ''])
        self.assertEqual(n.clean('<p>One</p><p>Two<br>Three</p><script>ignore()</script>'), 'One Two Three')

    def test_punctuation_and_read_more(self):
        lines = n.story_lines(2, 'Boston\u2019s \u201cnew\u201d plan\u2014approved', '<p>More trains\u2026 this fall.</p><p>Read more...</p>')
        self.assertEqual(lines, ['2. Boston\'s "new" plan - approved', '   More trains... this fall.', ''])
        self.assertNotIn('?', n.pdf_bytes(lines).decode('ascii'))

    def test_vocabulary_rotation_covers_study_list(self):
        today = date(2026, 10, 22)
        words = [s.vocabulary_lines(today + timedelta(days=i))[1].split(' | ')[0]
                 for i in range(len(s.WORDS))]
        self.assertEqual(len(set(words)), 40)
        self.assertIn('corroborate', words)
        self.assertIn('specious', words)
        for word in s.WORDS:
            self.assertTrue(all(word))

    def test_dictionary_definition_and_sense_selection(self):
        word = ('qualify', 'verb', 'To limit a statement or add a condition.', 'The author qualifies the conclusion.')
        response = [{'meanings': [{'partOfSpeech': 'verb', 'definitions': [
            {'definition': 'To meet the requirements for a competition.'},
            {'definition': 'To limit a statement by adding a condition.'}]}]}]
        urls = []
        def fetch(url):
            urls.append(url)
            return json.dumps(response)
        with patch.object(s, 'WORDS', [word]):
            lines = s.vocabulary_lines(date.today(), fetch)
        self.assertIn('To limit a statement by adding a condition.', lines)
        self.assertTrue(any('dictionaryapi.dev' in line for line in lines))
        self.assertEqual(urls, ['https://api.dictionaryapi.dev/api/v2/entries/en/qualify'])

    def test_dictionary_failure_preserves_original_definition(self):
        for response in ('not json', '{}', '[]', '[{"meanings": []}]'):
            with self.subTest(response=response):
                lines = s.vocabulary_lines(date.today(), lambda url: response)
                self.assertIn('Definition: local study notes (offline)', lines)
                self.assertTrue(lines[2])
                self.assertTrue(lines[3].startswith('Example:'))


if __name__ == '__main__':
    unittest.main()
