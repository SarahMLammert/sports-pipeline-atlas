"""Past NBA seasons for the Pro Pipeline, from hoopR's open NBA data (ESPN rosters and box scores, on GitHub).

    python3 scripts/nba_history.py                       # 2016-2025 -> rosters/pro/nba_<season>.csv
    python3 scripts/nba_history.py --seasons 2019-2025
    python3 scripts/pro_rosters.py nba --season 2016-2025 --match-only --build    # then match and rebuild the page

nba.com shows only today's rosters, so the current season still comes from `pro_rosters.py nba`. This script reads,
for each season, hoopR's player file (every player that season, with ESPN's college id, draft year and birthplace)
and its game rosters (which team each player was listed for, game by game), from
https://github.com/sportsdataverse/hoopR-nba-data. It needs pandas and pyarrow (both in requirements.txt).

Seasons are named by the year they start, like the rest of the pro rosters: 2018 = 2018-19 (hoopR's 2019).

ESPN gives a college only as a number. It becomes a school by looking at today's NBA players
(rosters/pro/nba_<current>_matched.csv, from nba.com, which names the school): each ESPN college id takes the school
most of its current players went to. About 9 in 10 players drafted since 2016 get a college this way; the rest have
none, so they aren't on the page.
"""
from __future__ import annotations

import argparse
import io
import sys
import urllib.request
from collections import Counter, defaultdict

from core import CACHE, check_packages, name_key, read_csv, write_csv
from pro_rosters import PRO_DIR, ROSTER_FIELDS, season_now

DATA = "https://raw.githubusercontent.com/sportsdataverse/hoopR-nba-data/main/nba/{kind}/parquet/{kind}_{year}.parquet"
# ESPN's team codes -> the team names the NBA rosters use (nba.com's, as in config/shared/pro_teams.csv). All-Star and
# exhibition teams (EAST, Team LeBron, ...) aren't here and are skipped.
TEAMS = {"ATL": "Hawks", "BOS": "Celtics", "BKN": "Nets", "CHA": "Hornets", "CHI": "Bulls", "CLE": "Cavaliers",
         "DAL": "Mavericks", "DEN": "Nuggets", "DET": "Pistons", "GS": "Warriors", "HOU": "Rockets", "IND": "Pacers",
         "LAC": "Clippers", "LAL": "Lakers", "MEM": "Grizzlies", "MIA": "Heat", "MIL": "Bucks", "MIN": "Timberwolves",
         "NO": "Pelicans", "NY": "Knicks", "OKC": "Thunder", "ORL": "Magic", "PHI": "Sixers", "PHX": "Suns",
         "POR": "Blazers", "SA": "Spurs", "SAC": "Kings", "TOR": "Raptors", "UTAH": "Jazz", "WSH": "Wizards"}


def parquet(kind: str, year: int, local: str | None = None):
    """One of hoopR's yearly files as a pandas table (cached in .cache/html, since past seasons don't change)."""
    import pandas as pd
    if local:
        return pd.read_parquet(f"{local}/nba/{kind}/parquet/{kind}_{year}.parquet")
    path = CACHE / f"hoopr_{kind}_{year}.parquet"
    if not path.exists():
        with urllib.request.urlopen(DATA.format(kind=kind, year=year), timeout=60) as r:
            path.write_bytes(r.read())
    return pd.read_parquet(io.BytesIO(path.read_bytes()))


def college_schools(people, current_matched: list[dict]) -> dict[int, str]:
    """ESPN college id -> school, by the schools today's players with that id went to (most of them wins)."""
    by_name = {name_key(r["name"]): r["college_school"] for r in current_matched if r.get("college_school")}
    votes: dict[int, Counter] = defaultdict(Counter)
    for name, college in zip(people["full_name"], people["college_id"], strict=True):
        school = by_name.get(name_key(name))
        if school and college == college:          # college is NaN when ESPN has none
            votes[int(college)][school] += 1
    return {c: v.most_common(1)[0][0] for c, v in votes.items()}


def season_rows(season: int, core, games, colleges: dict[int, str]) -> list[dict]:
    """The players of one season (ours: by its start year), one row per team he was listed for, in order."""
    games = games[games["team_abbreviation"].isin(TEAMS) & games["athlete_id"].notna()].sort_values("game_id")
    teams: dict[int, list[str]] = defaultdict(list)
    for aid, abbr in zip(games["athlete_id"], games["team_abbreviation"], strict=True):
        if TEAMS[abbr] not in teams[int(aid)]:
            teams[int(aid)].append(TEAMS[abbr])
    rows = []
    for p in core.to_dict("records"):
        aid = int(p["athlete_id"])
        if aid not in teams:
            continue
        cid = p.get("college_id")
        college = colleges.get(int(cid), "") if cid is not None and cid == cid else ""      # NaN: no college
        draft = int(p["draft_year"]) if p.get("draft_year") == p.get("draft_year") and p.get("draft_year") else ""
        country = p.get("birth_country") if isinstance(p.get("birth_country"), str) else ""
        for team in teams[aid]:
            rows.append({"league": "NBA", "season": season, "team": team, "name": p["full_name"],
                         "number": p.get("jersey") or "", "position": p.get("position_abbreviation") or "",
                         "status": "", "height": p.get("display_height") or "", "weight": p.get("display_weight") or "",
                         "experience": "", "college": college or "",
                         # drafted in June: his last college season is the spring of his draft year
                         "college_until": draft if college else "",
                         "birth_city": p.get("birth_city") if isinstance(p.get("birth_city"), str) else "",
                         "birth_state": p.get("birth_state") if isinstance(p.get("birth_state"), str) else "",
                         "birth_country": country, "pro_high_school": "",
                         "profile_url": f"https://www.espn.com/nba/player/_/id/{aid}", "player_id": f"espn:{aid}",
                         "other_name": ""})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seasons", default=f"2016-{season_now(league='nba') - 1}", help="a range of start years")
    ap.add_argument("--local", help="a local copy of hoopR-nba-data instead of downloading")
    args = ap.parse_args(argv)
    check_packages(["pandas", "pyarrow"], "Past NBA seasons (nba_history.py)")
    a, _, b = args.seasons.partition("-")
    seasons = list(range(int(a), int(b or a) + 1))
    current = read_csv(PRO_DIR / f"nba_{season_now(league='nba')}_matched.csv")
    if not current:
        print("Run `python3 scripts/pro_rosters.py nba` first: today's players are how ESPN's college ids get their schools.")
        return 1
    cores = {s: parquet("player_core", s + 1, args.local) for s in seasons}
    import pandas as pd
    people = pd.concat(list(cores.values())).drop_duplicates("athlete_id", keep="last")
    colleges = college_schools(people, current)
    print(f"{len(colleges)} ESPN college ids matched to schools")
    for s in seasons:
        rows = season_rows(s, cores[s], parquet("game_rosters", s + 1, args.local), colleges)
        path = PRO_DIR / f"nba_{s}.csv"
        write_csv(path, ROSTER_FIELDS, rows)
        print(f"NBA {s}: {len({r['player_id'] for r in rows})} players, "
              f"{len({r['player_id'] for r in rows if r['college']})} with a college -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
