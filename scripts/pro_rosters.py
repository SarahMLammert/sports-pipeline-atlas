"""Pro rosters with each player's college, matched to the college rosters (high school -> college -> pro).

    python3 scripts/pro_rosters.py nfl                  # this season's 32 NFL rosters
    python3 scripts/pro_rosters.py nba mlb nhl          # several leagues, one after the other
    python3 scripts/pro_rosters.py all                  # every league
    python3 scripts/pro_rosters.py nfl --refresh        # download the rosters again (they change every week)
    python3 scripts/pro_rosters.py nfl --match-only     # only redo the matching, from the saved roster file

Leagues and where their rosters come from (each league's own site):
  nfl   nfl.com team roster pages (a table with a College column)                    -> football
  nba   nba.com team pages (the roster in the page's data, with each player's school)  -> basketball-mens
  mlb   MLB's stats API, 40-man rosters with each player's high school and colleges     -> baseball
  nhl   the NHL's API: rosters, then each player's career, whose NCAA seasons name his college -> hockey-mens

Writes, in rosters/pro/:
  <league>_<season>.csv          every player on a roster: team, name, number, position, status, height, weight,
                                 experience, college, birthplace (MLB, NHL), high school (MLB), profile link, and
                                 college_until: his last college season as the college sport numbers it, worked
                                 out from his years in the league (NFL, NBA), his draft year (MLB) or his NCAA
                                 seasons (NHL)
  <league>_<season>_matched.csv  the same players with what the college rosters know about them: the school
                                 (as config/<sport>/schools.csv names it) and its division, the seasons on that
                                 roster, hometown and high school. matched = "yes" (same name on that school's
                                 roster), "likely" (last name and first names that fit), "hometown" (same name
                                 at another school, born in the town that roster gives as his hometown).

Past seasons (the college rosters start in 2016, so 2016 on is worth reading):
  nfl   nflverse's roster files (one a season, everyone on a roster at the season's end); nfl.com shows only today's
  mlb   the stats API's full-season roster of each team (everyone on it at any time that season)
  nhl   the NHL's API, each team's roster for that season (Arizona before Utah; no Vegas before 2017, Seattle before 2021)
  nba   scripts/nba_history.py (hoopR's open ESPN data) writes the files, then:  pro_rosters.py nba --season 2016-2025 --match-only

    python3 scripts/pro_rosters.py nfl --season 2016-2026        # 2016-2025 from nflverse, 2026 from nfl.com
    python3 scripts/pro_rosters.py mlb --season 2016-2027        # MLB's 2027 is this winter's 40-man rosters
    python3 scripts/pro_rosters.py nhl --season 2016-2026        # 2026 = 2026-27

Then the Pro Pipeline page's data, from every <league>_<season>_matched.csv:

    python3 scripts/pro_rosters.py --build                  # -> docs/pro/pipeline.json

A site that refuses automated visitors is left out, not worked around (wnba.com did on Nov 9).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import io
import json
import re
import string
import sys
from collections import Counter, defaultdict

from bs4 import BeautifulSoup

from core import (CACHE, CONFIG, ROOT, ROSTERS, Fetcher, Levels, clean, load_sport, name_key, read_csv, season_files,
                  write_csv)

PRO_DIR = ROSTERS / "pro"
PAGE_DATA = ROOT / "docs" / "pro" / "pipeline.json"
PRO_TEAMS = CONFIG / "shared" / "pro_teams.csv"     # each pro team's city and where it plays, for the map

# Past NFL seasons: nflverse's roster file for a season (on GitHub), and its team codes
NFLVERSE_URL = "https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{season}.csv"
NFL_CODES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens", "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers", "CHI": "Chicago Bears", "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys", "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars", "KC": "Kansas City Chiefs",
    "LA": "Los Angeles Rams", "LAC": "Los Angeles Chargers", "SD": "San Diego Chargers", "LV": "Las Vegas Raiders", "OAK": "Oakland Raiders",
    "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings", "NE": "New England Patriots", "NO": "New Orleans Saints",
    "NYG": "New York Giants", "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers", "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders",
}
# NFL statuses of players no longer with the team (released, retired, traded): left off the page
GONE = {"CUT", "RET", "TRD", "TRC"}

NFL_TEAMS = [
    "arizona-cardinals", "atlanta-falcons", "baltimore-ravens", "buffalo-bills", "carolina-panthers",
    "chicago-bears", "cincinnati-bengals", "cleveland-browns", "dallas-cowboys", "denver-broncos",
    "detroit-lions", "green-bay-packers", "houston-texans", "indianapolis-colts", "jacksonville-jaguars",
    "kansas-city-chiefs", "las-vegas-raiders", "los-angeles-chargers", "los-angeles-rams", "miami-dolphins",
    "minnesota-vikings", "new-england-patriots", "new-orleans-saints", "new-york-giants", "new-york-jets",
    "philadelphia-eagles", "pittsburgh-steelers", "san-francisco-49ers", "seattle-seahawks",
    "tampa-bay-buccaneers", "tennessee-titans", "washington-commanders",
]
NBA_TEAMS = {   # nba.com team id -> the name in its address
    1610612737: "hawks", 1610612738: "celtics", 1610612739: "cavaliers", 1610612740: "pelicans",
    1610612741: "bulls", 1610612742: "mavericks", 1610612743: "nuggets", 1610612744: "warriors",
    1610612745: "rockets", 1610612746: "clippers", 1610612747: "lakers", 1610612748: "heat", 1610612749: "bucks",
    1610612750: "timberwolves", 1610612751: "nets", 1610612752: "knicks", 1610612753: "magic", 1610612754: "pacers",
    1610612755: "sixers", 1610612756: "suns", 1610612757: "blazers", 1610612758: "kings", 1610612759: "spurs",
    1610612760: "thunder", 1610612761: "raptors", 1610612762: "jazz", 1610612763: "grizzlies",
    1610612764: "wizards", 1610612765: "pistons", 1610612766: "hornets",
}
MLB_TEAMS = {   # MLB stats API team id -> name
    108: "Los Angeles Angels", 109: "Arizona Diamondbacks", 110: "Baltimore Orioles", 111: "Boston Red Sox",
    112: "Chicago Cubs", 113: "Cincinnati Reds", 114: "Cleveland Guardians", 115: "Colorado Rockies",
    116: "Detroit Tigers", 117: "Houston Astros", 118: "Kansas City Royals", 119: "Los Angeles Dodgers",
    120: "Washington Nationals", 121: "New York Mets", 133: "Athletics", 134: "Pittsburgh Pirates",
    135: "San Diego Padres", 136: "Seattle Mariners", 137: "San Francisco Giants", 138: "St. Louis Cardinals",
    139: "Tampa Bay Rays", 140: "Texas Rangers", 141: "Toronto Blue Jays", 142: "Minnesota Twins",
    143: "Philadelphia Phillies", 144: "Atlanta Braves", 145: "Chicago White Sox", 146: "Miami Marlins",
    147: "New York Yankees", 158: "Milwaukee Brewers",
}
NHL_TEAMS = {
    "ANA": "Anaheim Ducks", "BOS": "Boston Bruins", "BUF": "Buffalo Sabres", "CAR": "Carolina Hurricanes",
    "CBJ": "Columbus Blue Jackets", "CGY": "Calgary Flames", "CHI": "Chicago Blackhawks", "COL": "Colorado Avalanche",
    "DAL": "Dallas Stars", "DET": "Detroit Red Wings", "EDM": "Edmonton Oilers", "FLA": "Florida Panthers",
    "LAK": "Los Angeles Kings", "MIN": "Minnesota Wild", "MTL": "Montreal Canadiens", "NJD": "New Jersey Devils",
    "NSH": "Nashville Predators", "NYI": "New York Islanders", "NYR": "New York Rangers", "OTT": "Ottawa Senators",
    "PHI": "Philadelphia Flyers", "PIT": "Pittsburgh Penguins", "SEA": "Seattle Kraken", "SJS": "San Jose Sharks",
    "STL": "St. Louis Blues", "TBL": "Tampa Bay Lightning", "TOR": "Toronto Maple Leafs", "UTA": "Utah Mammoth",
    "VAN": "Vancouver Canucks", "VGK": "Vegas Golden Knights", "WPG": "Winnipeg Jets", "WSH": "Washington Capitals",
}
# The leagues an NHL player's college seasons are filed under: "NCAA" in recent seasons, the conference before
NHL_COLLEGE_LEAGUES = {"NCAA", "H-East", "Hockey East", "ECAC", "NCHC", "Big Ten", "Big-10", "WCHA", "CCHA", "AHA",
                       "Atlantic Hockey", "CHA"}

LEAGUES = {
    "nfl": {"teams": NFL_TEAMS, "url": "https://www.nfl.com/teams/{team}/roster", "college_sport": "football",
            "site": "https://www.nfl.com", "new_season_month": 3,
            # the league's own spellings that fit more than one school: NFL.com writes Miami (OH) as "Miami (Ohio)"
            "colleges": {"Miami": "Miami (FL)",
                         # nflverse's spellings (past seasons)
                         "Miami, O.": "Miami (OH)", "Ohio U.": "Ohio", "Southern U.": "Southern", "Albany, N.Y.": "Albany",
                         "Charleston, W. Va.": "Charleston (WV)", "Augustana, S.D.": "Augustana (SD)",
                         "Northwestern State-Louisiana": "Northwestern State", "Northwestern State, La.": "Northwestern State",
                         "Monmouth, N.J.": "Monmouth", "Monmouth, Ill.": "Monmouth (IL)", "Marian, Ind.": "Marian (IN)",
                         "Wayne State, Mich.": "Wayne State (MI)", "Albany State, Ga.": "Albany State (GA)",
                         "Texas State-San Marcos": "Texas State", "Southern Utah State": "Southern Utah",
                         "UMass Amherst": "UMass", "Grand Valley": "Grand Valley State"}},
    "nba": {"teams": list(NBA_TEAMS), "url": "https://www.nba.com/team/{team}/{slug}", "college_sport": "basketball-mens",
            "new_season_month": 7, "colleges": {"Miami": "Miami (FL)", "St. Mary's": "Saint Mary's (CA)"}},
    "mlb": {"teams": list(MLB_TEAMS), "college_sport": "baseball", "new_season_month": 11,
            "colleges": {"Miami": "Miami (FL)", "St. Mary's": "Saint Mary's (CA)", "Cal State Stanislaus": "Stanislaus State",
                         "Centenary College of Louisiana": "Centenary", "Sacramento CC": "Sacramento City College",
                         "State College of Florida": "State College of Florida, Manatee-Sarasota",
                         "Caldwell Tech CC": "Caldwell CC"},
            "url": "https://statsapi.mlb.com/api/v1/teams/{team}/roster?rosterType=40Man&hydrate=person(education)",
            # a past season: everyone who was on the team at any time that season
            "past_url": "https://statsapi.mlb.com/api/v1/teams/{team}/roster?rosterType=fullSeason&season={season}&hydrate=person(education)"},
    "nhl": {"teams": list(NHL_TEAMS), "url": "https://api-web.nhle.com/v1/roster/{team}/current",
            "past_url": "https://api-web.nhle.com/v1/roster/{team}/{season}{next}",     # 2018 = 2018-19: 20182019
            "player_url": "https://api-web.nhle.com/v1/player/{id}/landing", "college_sport": "hockey-mens",
            "new_season_month": 7, "colleges": {"Miami U.": "Miami (OH)"}},
}
ROSTER_FIELDS = ["league", "season", "team", "name", "number", "position", "status", "height", "weight",
                 "experience", "college", "college_until", "birth_city", "birth_state", "birth_country",
                 "pro_high_school", "profile_url", "player_id", "other_name"]
MATCH_FIELDS = ROSTER_FIELDS + ["college_school", "college_level", "matched", "college_name", "college_first",
                                "college_last", "hometown", "home_state", "home_country", "high_school"]
# The roster table's columns, by header text
_COLUMNS = {"player": "name", "name": "name", "no": "number", "#": "number", "pos": "position",
            "position": "position", "status": "status", "height": "height", "ht": "height", "weight": "weight",
            "wt": "weight", "experience": "experience", "exp": "experience", "college": "college"}
_SUFFIX = re.compile(r"\s+(jr|sr|ii|iii|iv|v)\.?$", re.I)


def season_now(today: dt.date | None = None, league: str = "nfl") -> int:
    """The season a league's rosters show now, named by the year it starts: NFL rosters from March on belong to
    the coming fall, NBA and NHL ones from July (2026-27 = 2026), MLB's 40-man rosters from November to next
    year's season."""
    today = today or dt.date.today()
    month = LEAGUES[league]["new_season_month"]
    if month == 11:
        return today.year + 1 if today.month >= 11 else today.year
    return today.year if today.month >= month else today.year - 1


def _int(v) -> int | None:
    s = str(v or "").strip()
    return int(s) if s.isdigit() else None


# ---- reading each league's rosters ---------------------------------------------------------------------------

def parse_roster_page(html: str, site: str = "") -> list[dict]:
    """The players in a league roster page: the table with Player and College columns (NFL)."""
    soup = BeautifulSoup(html, "lxml")
    out = []
    for table in soup.find_all("table"):
        head = table.find("thead") or table.find("tr")
        if not head:
            continue
        headers = [_COLUMNS.get(clean(th.get_text(" ")).lower().strip(" .:"), "") for th in head.find_all(["th", "td"])]
        if "name" not in headers or "college" not in headers:
            continue
        for tr in (table.find("tbody") or table).find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) < len(headers) or tr is head:
                continue
            rec = {}
            for field, cell in zip(headers, cells):
                if not field:
                    continue
                if field == "name":
                    link = cell.find("a", href=True)
                    rec["name"] = clean((link or cell).get_text(" "))
                    href = link["href"] if link else ""
                    rec["profile_url"] = (site + href) if href.startswith("/") else href
                else:
                    rec[field] = clean(cell.get_text(" "))
            if rec.get("name"):
                out.append(rec)
    return out


def parse_nba_page(html: str) -> list[dict]:
    """The roster in an nba.com team page's data (the __NEXT_DATA__ script): name, number, position, height,
    weight, years in the league ("R" for a rookie) and school."""
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("script", id="__NEXT_DATA__")
    try:
        roster = json.loads(tag.string)["props"]["pageProps"]["team"]["roster"] if tag and tag.string else []
    except (ValueError, KeyError, TypeError):
        return []
    out = []
    for p in roster or []:
        name = clean(p.get("PLAYER"))
        if not name:
            continue
        slug, pid = p.get("PLAYER_SLUG") or "", p.get("PLAYER_ID") or ""
        out.append({"name": name, "number": clean(p.get("NUM")), "position": clean(p.get("POSITION")),
                    "height": clean(p.get("HEIGHT")), "weight": clean(p.get("WEIGHT")),
                    "experience": clean(p.get("EXP")), "college": clean(p.get("SCHOOL")),
                    "profile_url": f"https://www.nba.com/player/{pid}/{slug}" if pid else ""})
    return out


def parse_mlb_roster(text: str) -> list[dict]:
    """A team's 40-man roster from MLB's stats API, with each player's education: his colleges (several when he
    went to a junior college first, joined with " | "), his high school and his draft year."""
    try:
        roster = json.loads(text).get("roster", [])
    except ValueError:
        return []
    out = []
    for e in roster:
        p = e.get("person") or {}
        name = clean(p.get("fullName"))
        if not name:
            continue
        edu = p.get("education") or {}
        colleges = [clean(c.get("name")) for c in edu.get("colleges", []) if clean(c.get("name"))]
        hs = (edu.get("highschools") or [{}])[0]
        high_school = ", ".join(x for x in (clean(hs.get("name")), clean(hs.get("city")), clean(hs.get("state"))) if x)
        out.append({"name": name, "number": clean(e.get("jerseyNumber")),
                    "position": clean((e.get("position") or {}).get("abbreviation")),
                    "status": clean((e.get("status") or {}).get("description")),
                    "height": clean(p.get("height")), "weight": clean(p.get("weight")),
                    "debut": _int(clean(p.get("mlbDebutDate"))[:4]), "college": " | ".join(colleges),
                    # drafted out of college in June: his last college season is the spring of his draft year
                    "college_until": (p.get("draftYear") or "") if colleges else "",
                    "birth_city": clean(p.get("birthCity")), "birth_state": clean(p.get("birthStateProvince")),
                    "birth_country": clean(p.get("birthCountry")), "pro_high_school": high_school,
                    "profile_url": f"https://www.mlb.com/player/{p['id']}" if p.get("id") else ""})
    return out


def _default(v) -> str:
    return clean(v.get("default") if isinstance(v, dict) else v)


def parse_nhl_roster(text: str) -> list[dict]:
    """A team's roster from the NHL's API (forwards, defensemen, goalies). 'id' is for the player's own page."""
    try:
        data = json.loads(text)
    except ValueError:
        return []
    out = []
    for group in ("forwards", "defensemen", "goalies"):
        for p in data.get(group, []):
            name = f"{_default(p.get('firstName'))} {_default(p.get('lastName'))}".strip()
            if not name:
                continue
            inches = _int(p.get("heightInInches"))
            out.append({"id": p.get("id"), "name": name, "number": clean(p.get("sweaterNumber")),
                        "position": clean(p.get("positionCode")),
                        "height": f"{inches // 12}-{inches % 12}" if inches else "",
                        "weight": clean(p.get("weightInPounds")), "birth_city": _default(p.get("birthCity")),
                        "birth_state": _default(p.get("birthStateProvince")),
                        "birth_country": clean(p.get("birthCountry")),
                        "profile_url": f"https://www.nhl.com/player/{p['id']}" if p.get("id") else ""})
    return out


def nhl_college(text: str) -> tuple[str, int | None, int | None]:
    """(college, his last college season, his first NHL season) from a player's career in the NHL's API. College
    seasons are the regular seasons filed under NCAA or a college conference; "20152016" is season 2016 as
    college hockey numbers it. Several colleges (a transfer) are joined with " | ", the last one last."""
    try:
        seasons = json.loads(text).get("seasonTotals", [])
    except ValueError:
        return "", None, None
    colleges, last, first_nhl = [], None, None
    for s in sorted((s for s in seasons if s.get("gameTypeId") == 2), key=lambda s: (s.get("season", 0), s.get("sequence", 0))):
        year = _int(str(s.get("season", ""))[4:])
        league = clean(s.get("leagueAbbrev"))
        if league in NHL_COLLEGE_LEAGUES:
            team = _default(s.get("teamName"))
            if team and team not in colleges:
                colleges.append(team)
            last = year
        elif league == "NHL" and first_nhl is None:
            first_nhl = year
    return " | ".join(colleges), last, first_nhl


def _years_in_league(experience: str) -> int | None:
    """NFL.com's and nba.com's experience: 'R' for a rookie, else seasons in the league."""
    e = (experience or "").strip().upper()
    return 0 if e == "R" else int(e) if e.isdigit() else None


def college_until(league: str, season: int, experience: str) -> int | None:
    """His last college season, as the college sport numbers it, if he went straight to the league. Football
    names a season by its fall (an NFL rookie of 2026 last played college football in 2025); basketball by its
    spring (an NBA rookie of 2026-27 last played in 2025-26, season 2026)."""
    years = _years_in_league(experience)
    if years is None:
        return None
    return season - years - 1 if league == "nfl" else season - years


def parse_nflverse(text: str, season: int) -> list[dict]:
    """A season's NFL players from nflverse's roster file: everyone on a roster at the season's end (week 17-22),
    with college ("Wisconsin; Wisconsin-Stevens Point" when he went to several) and the year he came into the
    league, so his last college season is the fall before it."""
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        name = clean(r.get("full_name") or f"{r.get('first_name', '')} {r.get('last_name', '')}")
        if not name:
            continue
        legal = clean(f"{r.get('first_name', '')} {r.get('last_name', '')}")
        years, entry = _int(r.get("years_exp")), _int(r.get("entry_year")) or _int(r.get("rookie_year"))
        until = entry - 1 if entry else season - years - 1 if years is not None else ""
        rows.append({"league": "NFL", "season": season, "team": NFL_CODES.get(r.get("team", ""), r.get("team", "")),
                     "name": name, "number": r.get("jersey_number", ""), "position": r.get("position", ""),
                     "status": r.get("status", ""), "height": r.get("height", ""), "weight": r.get("weight", ""),
                     "experience": "" if years is None else years,
                     # "Texas A&amp;M" in some seasons: unescape before splitting on ";"
                     "college": "|".join(x.strip() for x in html.unescape(r.get("college") or "").split(";")
                                         if x.strip() and x.strip() != "No College"),
                     "college_until": until, "player_id": r.get("gsis_id") or r.get("esb_id") or "",
                     "other_name": legal if name_key(legal) != name_key(name) else ""})
    return rows


def nflverse(season: int, refresh: bool) -> list[dict]:
    fetcher = Fetcher(cache_dir=CACHE, refresh=refresh, delay=1.0, timeout=60)
    url = NFLVERSE_URL.format(season=season)
    try:
        status, _, text = fetcher.get(url, remember_miss=False)
    except Exception as exc:  # network trouble: say so, the next season still runs
        print(f"  problem: {url}: {exc}")
        return []
    rows = parse_nflverse(text, season) if status == 200 else []
    print(f"  nflverse {season}: {len(rows)} players" + ("" if rows else f" (HTTP {status})"))
    return rows


# NHL teams by season: Vegas from 2017-18, Seattle from 2021-22, and Utah (2024-25 on) was Arizona before
NHL_PAST = {"ARI": "Arizona Coyotes"}


def teams_for(league: str, season: int) -> list:
    if league != "nhl":
        return list(LEAGUES[league]["teams"])
    out = [t for t in NHL_TEAMS if not (t == "VGK" and season < 2017) and not (t == "SEA" and season < 2021)
           and not (t == "UTA" and season < 2024)]
    return out + (["ARI"] if season < 2024 else [])


def scrape(league: str, season: int, refresh: bool) -> list[dict]:
    conf = LEAGUES[league]
    past = season < season_now(league=league) and "past_url" in conf
    fetcher = Fetcher(cache_dir=CACHE, refresh=refresh, delay=2.0)
    careers = Fetcher(cache_dir=CACHE, refresh=False, delay=1.0)     # an NHL player's past seasons don't change
    rows, problems = [], []
    for team in teams_for(league, season):
        url = (conf["past_url"] if past else conf["url"]).format(team=team, slug=NBA_TEAMS.get(team, ""), season=season,
                                                                 next=season + 1)
        label = {"nba": f"{NBA_TEAMS.get(team, '')}".title(), "mlb": MLB_TEAMS.get(team, ""),
                 "nhl": NHL_TEAMS.get(team) or NHL_PAST.get(team, "")}.get(league) or string.capwords(str(team).replace("-", " "))
        try:
            status, _, text = fetcher.get(url, remember_miss=False)
        except Exception as exc:  # network trouble: say which team, keep going
            problems.append(f"{label}: {exc}")
            continue
        if status != 200:
            players = []
        elif league == "nfl":
            players = parse_roster_page(text, conf["site"])
        elif league == "nba":
            players = parse_nba_page(text)
        elif league == "mlb":
            players = parse_mlb_roster(text)
        else:
            players = parse_nhl_roster(text)
        if not players:
            problems.append(f"{label}: HTTP {status}, no players read")
        for p in players:
            if league == "nhl" and p.get("id"):
                try:
                    st, _, career = careers.get(conf["player_url"].format(id=p["id"]), remember_miss=False)
                except Exception as exc:  # network trouble: say which team, keep going
                    problems.append(f"{label}, {p['name']}: {exc}")
                    st, career = 0, ""
                if st == 200:
                    p["college"], until, first_nhl = nhl_college(career)
                    p["college_until"] = until or ""
                    p["experience"] = season - first_nhl if first_nhl else ""
            elif league == "mlb":
                p["experience"] = season - p["debut"] if p.get("debut") else ""      # seasons since his debut
            elif league in ("nfl", "nba"):
                p["college_until"] = college_until(league, season, p.get("experience", "")) or ""
            rows.append({"league": league.upper(), "season": season, "team": label,
                         **{f: p.get(f, "") for f in ROSTER_FIELDS if f not in ("league", "season", "team")}})
        print(f"  {label:24} {len(players):3} players")
    if league == "nhl" and past:
        rows += nhl_from_careers(season, rows, careers)
    for p in problems:
        print("  problem:", p)
    return rows


# The NHL's past-season rosters can be short (about 20 a team from 2023-24 on, where earlier seasons list everyone who
# played) or empty (Arizona 2023-24). Each player's career says which NHL teams he played for each season, so the
# players already known from any NHL roster file fill those gaps: whoever played for a team that season is added.
NHL_CAREER_TEAMS = {"Utah Hockey Club": "Utah Mammoth", "Montréal Canadiens": "Montreal Canadiens"}


def nhl_from_careers(season: int, rows: list[dict], careers: Fetcher) -> list[dict]:
    have = {(r["team"], r.get("profile_url")) for r in rows}
    ids = set()
    for path in PRO_DIR.glob("nhl_*.csv"):
        if not path.name.endswith("_matched.csv"):
            ids |= {r["profile_url"].rsplit("/", 1)[-1] for r in read_csv(path) if r.get("profile_url")}
    ids |= {r["profile_url"].rsplit("/", 1)[-1] for r in rows if r.get("profile_url")}
    teams = set(NHL_TEAMS.values()) | set(NHL_PAST.values())
    want, added = f"{season}{season + 1}", Counter()
    out = []
    for pid in sorted(i for i in ids if i.isdigit()):
        try:
            st, _, text = careers.get(LEAGUES["nhl"]["player_url"].format(id=pid), remember_miss=False)
            data = json.loads(text) if st == 200 else {}
        except Exception:  # not saved and no network: skip him
            continue
        played = {NHL_CAREER_TEAMS.get(_default(s.get("teamName")), _default(s.get("teamName")))
                  for s in data.get("seasonTotals", [])
                  if str(s.get("season")) == want and s.get("gameTypeId") == 2 and s.get("leagueAbbrev") == "NHL"}
        url = f"https://www.nhl.com/player/{pid}"
        college, until, first_nhl = nhl_college(text)
        inches = _int(data.get("heightInInches"))
        for team in played & teams:
            if (team, url) in have:
                continue
            added[team] += 1
            out.append({"league": "NHL", "season": season, "team": team,
                        "name": f"{_default(data.get('firstName'))} {_default(data.get('lastName'))}".strip(),
                        "number": clean(data.get("sweaterNumber")), "position": clean(data.get("position")), "status": "",
                        "height": f"{inches // 12}-{inches % 12}" if inches else "", "weight": clean(data.get("weightInPounds")),
                        "experience": season - first_nhl if first_nhl else "", "college": college,
                        "college_until": until or "", "birth_city": _default(data.get("birthCity")),
                        "birth_state": _default(data.get("birthStateProvince")), "birth_country": clean(data.get("birthCountry")),
                        "pro_high_school": "", "profile_url": url, "player_id": pid, "other_name": ""})
    if out:
        print(f"  + {len(out)} more players from their careers ({len(added)} teams; most: "
              f"{', '.join(f'{t} {n}' for t, n in added.most_common(3))})")
    return out


# ---- matching to the college rosters ---------------------------------------------------------------------------

def _last_name_key(name: str) -> str:
    parts = _SUFFIX.sub("", clean(name)).split()
    return name_key(parts[-1]) if parts else ""


def college_index(sport_name: str) -> dict[tuple[str, str], dict]:
    """(school, name key) -> first/last season, hometown and high school, from the sport's season files."""
    sport = load_sport(sport_name)
    idx: dict[tuple[str, str], dict] = {}
    for season, path in sorted(season_files(sport.rosters_dir).items()):
        for r in read_csv(path):
            k = (r["school"], name_key(_SUFFIX.sub("", r["name"])))
            got = idx.get(k)
            if got is None:
                idx[k] = got = {"college_first": season, "hometown": "", "home_city": "", "home_state": "",
                                "home_country": "", "high_school": "", "college_name": r["name"],
                                "last_key": _last_name_key(r["name"]), "school": r["school"]}
            got["college_last"] = season
            for f in ("hometown", "home_city", "home_state", "home_country", "high_school"):
                if r.get(f):
                    got[f] = r[f]          # the latest season that has it
    return idx


def college_spellings(text: str) -> list[str]:
    """The league's name for a college, then the ways schools.csv may write it: MLB writes "Chipola JC",
    "Miami Dade CC", "JC of Central Florida" and "Aurora U" for Chipola College, Miami Dade College, College of
    Central Florida and Aurora (University)."""
    out = [text]
    of = re.sub(r"^(?:JC|CC) of\b", "College of", text)
    out += [of, re.sub(r"\b(?:JC|CC)$", "College", of), re.sub(r"\s*\b(?:JC|CC)$", "", of), re.sub(r"\bU$", "University", of)]
    return list(dict.fromkeys(x.strip() for x in out if x.strip()))


def _first_names_fit(pro: str, college: str) -> bool:
    """Could these be the same person's first names? Same first letter (Pat/Patrick, Mike/Michael), one inside
    the other (Riq/Tariq, Cobie/Decobie), or the pro name written into the college one (Ahmad "Sauce")."""
    a = name_key(clean(pro).split()[0]) if clean(pro) else ""
    whole = name_key(college)
    b = name_key(clean(college).split()[0]) if clean(college) else ""
    if not a or not b:
        return False
    return a[0] == b[0] or a in b or b in a or (len(a) >= 3 and a in whole[:-len(_last_name_key(college)) or None])


def _born_there(r: dict, info: dict) -> bool:
    """Is the town the pro league gives as his birthplace the hometown on the college roster?"""
    city, home = name_key(r.get("birth_city", "")), name_key(info.get("home_city", ""))
    if not city or city != home:
        return False
    a, b = (r.get("birth_state") or "").upper(), (info.get("home_state") or "").upper()
    return not a or not b or a == b


def _fits(until: int | None, info: dict) -> bool:
    return until is None or until - 2 <= int(info["college_last"]) <= until + 1


def match(rows: list[dict], league: str) -> list[dict]:
    """Find each pro player on his college's roster.

    matched = "yes": the same name on that school's roster (with several colleges listed, the one he's found
    at). "likely": the same last name at that school and first names that fit (_first_names_fit: "Sauce Gardner"
    is Ahmad "Sauce" Gardner, "Pat Surtain II" Patrick Surtain), taken only when exactly one such player's last
    college season fits the one worked out for him (college_until, give or take). "hometown": the league's
    college isn't found or his name isn't on its roster, but exactly one player with his name, at any school,
    lists the town he was born in as his hometown, in seasons that fit. Nicknames unlike the name ("Bam" for
    Zonovan Knight) stay unmatched rather than risk a wrong person."""
    conf = LEAGUES[league]
    sport = load_sport(conf["college_sport"])
    levels = Levels.load(sport)
    idx = college_index(sport.name)
    by_last, by_name = defaultdict(list), defaultdict(list)
    for (school, nk), info in idx.items():
        by_last[(school, info["last_key"])].append(info)
        by_name[nk].append(info)
    out = []
    for r in rows:
        season = int(r["season"])
        until = _int(r.get("college_until"))
        if until is None and league == "nfl":            # roster files saved before college_until existed
            until = college_until(league, season, r.get("experience", ""))
        nk = name_key(_SUFFIX.sub("", r["name"]))
        # nflverse gives the legal name too (Ahmad Gardner for Sauce Gardner): either may be on the college roster
        keys = list(dict.fromkeys(k for k in (nk, name_key(_SUFFIX.sub("", r.get("other_name") or ""))) if k))
        listed = [x.strip() for x in (r.get("college") or "").split("|") if x.strip()]
        schools = []
        for text in listed:
            for name in college_spellings(conf.get("colleges", {}).get(text, text)):
                lvl, school = levels.level(name, (until or season - 1))
                if school:
                    schools.append((lvl, school))
                    break
        level, school = schools[-1] if schools else ("", "")
        hit, how = None, ""
        for lvl, sch in schools:
            for k in keys:
                if not hit and (sch, k) in idx:
                    (level, school), hit, how = (lvl, sch), idx[(sch, k)], "yes"
        if not hit and schools:
            fits = [i for lvl, sch in schools for i in by_last.get((sch, _last_name_key(r["name"])), [])
                    if until is not None and _fits(until, i) and _first_names_fit(r["name"], i["college_name"])]
            if len(fits) == 1:
                hit, how = fits[0], "likely"
                level, school = next((lvl, sch) for lvl, sch in schools if sch == hit["school"])
        if not hit and listed and r.get("birth_city"):
            fits = [i for i in by_name.get(nk, []) if _born_there(r, i) and _fits(until, i)]
            if len(fits) == 1:
                hit, how = fits[0], "hometown"
                school = hit["school"]
                level = levels.level(school, int(hit["college_last"]))[0]
        info = {k: v for k, v in (hit or {}).items() if k not in ("last_key", "school", "home_city")}
        out.append({**r, "college_school": school, "college_level": level if school else "", "matched": how, **info})
    return out


def summary(rows: list[dict]) -> None:
    n = len(rows)
    with_college = sum(1 for r in rows if r["college"])
    known = sum(1 for r in rows if r["college_school"])
    matched = Counter(r["matched"] for r in rows if r["matched"])
    total = sum(matched.values())
    print(f"{n} players; {with_college} list a college; {known} of those colleges are in schools.csv; "
          f"{total} found on a college roster ({total / max(1, with_college):.0%} of those with a college; "
          f"{matched['yes']} by name, {matched['likely']} by last name, {matched['hometown']} by hometown)")
    print("  by division:", dict(Counter(r["college_level"] or "?" for r in rows if r["matched"]).most_common()))
    print("  with a hometown:", sum(1 for r in rows if r.get("hometown")),
          "| with a high school:", sum(1 for r in rows if r.get("high_school") or r.get("pro_high_school")))
    missing = Counter(c for r in rows if r["college"] and not r["college_school"] for c in [r["college"]])
    if missing:
        print("  colleges not in schools.csv (most players first):", missing.most_common(15))
    unmatched = Counter(r["college_school"] for r in rows if r["college_school"] and not r["matched"])
    if unmatched:
        print("  known college, name not on its roster (most first):", unmatched.most_common(10))


def run(league: str, season: int | None, refresh: bool, match_only: bool) -> int:
    season = season or season_now(league=league)
    roster_path = PRO_DIR / f"{league}_{season}.csv"
    if match_only:
        rows = read_csv(roster_path)
        if not rows:
            print(f"{roster_path} not found or empty: run without --match-only first.")
            return 1
    elif league == "nfl" and season < season_now(league="nfl"):     # a past season: nfl.com shows only today's
        print(f"NFL {season}: nflverse's roster file")
        rows = nflverse(season, refresh)
        if not rows:
            return 1
        write_csv(roster_path, ROSTER_FIELDS, rows)
        print(f"-> {roster_path}")
    elif season > season_now(league=league) or (season < season_now(league=league) and "past_url" not in LEAGUES[league]):
        print(f"{league.upper()} {season}: only this season's rosters ({season_now(league=league)}) can be read here; "
              "past NBA seasons come from scripts/nba_history.py, then --match-only.")
        return 1
    else:
        print(f"{league.upper()} {season}: reading {len(teams_for(league, season))} rosters")
        rows = scrape(league, season, refresh)
        if not rows:
            print("No players read; nothing saved.")
            return 1
        write_csv(roster_path, ROSTER_FIELDS, rows)
        print(f"-> {roster_path}")
    matched = match(rows, league)
    out_path = PRO_DIR / f"{league}_{season}_matched.csv"
    write_csv(out_path, MATCH_FIELDS, matched)
    summary(matched)
    print(f"-> {out_path}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("leagues", nargs="*", metavar="league", help=f"{', '.join(LEAGUES)} or all")
    ap.add_argument("--season", type=seasons_arg, default=[None],
                    help="a season or a range (2017-2026); default: the season each league's rosters show now")
    ap.add_argument("--refresh", action="store_true", help="download the rosters again")
    ap.add_argument("--match-only", action="store_true", help="redo the matching from the saved roster file")
    ap.add_argument("--build", action="store_true", help=f"then write the Pro Pipeline page's data ({PAGE_DATA.name})")
    args = ap.parse_args(argv)
    if not args.leagues and not args.build:
        ap.error("name a league, or --build")
    wrong = [x for x in args.leagues if x not in LEAGUES and x != "all"]
    if wrong:
        ap.error(f"unknown league {', '.join(wrong)} (choose from {', '.join(LEAGUES)}, all)")
    PRO_DIR.mkdir(parents=True, exist_ok=True)
    leagues = list(LEAGUES) if "all" in args.leagues else list(dict.fromkeys(args.leagues))
    failed = [f"{lg} {s or ''}".strip() for lg in leagues for s in args.season if run(lg, s, args.refresh, args.match_only)]
    if failed:
        print("No result for:", ", ".join(failed))
    if args.build:
        build_page_data()
    return 1 if failed else 0


def seasons_arg(text: str) -> list[int]:
    m = re.fullmatch(r"(\d{4})(?:-(\d{4}))?", text.strip())
    if not m:
        raise argparse.ArgumentTypeError("a season (2026) or a range (2017-2026)")
    a, b = int(m[1]), int(m[2] or m[1])
    return list(range(min(a, b), max(a, b) + 1))


# ---- the Pro Pipeline page's data ------------------------------------------------------------------------------

def _hometown_places(sport_name: str) -> dict[tuple[str, str], tuple[float, float]]:
    """(hometown text, school or "") -> (lat, lon), from the sport's geocoded hometowns."""
    out = {}
    for r in read_csv(ROSTERS / sport_name / "hometowns.csv"):
        try:
            out[(r["hometown"], r.get("school", ""))] = (round(float(r["lat"]), 4), round(float(r["lon"]), 4))
        except (TypeError, ValueError, KeyError):
            continue
    return out


def _campuses() -> dict[str, tuple[str, str, float, float]]:
    out = {}
    for r in read_csv(CONFIG / "shared" / "school_locations.csv"):
        try:
            out[r["school"]] = (r["city"], r["state"], round(float(r["lat"]), 4), round(float(r["lon"]), 4))
        except (TypeError, ValueError, KeyError):
            continue
    return out


def build_page_data(out_path=PAGE_DATA, pro_dir=None) -> dict:
    """docs/pro/pipeline.json: every pro player found with a college, once per league, with his teams by season,
    his college and division, and his hometown and high school with the hometown's place on the map.

    A player is one person across seasons: the same player on the college roster (or, not found there, the same
    name and college) in one league; nflverse's past seasons and nfl.com's current one don't share an id. Players the league lists as released, retired or traded that season
    (GONE) leave that season out. Columns, so the file stays small; -1 = none:
      players.g league, n name, p position, c college (schools), lv division, h hometown, s state or country,
      hs high school, at hometown [lat, lon] or null, m how he was matched (1 name, 2 last name, 3 hometown,
      0 college only), t [[team, first season, last season], ...] in order."""
    pro_dir = pro_dir or PRO_DIR
    teams_conf = {(r["league"], r["team"].lower()): r for r in read_csv(PRO_TEAMS)}
    campuses = _campuses()
    leagues, teams, schools = [], [], []
    team_ix, school_ix = {}, {}
    people: dict[tuple, dict] = {}
    MATCH_CODE = {"yes": 1, "likely": 2, "hometown": 3}
    places_by_sport: dict[str, dict] = {}
    files = sorted(pro_dir.glob("*_matched.csv"))
    seasons_by_league = defaultdict(set)
    for path in files:
        league = path.name.split("_")[0]
        if league not in LEAGUES:
            continue
        sport_name = LEAGUES[league]["college_sport"]
        places = places_by_sport.setdefault(sport_name, _hometown_places(sport_name))
        for r in read_csv(path):
            if not r.get("college_school") or (r.get("status") or "").upper() in GONE:
                continue
            season = int(r["season"])
            lg = league.upper()
            seasons_by_league[lg].add(season)
            tkey = (lg, (r["team"] or "").lower())
            if tkey not in team_ix:
                t = teams_conf.get(tkey, {})
                team_ix[tkey] = len(teams)
                lat, lon = t.get("lat"), t.get("lon")
                teams.append([lg, t.get("name") or r["team"], t.get("city", ""), t.get("state", ""),
                              float(lat) if lat else None, float(lon) if lon else None, t.get("color", ""), t.get("color2", "")])
            school = r["college_school"]
            if school not in school_ix:
                school_ix[school] = len(schools)
                c = campuses.get(school)
                schools.append([school, c[0] if c else "", c[1] if c else "", c[2] if c else None, c[3] if c else None])
            # one person: the college roster's player when he was found there (nflverse calls Sauce Gardner
            # "Ahmad Gardner" in some seasons), else his name at that college
            key = ((lg, school, name_key(r["college_name"]), r.get("college_first", "")) if r.get("college_name")
                   else (lg, school, name_key(_SUFFIX.sub("", r["name"]))))
            p = people.get(key)
            if p is None:
                p = people[key] = {"g": lg, "n": r["name"], "p": r.get("position", ""), "c": school_ix[school],
                                   "lv": r.get("college_level", ""), "h": "", "s": "", "hs": "", "at": None,
                                   "m": MATCH_CODE.get(r.get("matched", ""), 0), "seasons": {}}
            p["seasons"][season] = team_ix[tkey]
            if season >= max(p["seasons"]):          # the latest season names him and his position
                p["n"], p["p"] = r["name"], r.get("position", "") or p["p"]
            home = r.get("hometown", "")
            if home and not p["h"]:
                country = r.get("home_country", "")
                p["h"], p["s"] = home, r.get("home_state") or (country if country not in ("", "USA") else "")
                p["at"] = places.get((home, "")) or places.get((home, school))
            hs = r.get("high_school") or r.get("pro_high_school") or ""
            if hs and not p["hs"]:
                p["hs"] = hs
            if p["m"] == 0 and r.get("matched"):
                p["m"] = MATCH_CODE.get(r["matched"], 0)
    for lg in sorted(seasons_by_league, key=lambda x: list(LEAGUES).index(x.lower())):
        conf = LEAGUES[lg.lower()]
        leagues.append({"id": lg, "sport": conf["college_sport"], "seasons": sorted(seasons_by_league[lg])})
    rows = []
    for p in people.values():
        stints = []
        for season in sorted(p["seasons"]):
            t = p["seasons"][season]
            if stints and stints[-1][0] == t and stints[-1][2] in (season - 1, season - 2):
                stints[-1][2] = season
            else:
                stints.append([t, season, season])
        rows.append({**{k: v for k, v in p.items() if k != "seasons"}, "t": stints})
    rows.sort(key=lambda p: (p["g"], p["n"]))
    lg_ix = {x["id"]: i for i, x in enumerate(leagues)}
    cols = {k: [] for k in ("g", "n", "p", "c", "lv", "h", "s", "hs", "at", "m", "t")}
    for p in rows:
        for k in cols:
            cols[k].append(lg_ix[p["g"]] if k == "g" else p[k])
    data = {"leagues": leagues, "teams": teams, "schools": schools, "players": cols, "N": len(rows),
            "built": dt.date.today().isoformat()}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    by_lg = Counter(p["g"] for p in rows)
    print(f"{len(rows)} pro players with a college ({', '.join(f'{k} {v}' for k, v in by_lg.items())}); "
          f"{sum(1 for p in rows if p['at'])} with a hometown on the map; "
          f"{sum(1 for t in teams if t[4] is None)} teams with no place in {PRO_TEAMS.name}; "
          f"{sum(1 for s in schools if s[3] is None)} colleges with no campus -> {out_path}")
    return data


if __name__ == "__main__":
    sys.exit(main())
