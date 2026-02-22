#!/usr/bin/env python3
"""
 ____  _ _       ____                  _
/ ___|(_) |_ ___/ ___| _ __   ___  ___| |_ ___ _ __
\___ \| | __/ _ \___ \| '_ \ / _ \/ __| __/ _ \ '__|
 ___) | | ||  __/___) | |_) |  __/ (__| ||  __/ |
|____/|_|\__\___|____/| .__/ \___|\___|\__\___|_|
                      |_|

SiteSpecter - Ghost-crawl any website and capture it as local HTML.
A d3vn0mi open-source tool.

https://github.com/d3vn0mi
"""

__version__ = "1.0.0"
__author__ = "d3vn0mi"
__license__ = "MIT"

import argparse
import os
import re
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urldefrag, parse_qsl, urlencode

import requests
from bs4 import BeautifulSoup

BANNER = r"""
 ____  _ _       ____                  _
/ ___|(_) |_ ___/ ___| _ __   ___  ___| |_ ___ _ __
\___ \| | __/ _ \___ \| '_ \ / _ \/ __| __/ _ \ '__|
 ___) | | ||  __/___) | |_) |  __/ (__| ||  __/ |
|____/|_|\__\___|____/| .__/ \___|\___|\__\___|_|
                      |_|
        by d3vn0mi  |  v{}
""".format(__version__)


def normalize_url(url: str) -> str:
    """
    Normalize URL to reduce duplicates:
    - remove fragment (#...)
    - normalize trailing slash
    - sort query parameters
    """
    url, _frag = urldefrag(url)
    parsed = urlparse(url)

    # Sort query parameters to canonicalize
    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    query_pairs.sort()
    query = urlencode(query_pairs)

    # Normalize path: keep '/' as '/', otherwise strip trailing slash
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    normalized = parsed._replace(path=path, query=query).geturl()
    return normalized


def is_html_response(resp: requests.Response) -> bool:
    ctype = resp.headers.get("Content-Type", "")
    return "text/html" in ctype.lower() or "application/xhtml+xml" in ctype.lower()


def safe_filename_from_url(url: str) -> Path:
    """
    Map URL to a local file path:
    - / -> index.html
    - /a/b -> a/b.html
    - /a/b/ -> a/b/index.html (but we normalize trailing / away above)
    - include query string in filename (sanitized) to avoid collisions
    """
    parsed = urlparse(url)
    path = parsed.path or "/"

    # Convert to a filesystem path
    if path.endswith("/"):
        path = path + "index"
    if path == "/":
        path = "/index"

    # If it looks like it already has an extension, keep it; else add .html
    local_path = Path(path.lstrip("/"))
    if local_path.suffix == "":
        local_path = local_path.with_suffix(".html")

    # Handle query string to avoid collisions (e.g. page?id=1 vs page?id=2)
    if parsed.query:
        # sanitize query for filename usage
        q = re.sub(r"[^a-zA-Z0-9._-]+", "_", parsed.query)[:180]
        local_path = local_path.with_name(f"{local_path.stem}__q_{q}{local_path.suffix}")

    return local_path


def extract_links(base_url: str, html: str) -> Set[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: Set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not href:
            continue
        # Skip non-http(s)
        if href.startswith(("mailto:", "tel:", "javascript:", "data:")):
            continue
        absolute = urljoin(base_url, href)
        links.add(absolute)
    return links


@dataclass
class CrawlItem:
    url: str
    depth: int


def same_host(url: str, host: str) -> bool:
    try:
        return urlparse(url).netloc == host
    except Exception:
        return False


def crawl_and_save(
    start_url: str,
    out_dir: Path,
    max_depth: int,
    max_pages: int,
    delay: float,
    same_domain_only: bool,
    user_agent: str,
    timeout: float,
    quiet: bool = False,
) -> Tuple[int, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    start_url = normalize_url(start_url)
    start_host = urlparse(start_url).netloc

    visited: Set[str] = set()
    queued: Set[str] = set([start_url])
    q: deque[CrawlItem] = deque([CrawlItem(start_url, 0)])
    saved = 0
    fetched = 0

    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})

    while q and fetched < max_pages:
        item = q.popleft()
        url = item.url
        depth = item.depth

        if url in visited:
            continue
        visited.add(url)

        if same_domain_only and not same_host(url, start_host):
            continue

        try:
            resp = session.get(url, timeout=timeout, allow_redirects=True)
            fetched += 1

            # Normalize after redirects
            final_url = normalize_url(resp.url)
            if final_url not in visited:
                visited.add(final_url)

            if resp.status_code >= 400:
                if not quiet:
                    print(f"  [{resp.status_code}] {url}")
                continue

            if not is_html_response(resp):
                continue

            html = resp.text

            # Save HTML
            rel_path = safe_filename_from_url(final_url)
            full_path = out_dir / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(html, encoding="utf-8", errors="ignore")
            saved += 1

            if not quiet:
                print(f"  [depth={depth}] {final_url} -> {rel_path}")

            # Enqueue new links if depth allows
            if depth < max_depth:
                for link in extract_links(final_url, html):
                    link = normalize_url(link)
                    if link in visited or link in queued:
                        continue
                    if same_domain_only and not same_host(link, start_host):
                        continue
                    queued.add(link)
                    q.append(CrawlItem(link, depth + 1))

            if delay > 0:
                time.sleep(delay)

        except requests.RequestException as exc:
            if not quiet:
                print(f"  [ERR] {url}: {exc}")
            continue

    return fetched, saved


def main() -> int:
    p = argparse.ArgumentParser(
        prog="sitespecter",
        description="SiteSpecter by d3vn0mi - Ghost-crawl any website and capture it as local HTML.",
        epilog="Built with care by d3vn0mi | https://github.com/d3vn0mi",
    )
    p.add_argument("url", help="Start URL (e.g., https://example.com/)")
    p.add_argument("-o", "--out", default="site_dump", help="Output directory (default: site_dump)")
    p.add_argument("--max-depth", type=int, default=2, help="Max link depth to follow (default: 2)")
    p.add_argument("--max-pages", type=int, default=500, help="Max pages to fetch (default: 500)")
    p.add_argument("--delay", type=float, default=0.2, help="Delay between requests in seconds (default: 0.2)")
    p.add_argument(
        "--no-same-domain-only",
        action="store_true",
        help="Allow crawling off-domain links (default: same-domain only)",
    )
    p.add_argument("--ua", default=f"SiteSpecter/{__version__} (d3vn0mi)", help="User-Agent string")
    p.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout seconds (default: 15)")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress per-page output")
    p.add_argument("-v", "--version", action="version", version=f"SiteSpecter {__version__} by d3vn0mi")

    args = p.parse_args()
    out_dir = Path(args.out)
    same_domain_only = not args.no_same_domain_only

    print(BANNER)
    print(f"  Target : {args.url}")
    print(f"  Output : {out_dir.resolve()}")
    print(f"  Depth  : {args.max_depth}  |  Max pages: {args.max_pages}")
    print(f"  Delay  : {args.delay}s  |  Timeout: {args.timeout}s")
    print(f"  Domain : {'same-domain only' if same_domain_only else 'cross-domain allowed'}")
    print()

    fetched, saved = crawl_and_save(
        start_url=args.url,
        out_dir=out_dir,
        max_depth=max(0, args.max_depth),
        max_pages=max(1, args.max_pages),
        delay=max(0.0, args.delay),
        same_domain_only=same_domain_only,
        user_agent=args.ua,
        timeout=max(1.0, args.timeout),
        quiet=args.quiet,
    )

    print()
    print(f"  Fetched : {fetched} pages")
    print(f"  Saved   : {saved} HTML files -> {out_dir.resolve()}")
    print()
    print("  Done. // d3vn0mi")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
