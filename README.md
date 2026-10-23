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

The default issue includes:

- Three world headlines from BBC News and three Boston-area headlines from WBUR (Boston.com is a fallback), with short feed excerpts.
- A boxed Boston weather panel with ASCII condition symbols, today's high/low in Fahrenheit, maximum precipitation probability, maximum wind speed, and sunrise/sunset. Forecast data comes from Open-Meteo, with times in America/New_York. It is a daily forecast, not live observations.
- A positive philosophy or reflection quotation with attribution.
- An LSAT-focused reading/argument word, part of speech, dictionary definition, and original reasoning example.
- An aquatic animal fact with its source organization.

The default layout fits on one Letter page. Larger custom configurations paginate automatically. The compact PDF renderer uses a built-in font and replaces unsupported non-ASCII characters.

### Customize your issue

Edit `config.json`: `news_sections` controls section titles, feed URLs, and the total story `limit` per section. Feeds are tried in order until the limit is filled. `weather` controls the city label, coordinates, and timezone; set `enabled` to `false` to omit it. Set `daily_extras` to `false` to omit the three daily reading sections. Legacy configurations using `feeds` and `articles_per_feed` still work.

The daily reading is selected deterministically by the local calendar date. Quotes repeat every 7 days and facts every 13. Animal fact reference URLs are retained in `daily_sections.py`; quotations identify the work and translator when applicable.

Vocabulary now rotates through 40 academic and argument-analysis terms in `vocabulary.json` (for example, *equivocal*, *corroborate*, *specious*, and *cogent*). This is an independently curated reading-prep list, not an official LSAC list or a transcription of a commercial prep resource. For further study, use [Magoosh's GRE vocabulary flashcards](https://gre.magoosh.com/flashcards/vocabulary); GRE academic vocabulary overlaps with challenging LSAT reading. Definitions are looked up through the [Free Dictionary API](https://dictionaryapi.dev/) for the chosen part of speech, preferring a sense that shares terms with the study definition. Dictionary entries can contain multiple senses; examples and offline study meanings remain independently written for argument-analysis practice. If lookup fails, the PDF labels the local study definition as offline. Set `vocabulary.live_dictionary` to `false` to skip lookups. No paid API or key is required.

News summaries omit WordPress post credits and trailing read-more prompts, collapse HTML spacing, and avoid repeating an identical headline. Curly punctuation is converted to printable ASCII rather than question marks. Numbered stories have indented summaries and a blank line between them; source credits list only publishers that supplied a printed story.

Only configure trusted HTTPS feed URLs. External data requires access to `feeds.bbci.co.uk`, `www.wbur.org`, `www.boston.com`, `api.open-meteo.com`, and `api.dictionaryapi.dev` (including any HTTPS redirect destinations). Open-Meteo's free hosted API is intended for noncommercial use; see [its terms](https://open-meteo.com/en/terms). Forecast attribution: [Open-Meteo](https://open-meteo.com/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

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

Unavailable feeds are reported and skipped, and empty sections are marked unavailable. If no articles are retrieved from any section, the app fails without printing; there is no automatic retry that day. Weather failures produce an explicit unavailable message instead of a made-up or stale forecast. HTTPS certificate verification remains enabled. This cloud workspace cannot directly reach your home printer: printing and scheduling commands must run on your Mac.

## Development

```sh
python3 -m unittest discover -s tests -v
python3 newsletter.py --output-dir /tmp/daily-newsletter generate
```

Global options (`--config` and `--output-dir`) go before the subcommand. Tests cover RSS/Atom parsing, PDF pagination and structure, feed failures, print queue submission and duplicate prevention, and schedule construction. Actual Brother printing and LaunchAgent execution require validation on macOS.
