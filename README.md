# SiteSpecter

```
 ____  _ _       ____                  _
/ ___|(_) |_ ___/ ___| _ __   ___  ___| |_ ___ _ __
\___ \| | __/ _ \___ \| '_ \ / _ \/ __| __/ _ \ '__|
 ___) | | ||  __/___) | |_) |  __/ (__| ||  __/ |
|____/|_|\__\___|____/| .__/ \___|\___|\__\___|_|
                      |_|
        by d3vn0mi
```

**Ghost-crawl any website and capture it as local HTML.**

SiteSpecter silently crawls a target website by following `<a href>` links and saves every HTML page it finds to a local directory — preserving the site's path structure. Think of it as a digital specter that passes through a site and captures everything it touches.

---

## Features

- **Recursive crawling** — follows links up to a configurable depth
- **Same-domain enforcement** — stays on the target host by default (can be disabled)
- **URL normalization** — deduplicates URLs by sorting query params, stripping fragments, and normalizing paths
- **Structured output** — mirrors the site's URL path structure in the output directory
- **Query-aware filenames** — pages with different query strings are saved as separate files
- **Image downloading** — automatically finds and saves all images (`<img>`, `srcset`, CSS backgrounds) into a `pictures/` folder
- **Polite crawling** — configurable delay between requests and custom User-Agent
- **Progress output** — real-time display of crawled pages with depth info (or `--quiet` mode)

## Requirements

- Python 3.8+
- [requests](https://pypi.org/project/requests/)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)

## Installation

```bash
# Clone the repo
git clone https://github.com/d3vn0mi/save_site_to_html.git
cd save_site_to_html

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Crawl a site with default settings (depth=2, max 500 pages)
python sitespecter.py https://example.com

# Save to a specific directory
python sitespecter.py https://example.com -o ./my_capture

# Deep crawl with more pages
python sitespecter.py https://example.com --max-depth 4 --max-pages 2000

# Crawl without downloading images
python sitespecter.py https://example.com --no-pictures

# Quiet mode — only show the summary
python sitespecter.py https://example.com -q
```

## Usage

```
usage: sitespecter [-h] [-o OUT] [--max-depth MAX_DEPTH]
                   [--max-pages MAX_PAGES] [--delay DELAY]
                   [--no-same-domain-only] [--ua UA] [--timeout TIMEOUT]
                   [--no-pictures] [-q] [-v]
                   url

SiteSpecter by d3vn0mi - Ghost-crawl any website and capture it as local HTML.

positional arguments:
  url                   Start URL (e.g., https://example.com/)

options:
  -h, --help            show this help message and exit
  -o, --out OUT         Output directory (default: site_dump)
  --max-depth MAX_DEPTH
                        Max link depth to follow (default: 2)
  --max-pages MAX_PAGES
                        Max pages to fetch (default: 500)
  --delay DELAY         Delay between requests in seconds (default: 0.2)
  --no-same-domain-only
                        Allow crawling off-domain links (default: same-domain only)
  --ua UA               User-Agent string
  --timeout TIMEOUT     HTTP timeout seconds (default: 15)
  --no-pictures         Skip downloading images (default: download all images)
  -q, --quiet           Suppress per-page output
  -v, --version         show version and exit
```

## Example Output

```
 ____  _ _       ____                  _
/ ___|(_) |_ ___/ ___| _ __   ___  ___| |_ ___ _ __
\___ \| | __/ _ \___ \| '_ \ / _ \/ __| __/ _ \ '__|
 ___) | | ||  __/___) | |_) |  __/ (__| ||  __/ |
|____/|_|\__\___|____/| .__/ \___|\___|\__\___|_|
                      |_|
        by d3vn0mi  |  v1.1.0

  Target : https://example.com
  Output : /home/user/site_dump
  Depth  : 2  |  Max pages: 500
  Delay  : 0.2s  |  Timeout: 15.0s
  Domain : same-domain only
  Images : enabled

  [depth=0] https://example.com -> index.html

  Found 3 images. Downloading...
  [img] https://example.com/logo.png -> pictures/logo_a1b2c3d4.png
  [img] https://example.com/banner.jpg -> pictures/banner_e5f6g7h8.jpg
  [img] https://example.com/icon.svg -> pictures/icon_i9j0k1l2.svg

  Fetched : 1 pages
  Saved   : 1 HTML files -> /home/user/site_dump
  Images  : 3 pictures -> /home/user/site_dump/pictures

  Done. // d3vn0mi
```

## How It Works

1. **Normalize** the start URL (strip fragments, sort query params)
2. **Fetch** the page and check it returns HTML
3. **Save** the HTML to a local file that mirrors the URL path
4. **Extract** all `<a href>` links and image URLs (`<img>`, `srcset`, CSS backgrounds) from the page
5. **Filter** links by domain (if same-domain mode is on) and skip already-visited URLs
6. **Enqueue** new links with incremented depth
7. **Repeat** until max depth or max pages is reached
8. **Download** all discovered images into a `pictures/` folder

## Project Structure

```
save_site_to_html/
  sitespecter.py      # Main crawler script
  requirements.txt    # Python dependencies
  README.md           # This file
  .gitignore          # Git ignore rules

site_dump/            # Default output (created at runtime)
  index.html          # Captured HTML pages
  about.html
  pictures/           # Downloaded images
    logo_a1b2c3d4.png
    banner_e5f6g7h8.jpg
```

## License

MIT License. See [LICENSE](LICENSE) for details.

---

**Built by [d3vn0mi](https://github.com/d3vn0mi)**
