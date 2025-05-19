#!/usr/bin/env python3
import sys
import argparse
import requests
from bs4 import BeautifulSoup
from wcwidth import wcswidth
from deep_translator import GoogleTranslator

SCHEDULE_URL = "https://wwr-stardom.com/schedule"

NAME_OVERRIDES = {
    #A
    "アイリカ": "Airica",
    "鉄アキラ": "Akira Kurogane",
    "壮麗亜美": "Ami Sorei",
    "金屋あんね": "Anne Kanaya",
    "星輝ありさ": "Arisa Hoshiki",
    "郷田明日香" : "Asuka Goda",
    "アティーナ": "Athena",
    "さくらあや": "Aya Sakura",
    "稲葉あづさ": "Azusa Inaba",
    "稲葉あずさ（JTO）": "Azusa Inaba",
    #B
    #C
    "橋本千紘": "Chihiro Hashimoto",
    #D
    "ダンプ松本": "Dump Matsumoto",
    #F
    "フキゲンです★": "Fukigen Death",
    
    #H
    "羽南": "Hanan",
    "梅咲遥": "Haruka Umesaki",
    "ひめか": "Himeka",
    "叶ミク": "Himiko",
    "妃南": "Hina",
    "姫ゆりあ": "Hime-Yuria",
    "炎華": "Honoka",
    "花穂ノ利": "Hanori Hana",
    "葉月": "Hazuki",
    #I
    "星いぶき": "Ibuki Hoshi",
    "青木 いつ希": "Itsuki Aoki",
    #J
    "ジョディ・スレット": "Jody Threat",
    "ジョニー・ロビー": "Johnnie Robbie",
    #K
    "関口翔": "Kakeru Sekiguchi",
    "カリエンティタ": "Kalientita",
    "米山香織": "Kaori Yoneyama",
    "ケルシー・ヘザー": "Kelsey Heather",
    "虎龍清花": "Kiyoka Kotatsu",
    "コグマ": "Koguma",
    "狐伯": "Kohaku",
    "小波": "Konami",
    "玖麗さやか": "Kurara Sayaka",
    #L
    "レディ・Ｃ": "Lady C",
    "ジュビア": "Lluvia",
    #M
    "舞華": "Maika",
    "尾﨑妹加": "Maika Ozaki",
    "舞夢": "Mai Sakurai",
    "愛海": "Manami",
    "浜辺纏": "Matoi Hamabe",
    "マヤ・ワールド": "Maya World",
    "岩谷麻優": "Mayu Iwatani",
    "岩谷麻由": "Mayu Iwatani",
    "マゼラティ": "Mazzerati",
    "メーガン・ベーン": "Megan Bayne",
    "星来芽依": "Mei Seira",
    "岩田美香": "Mika Iwata",
    "白川未奈": "Mina Shirakawa",
    "光芽ミリア": "Miria Koga",
    "神姫楽ミサ": "Misa Kagura",
    "天咲光由": "Miyu Amasaki",
    "香藤満月": "Mizuki Kato",
    "向後桃": "Momo Kohgo",
    "渡辺桃": "Momo Watanabe",
    #N
    "羽多乃ナナミ": "Nanami Hatano",
    "刀羅ナツコ": "Natsuko Tora",
    "なつぽい": "Natsupoi",
    "高橋奈七永": "Nanae Takahashi",
    #R
    "八神蘭奈": "Ranna Yagami",
    "ラム会長": "Ram Kaicho",
    "レイチェル・ローズ ": "Raychell Rose",
    "梨杏": "Rian",
    "吏南": "Rina",
    "山下りな": "Rina Yamashita",
    "琉悪夏": "Ruaka",
    #S
    "鹿島沙希": "Saki Kashima",
    "安納サオリ": "Saori Anou",
    "咲蘭": "Saran",
    "飯田沙耶": "Saya Iida",
    "上谷沙弥": "Saya Kamitani",

    "ソイ": "Soy",
    "スターライト・キッド": "Starlight Kid",
    "鈴季すず":"Suzu Suzuki",
    "朱里": "Syuri",
    #T
    "タバタ": "Tabata",
    "本間多恵": "Tae Honma",
    "中野たむ": "Tam Nakano",
    "タイ・メロ": "Tay Melo",
    "テクラ": "Thekla",
    "稲葉ともか": "Tomoka Inaba",
    "稲葉ともか（JTO）": "Tomoka Inaba",
    #U
    "ウナギ・サヤカ": "Unagi Sayaka",
    #V
    "ヴァイプレス": "Vipress",
    #W
    "月山和香": "Waka Tsukiyama",
    #X
    "ジーナ": "Xena",
    #Y
    "マコトユマ": "Yuma Makoto",
    "まなせゆうな": "Yuna Manase",
    "堀田 祐美子": "Yumiko Hotta",
    "岡優里佳": "Yurika Oka",
    "優宇": "Yuu",
    
    #Z
}


def get_card_links() -> list[str]:
    r = requests.get(SCHEDULE_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    return [
        a["href"]
        for a in soup.find_all("a", class_="btn", string="対戦カード")
    ]


def parse_card(url: str) -> tuple[str, list[dict]]:
    r = requests.get(url); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    title_el = soup.select_one("h1.match_head_title")
    base_title = title_el.get_text(strip=True) if title_el else url

    # date
    date_el = soup.select_one("p.date")
    title = f"{date_el.get_text(strip=True)}』{base_title}" if date_el else base_title

    # time
    ticket_el = soup.select_one("a.btnstyle4")
    if ticket_el and ticket_el.get("href"):
        try:
            r2 = requests.get(ticket_el["href"]); r2.raise_for_status()
            soup2 = BeautifulSoup(r2.text, "html.parser")
            for div in soup2.find_all("div", class_="data_bg2"):
                if "本戦開始時間" in div.get_text():
                    span = div.parent.find("span", class_="time")
                    if span:
                        title = f"『{span.get_text(strip=True)} {title}"
                    break
        except requests.RequestException:
            pass

    matches = []
    for wrap in soup.select("div.match_cover div.match_wrap"):
        mt = wrap.select_one("h2.sub_content_title1")
        match_type = mt.get_text(strip=True) if mt else "Match"

        # two-team row style
        row = wrap.find("div", class_="match_block_row")
        if row:
            teams = [
                [n.get_text(strip=True) for n in row.select("div.leftside h3.name")],
                [n.get_text(strip=True) for n in row.select("div.rightside h3.name")],
            ]
        else:
            # N-team column style
            col = wrap.find("div", class_="match_block_column") or []
            uls = col.select("ul.match_block_3col")
            teams = [
                [n.get_text(strip=True) for n in ul.select("h3.name")]
                for ul in uls
            ]

        matches.append({"type": match_type, "teams": teams})

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


def print_match_table(match_type: str, teams: list[list[str]]) -> None:
    # compute rows & widths
    N = len(teams)
    rows = max(len(t) for t in teams)
    widths = [max((disp_len(p) for p in t), default=0) for t in teams]
    w_vs = disp_len("vs")

    # top border
    border_parts = []
    for i in range(N):
        border_parts.append("─" * widths[i])
        if i < N - 1:
            border_parts.append("─" * w_vs)
    top = "┌" + "┬".join(border_parts) + "┐"

    # bottom border
    bottom = "└" + "┴".join(border_parts) + "┘"

    print(match_type)
    print(top)

    mid_row = rows // 2
    for r in range(rows):
        row_parts = []
        for i in range(N):
            cell = teams[i][r] if r < len(teams[i]) else ""
            row_parts.append(pad_center(cell, widths[i]))
            if i < N - 1:
                sep = "vs" if r == mid_row else ""
                row_parts.append(pad_center(sep, w_vs))
        print("│" + "│".join(row_parts) + "│")

    print(bottom)
    print()


def main():
    parser = argparse.ArgumentParser(description="Display Stardom event card.")
    parser.add_argument(
        "-d", "--date", metavar="YYYYMMDD",
        help="Scrape exact date (e.g. 20250517)"
    )
    parser.add_argument(
        "-c", "--compact", action="store_true",
        help="Compact mode: single line per match"
    )
    parser.add_argument(
        "n", nargs="?", type=int, default=1,
        help="Which upcoming show (1=next, 2=second, ...) ignored if --date"
    )
    parser.add_argument(
        "-e", "--english", action="store_true",
        help="Translate match types and names to English"
    )
    args = parser.parse_args()

    # choose URL
    if args.date:
        url = f"https://wwr-stardom.com/event/{args.date}/"
    else:
        links = get_card_links()
        if not links:
            sys.exit("No cards found.")
        if args.n < 1 or args.n > len(links):
            sys.exit(f"Only found {len(links)} card(s).")
        url = links[args.n - 1]

    title, matches = parse_card(url)

    # translation
    if args.english:
        translator = GoogleTranslator(source="ja", target="en")
        originals = [title] + [m["type"] for m in matches]
        for m in matches:
            for team in m["teams"]:
                originals.extend(team)

        # dedupe, preserve order
        seen = {}
        for o in originals:
            if o and o not in seen:
                seen[o] = None
        originals = list(seen.keys())

        # batch translate
        translated = translator.translate_batch(originals)
        mapping = dict(zip(originals, translated))

        # apply overrides
        for jp, en in NAME_OVERRIDES.items():
            mapping[jp] = en

        # remap everything
        title = mapping.get(title, title)
        for m in matches:
            m["type"] = mapping.get(m["type"], m["type"])
            m["teams"] = [
                [mapping.get(p, p) for p in team]
                for team in m["teams"]
            ]

    # print title
    print(f"{title}\n")

    # output
    for idx, m in enumerate(matches, start=1):
        if args.compact:
            num = f"{idx:02d}"
            # join participants within each team by "."
            team_strs = [".".join(team) for team in m["teams"]]
            # .vs. between teams
            line = f"{num}.{m['type']}:" + ".vs.".join(team_strs)
            print(line)
        else:
            print_match_table(m["type"], m["teams"])


if __name__ == "__main__":
    main()
