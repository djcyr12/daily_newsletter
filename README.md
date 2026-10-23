# Daily Newsletter

Fetch RSS headlines, generate a printable PDF, and print each day from a Mac to a network printer such as the Brother HL-L3220CDW. Requires Python 3.10+; no Python packages or API keys.

## Set up your Mac

1. Connect your Mac and Brother printer to the same network. Add the printer in **System Settings → Printers & Scanners → Add Printer**, using AirPrint if offered. Verify printing from macOS first.
2. Install Python 3.10+ from python.org (run its bundled **Install Certificates.command** if needed), or use `brew install python` if you have Homebrew.
3. Clone this repository onto your Mac and open Terminal in the repository folder. A location such as `~/Projects/daily_newsletter` avoids macOS background-access restrictions on Desktop/Documents.

List printer queues, generate an issue, and review it:

```sh
python3 newsletter.py printers
python3 newsletter.py generate
open "$HOME/Library/Application Support/DailyNewsletter/newsletter-$(date +%F).pdf"
```

The default newsletter has six BBC World News headlines and feed summaries. Edit `config.json` to change the title, HTTPS RSS/Atom feeds, and articles per feed (1–30). Only configure trusted feed URLs. The compact PDF renderer uses a built-in font and replaces unsupported non-ASCII characters. Issues contain feed excerpts, not full articles.

## Print and schedule

Replace `YOUR_QUEUE_NAME` with the exact queue name reported by `printers`:

```sh
python3 newsletter.py print --printer YOUR_QUEUE_NAME
python3 newsletter.py schedule --printer YOUR_QUEUE_NAME --hour 7 --minute 30
```

Printing submits one Letter-size PDF to macOS. Successful queue acceptance is recorded to prevent repeated submissions on the same date. It does not confirm physical printing: check Printers & Scanners for paper, toner, or connection errors. Add `--force` to the `print` command only if you intentionally want another copy. A crash between queue acceptance and recording can result in a repeated submission.

Scheduling installs a user LaunchAgent at `~/Library/LaunchAgents/local.daily-newsletter.plist`. It runs at the selected time in your Mac's local timezone. The Mac must be logged in and awake, with Internet and printer access. macOS can run a missed calendar job after waking; this setup does not wake the Mac or run while it is shut down. Keep Python and the repository at the same paths; rerun `schedule` if either moves.

PDFs, submission records, and schedule logs are stored in `~/Library/Application Support/DailyNewsletter/`. Older files are retained; remove them as needed. To remove the schedule:

```sh
python3 newsletter.py unschedule
```

Unavailable feeds are reported and skipped. If no articles are retrieved, the app fails without printing; there is no automatic retry that day. HTTPS certificate verification remains enabled. This cloud workspace cannot directly reach your home printer: printing and scheduling commands must run on your Mac.

## Development

```sh
python3 -m unittest discover -s tests -v
python3 newsletter.py --output-dir /tmp/daily-newsletter generate
```

Global options (`--config` and `--output-dir`) go before the subcommand. Tests cover RSS/Atom parsing, PDF pagination and structure, feed failures, print queue submission and duplicate prevention, and schedule construction. Actual Brother printing and LaunchAgent execution require validation on macOS.
