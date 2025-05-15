#!/usr/bin/env python3
import sys
import argparse
import requests
from bs4 import BeautifulSoup
from wcwidth import wcswidth
from deep_translator import GoogleTranslator

SCHEDULE_URL = "https://wwr-stardom.com/schedule"


def get_card_links() -> list[str]:
    r = requests.get(SCHEDULE_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    return [a["href"] for a in soup.find_all("a", class_="btn", string="対戦カード")]


def parse_card(url: str) -> tuple[str, list[dict]]:
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    title_el = soup.select_one("h1.match_head_title")
    title = title_el.get_text(strip=True) if title_el else url

    # Fetch show time
    ticket_el = soup.select_one("a.btnstyle4")
    if ticket_el and ticket_el.get("href"):
        try:
            r2 = requests.get(ticket_el["href"])
            r2.raise_for_status()
            soup2 = BeautifulSoup(r2.text, "html.parser")
            for div in soup2.find_all("div", class_="data_bg2"):
                if "本戦開始時間" in div.get_text():
                    span = div.parent.find("span", class_="time")
                    if span:
                        time_str = span.get_text(strip=True)
                        title = f"{title} ({time_str})"
                    break
        except requests.RequestException:
            pass

    matches = []
    for wrap in soup.select("div.match_cover div.match_wrap"):
        mt = wrap.select_one("h2.sub_content_title1")
        match_type = mt.get_text(strip=True) if mt else ""

        # Row-style
        row = wrap.find("div", class_="match_block_row")
        if row:
            left = [n.get_text(strip=True) for n in row.select("div.leftside h3.name")]
            right = [n.get_text(strip=True) for n in row.select("div.rightside h3.name")]
            matches.append({'type': match_type, 'left': left, 'right': right})
            continue

        # Column-style
        col = wrap.find("div", class_="match_block_column")
        if col:
            uls = col.select("ul.match_block_3col")
            left = [n.get_text(strip=True) for n in uls[0].select("h3.name")] if len(uls) > 0 else []
            right = [n.get_text(strip=True) for n in uls[1].select("h3.name")] if len(uls) > 1 else []
            matches.append({'type': match_type, 'left': left, 'right': right})
    return title, matches


def disp_len(s: str) -> int:
    return wcswidth(s)


def pad_center(text: str, width: int) -> str:
    length = disp_len(text)
    if length >= width:
        return text
    space = width - length
    left = space // 2
    right = space - left
    return " " * left + text + " " * right


def print_match_table(match_type: str, left: list[str], right: list[str], w1: int, w2: int, w3: int) -> None:
    top = f"┌{'─'*w1}┬{'─'*w2}┬{'─'*w3}┐"
    bottom = f"└{'─'*w1}┴{'─'*w2}┴{'─'*w3}┘"
    print(match_type)
    print(top)
    rows = max(len(left), len(right))
    for i in range(rows):
        l = left[i] if i < len(left) else ''
        r = right[i] if i < len(right) else ''
        mid = 'vs' if i == rows // 2 else ''
        line = '│' + pad_center(l, w1) + '│' + pad_center(mid, w2) + '│' + pad_center(r, w3) + '│'
        print(line)
    print(bottom)


def main():
    parser = argparse.ArgumentParser(description="Display Stardom event card.")
    parser.add_argument("n", nargs="?", type=int, default=1,
                        help="Which show (1=next, 2=second, etc.)")
    parser.add_argument("-e", "--english", action="store_true",
                        help="Translate match types and names to English via Google Translate API")
    args = parser.parse_args()

    links = get_card_links()
    if not links:
        sys.exit("No cards found.")
    if args.n < 1 or args.n > len(links):
        sys.exit(f"Only found {len(links)} card(s).")

    title, matches = parse_card(links[args.n - 1])

    # Handle translations
    print_matches = []
    if args.english:
        translator = GoogleTranslator(source='ja', target='en')
        # collect unique texts
        originals = [title]
        for m in matches:
            originals.append(m['type'])
            originals.extend(m['left'])
            originals.extend(m['right'])
        seen = {}  # preserve order
        for text in originals:
            if text and text not in seen:
                seen[text] = None
        originals = list(seen.keys())
        # batch translate
        translations = translator.translate_batch(originals)
        mapping = dict(zip(originals, translations))
        title = mapping.get(title, title)
        for m in matches:
            mtype = mapping.get(m['type'], m['type'])
            left = [mapping.get(name, name) for name in m['left']]
            right = [mapping.get(name, name) for name in m['right']]
            print_matches.append({'type': mtype, 'left': left, 'right': right})
    else:
        title = title
        print_matches = [{'type': m['type'], 'left': m['left'], 'right': m['right']} for m in matches]

    # Compute uniform widths
    w2 = disp_len('vs')
    w1 = max((disp_len(n) for m in print_matches for n in m['left']), default=0)
    w3 = max((disp_len(n) for m in print_matches for n in m['right']), default=0)

    print(f"{title}\n")
    for m in print_matches:
        print_match_table(m['type'], m['left'], m['right'], w1, w2, w3)

if __name__ == "__main__":
    main()
