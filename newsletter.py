#!/usr/bin/env python3
"""Fetch RSS/Atom news, produce a PDF, and print daily on macOS."""
import argparse
from datetime import date
import fcntl
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import plistlib
import re
import subprocess
import sys
import textwrap
import unicodedata
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
DATA = Path.home() / 'Library/Application Support/DailyNewsletter'
LABEL = 'local.daily-newsletter'


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def clean(value):
    parser = PlainText()
    parser.feed(value or '')
    return ' '.join(unescape(' '.join(parser.parts)).split())


def parse_feed(raw, limit):
    root = ET.fromstring(raw)
    articles = []
    for item in root.iter():
        if item.tag.split('}')[-1] not in ('item', 'entry'):
            continue
        fields = {child.tag.split('}')[-1]: child for child in item}
        title = clean(''.join(fields['title'].itertext())) if 'title' in fields else ''
        summary = next((clean(''.join(fields[key].itertext())) for key in
                        ('description', 'summary', 'content') if key in fields), '')
        if title:
            articles.append((title, summary[:1000]))
        if len(articles) >= limit:
            break
    return articles


def fetch_feed(url, limit):
    if urlparse(url).scheme != 'https':
        raise ValueError('Feed URLs must use HTTPS')
    with urlopen(Request(url, headers={'User-Agent': 'DailyNewsletter/1.0'}), timeout=25) as response:
        if urlparse(response.geturl()).scheme != 'https':
            raise ValueError('Feed redirected away from HTTPS')
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError('Feed exceeds 2 MB limit')
    return parse_feed(raw, limit)


def pdf_bytes(lines):
    """Build a Letter PDF using the built-in Courier font."""
    wrapped = []
    for line in lines:
        value = unicodedata.normalize('NFKD', line).encode('ascii', 'replace').decode()
        wrapped.extend(textwrap.wrap(value, width=88) or [''])
    pages = [wrapped[i:i + 48] for i in range(0, len(wrapped), 48)] or [[]]
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>']
    kids = []
    for page in pages:
        number = len(objects) + 1
        kids.append(f'{number} 0 R')
        objects.append((f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
                        f'/Resources << /Font << /F1 3 0 R >> >> /Contents {number + 1} 0 R >>').encode())
        commands = ['BT /F1 10 Tf 12 TL 42 744 Td']
        for line in page:
            escaped = re.sub(r'([\\()])', r'\\\1', line)
            commands.append(f'({escaped}) Tj T*')
        stream = ('\n'.join(commands) + '\nET\n').encode('ascii')
        objects.append(f'<< /Length {len(stream)} >>\nstream\n'.encode() + stream + b'endstream')
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(pages)} >>".encode()
    result = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f'{number} 0 obj\n'.encode() + obj + b'\nendobj\n')
    xref = len(result)
    result.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:
        result.extend(f'{offset:010d} 00000 n \n'.encode())
    result.extend((f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n'
                   f'startxref\n{xref}\n%%EOF\n').encode())
    return bytes(result)


def generate(config_path, output_dir):
    config = json.loads(config_path.read_text())
    limit = config.get('articles_per_feed', 6)
    if not isinstance(limit, int) or not 1 <= limit <= 30:
        raise ValueError('articles_per_feed must be between 1 and 30')
    feeds = config.get('feeds', [])
    if not isinstance(feeds, list) or not feeds or len(feeds) > 20:
        raise ValueError('Configure between 1 and 20 feed URLs')
    lines = [str(config.get('title', 'Daily Newsletter')), date.today().isoformat(), '']
    count = 0
    for url in feeds:
        try:
            articles = fetch_feed(url, limit)
        except Exception as exc:
            print(f'Feed unavailable ({url}): {exc}', file=sys.stderr)
            continue
        if articles:
            lines.extend([url, ''])
        for title, summary in articles:
            lines.extend([title, summary, ''])
            count += 1
    if not count:
        raise ValueError('No articles retrieved; nothing generated or printed')
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f'newsletter-{date.today().isoformat()}.pdf'
    temporary = path.with_suffix('.pdf.tmp')
    temporary.write_bytes(pdf_bytes(lines))
    temporary.replace(path)
    print(f'Generated {path} ({count} articles)')
    return path


def print_issue(config_path, output_dir, printer, force=False):
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / '.print.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        marker = output_dir / f'submitted-{date.today().isoformat()}.txt'
        if marker.exists() and not force:
            print("Today's newsletter was already submitted; skipping.")
            return
        path = generate(config_path, output_dir)
        result = subprocess.run(['/usr/bin/lp', '-d', printer, '-n', '1', '-o', 'media=Letter', str(path)],
                                check=True, text=True, capture_output=True)
        marker.write_text(result.stdout)
        print(result.stdout.strip())


def schedule_definition(args):
    return {
        'Label': LABEL,
        'ProgramArguments': [str(Path(sys.executable).resolve()), str(ROOT / 'newsletter.py'),
                             '--config', str(args.config.resolve()), '--output-dir',
                             str(args.output_dir.resolve()), 'print', '--printer', args.printer],
        'StartCalendarInterval': {'Hour': args.hour, 'Minute': args.minute},
        'WorkingDirectory': str(ROOT),
        'StandardOutPath': str(args.output_dir.resolve() / 'schedule.log'),
        'StandardErrorPath': str(args.output_dir.resolve() / 'schedule-error.log'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config.json')
    parser.add_argument('--output-dir', type=Path, default=DATA)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('generate')
    commands.add_parser('printers')
    printing = commands.add_parser('print')
    printing.add_argument('--printer', required=True)
    printing.add_argument('--force', action='store_true')
    scheduling = commands.add_parser('schedule')
    scheduling.add_argument('--printer', required=True)
    scheduling.add_argument('--hour', type=int, choices=range(24), default=7)
    scheduling.add_argument('--minute', type=int, choices=range(60), default=30)
    commands.add_parser('unschedule')
    args = parser.parse_args()
    try:
        if args.command == 'generate':
            generate(args.config, args.output_dir)
        elif sys.platform != 'darwin':
            parser.error('Printing and scheduling must run on your Mac')
        elif args.command == 'printers':
            subprocess.run(['/usr/bin/lpstat', '-p', '-d'], check=True)
        elif args.command == 'print':
            print_issue(args.config, args.output_dir, args.printer, args.force)
        else:
            agent = Path.home() / 'Library/LaunchAgents' / f'{LABEL}.plist'
            if agent.exists():
                subprocess.run(['/bin/launchctl', 'unload', str(agent)], check=False)
            if args.command == 'unschedule':
                agent.unlink(missing_ok=True)
                print('Schedule removed')
            else:
                args.output_dir.mkdir(parents=True, exist_ok=True)
                agent.parent.mkdir(parents=True, exist_ok=True)
                agent.write_bytes(plistlib.dumps(schedule_definition(args)))
                subprocess.run(['/bin/launchctl', 'load', str(agent)], check=True)
                print(f'Scheduled daily at {args.hour:02d}:{args.minute:02d} local time')
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            print(exc.stderr.strip(), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
