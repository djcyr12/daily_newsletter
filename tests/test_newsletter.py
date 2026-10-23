import argparse
from datetime import date
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import newsletter as n


class NewsletterTests(unittest.TestCase):
    def test_rss_and_atom(self):
        rss = b'<rss><channel><item><title>One &amp; Two</title><description>&lt;p&gt;Summary&lt;/p&gt;</description></item><item><title>Other</title></item></channel></rss>'
        self.assertEqual(n.parse_feed(rss, 1), [('One & Two', 'Summary')])
        atom = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Atom</title><summary>Text</summary></entry></feed>'
        self.assertEqual(n.parse_feed(atom, 2), [('Atom', 'Text')])

    def test_pdf_pagination_and_offsets(self):
        pdf = n.pdf_bytes(['A (story) \\ headline'] * 100)
        self.assertIn(b'/Count 3', pdf)
        self.assertIn(b'A \\(story\\) \\\\ headline', pdf)
        xref = int(pdf.split(b'startxref\n')[1].splitlines()[0])
        self.assertEqual(pdf[xref:xref+4], b'xref')
        offsets = pdf[xref:].splitlines()[3:12]
        for number, entry in enumerate(offsets, 1):
            offset = int(entry.split()[0])
            self.assertTrue(pdf[offset:].startswith(f'{number} 0 obj'.encode()))

    def test_generate_and_feed_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / 'config.json'
            config.write_text(json.dumps({'feeds': ['https://one', 'https://two']}))
            with patch.object(n, 'fetch_feed', side_effect=[OSError('offline'), [('Title', 'Body')]]):
                result = n.generate(config, root)
            self.assertIn(b'Title', result.read_bytes())
            with patch.object(n, 'fetch_feed', side_effect=OSError('offline')):
                with self.assertRaisesRegex(ValueError, 'No articles'):
                    n.generate(config, root)

    def test_print_once_force_and_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / 'issue.pdf'
            with patch.object(n, 'generate', return_value=pdf), patch.object(n.subprocess, 'run') as run:
                run.return_value = subprocess.CompletedProcess([], 0, stdout='request id is queue-42\n')
                n.print_issue(root / 'config', root, 'Brother')
                n.print_issue(root / 'config', root, 'Brother')
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0], ['/usr/bin/lp', '-d', 'Brother', '-n', '1', '-o', 'media=Letter', str(pdf)])
                n.print_issue(root / 'config', root, 'Brother', force=True)
                self.assertEqual(run.call_count, 2)
                marker = root / f'submitted-{date.today().isoformat()}.txt'
                marker.unlink()
                run.side_effect = subprocess.CalledProcessError(1, 'lp')
                with self.assertRaises(subprocess.CalledProcessError):
                    n.print_issue(root / 'config', root, 'Brother')
                self.assertFalse(marker.exists())

    def test_schedule_roundtrip(self):
        args = argparse.Namespace(config=Path('/tmp/a config.json'), output_dir=Path('/tmp/news'), printer='Brother', hour=8, minute=15)
        result = plistlib.loads(plistlib.dumps(n.schedule_definition(args)))
        self.assertEqual(result['StartCalendarInterval'], {'Hour': 8, 'Minute': 15})
        self.assertIn('/tmp/a config.json', result['ProgramArguments'])
        self.assertEqual(result['ProgramArguments'][-3:], ['print', '--printer', 'Brother'])


if __name__ == '__main__':
    unittest.main()
