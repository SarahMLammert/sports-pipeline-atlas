# Sports Pipeline Atlas

Where players come from, from high school to college to the pros, and where coaches move, sport by sport. (Called the
College Sports Atlas until Nov 22, 2026; the repository and the site's address are still `college-sports-atlas`.) Rosters and staff lists are scraped
from each school's athletics site, hometowns are placed on a map, and everything is published as a static
site in `docs/` (GitHub Pages).

| sport | folder | schools | players | seasons |
|---|---|---|---|---|
| Football | `football` | 831 (FBS, FCS, D2, D3, NAIA, JUCO) | 446K | 2016–2019, 2021–2026 (no 2020) |
| Baseball | `baseball` | 1,083 (D1, D2, D3, NAIA, JUCO) | 219K | 2016–2027 |
| Softball | `softball` | 1,118 (D1, D2, D3, NAIA, JUCO) | 115K | 2016–2027 |
| Lacrosse (Men's) | `lacrosse-mens` | 431 (D1, D2, D3, NAIA, JUCO) | 69K | 2016–2027 |
| Lacrosse (Women's) | `lacrosse-womens` | 583 (D1, D2, D3, NAIA, JUCO) | 58K | 2016–2027 |
| Hockey (Men's) | `hockey-mens` | 162 (NCAA D1, D2, D3) | 20K | 2016–2027 |
| Hockey (Women's) | `hockey-womens` | 126 (National Collegiate = D1 and D2 schools, D3) | 12K | 2016–2027 |
| Basketball (Men's) | `basketball-mens` | 1,216 (D1, D2, D3, NAIA, JUCO) | 120K | 2016–2027 |
| Basketball (Women's) | `basketball-womens` | 1,220 | 99K | 2016–2027 |
| Volleyball (Women's) | `volleyball-womens` | 1,192 | 98K | 2016–2026 (fall) |
| Volleyball (Men's) | `volleyball-mens` | 260 | 16K | 2016–2027 |
| Soccer (Men's) | `soccer-mens` | 950 | 152K | 2016–2026 (fall) |
| Soccer (Women's) | `soccer-womens` | 1,161 | 149K | 2016–2026 (fall) |
| Wrestling (Men's) | `wrestling-mens` | 321 | 44K | 2016–2027 |
| Wrestling (Women's) | `wrestling-womens` | 178 | 9K | 2016–2027 |
| Field Hockey | `field-hockey` | 276 (NCAA) | 26K | 2016–2026 (fall) |
| Water Polo (Men's) | `water-polo-mens` | 50 (NCAA) | 5K | 2016–2026 (fall) |
| Water Polo (Women's) | `water-polo-womens` | 59 (NCAA) | 5K | 2016–2026 |
| Rowing (Men's) | `rowing-mens` | 54 (NCAA) | 9K | 2016–2026 |
| Rowing (Women's) | `rowing-womens` | 137 (NCAA) | 25K | 2016–2026 |
| Tennis (Men's) | `tennis-mens` | 737 | 36K | 2016–2026 |
| Tennis (Women's) | `tennis-womens` | 880 | 38K | 2016–2026 |
| Golf (Men's) | `golf-mens` | 939 | 43K | 2016–2026 |
| Golf (Women's) | `golf-womens` | 844 | 27K | 2016–2026 |
| Cross Country (Men's) | `cross-country-mens` | 1,138 | 75K | 2016–2026 (fall) |
| Cross Country (Women's) | `cross-country-womens` | 1,188 | 75K | 2016–2026 (fall) |
| Track & Field (Men's) | `track-mens` | 959 (indoor and outdoor together) | 150K | 2016–2026 |
| Track & Field (Women's) | `track-womens` | 1,035 (indoor and outdoor together) | 141K | 2016–2026 |
| Swimming & Diving (Men's) | `swimming-mens` | 471 | 43K | 2016–2027 |
| Swimming & Diving (Women's) | `swimming-womens` | 571 | 55K | 2016–2027 |

Schools are the ones with players in the data. All 30 sports are built; a sport that is set up but not built yet
shows as "coming soon" on the front page.

The pros (NFL, NBA, MLB, NHL, 2016 on) are traced back to these college rosters on the Pro Pipeline page: about
12,000 players with a known college, 7,300 of them with a hometown (Nov 22). See "Pro rosters" below.

Football, volleyball and soccer are named by the fall they're played in. Spring and winter sports are named by the
spring the season ends in (2025-26 = 2026); from August the current season is next spring's. A sport appears on the
front page once it has been built. Every script turns seasons into labels and addresses (and a page's year back into a
season) with the same few functions in `scripts/core.py` (`season_span`, `season_from_label`, `fill_season`,
`current_season`); `docs/common.js` has the same rule for the site.

## The site

`docs/index.html` is the sport picker: one ring around the globe. Two three-part ring pickers choose what is on it:
**Maps** at the top right (high school, college, pro) and, for college maps, **Season** at the top left (fall,
winter, spring; it opens on the season being played). College maps put that season's sports on the ring (each sport's
season is `ring` in its settings); pro maps put the NFL, NBA, MLB and NHL there, each opening the Pro Pipeline;
high school maps are still to come. The address keeps the choice (`#season=winter`, `#level=pro`). The globe is NASA's Blue
Marble picture (`docs/img/earth.jpg`, 2048×1024, clouds included, from the three-globe package's example images)
wrapped onto a canvas; if it can't be read, world-atlas's 1:50m map is drawn instead. Behind it, the page is painted in thick oil-paint strokes that burst out from the
globe in the picked season's colors (fall golds, oranges and reds; winter white, ice blue and navy; spring yellows, pinks
and greens; violets for pro and high school maps; `PAINT` in index.html, the same every visit), light near the globe and
deeper at the edges, with a faint
latitude-longitude grid of a much bigger globe centred on the real one (`body[data-tone]`, `.sky`). Its list of sports comes from `docs/sports.js`, its numbers from each sport's
`summary.json`. There is one set of six
pages for every sport, opened with the sport in the address (`players-dotmap.html?sport=softball`):

- **Recruiting Map** (`players-dotmap.html`): a dot for every hometown, worldwide; filters for school,
  conference, division, seasons, transfers and positions; search for a school, player or town. Night lights (the moon
  button, on by default and remembered in the browser) darken the map and make each hometown glow in its school's
  color; crowded places add up like city lights.
- **Recruiting Footprints** (`players-heatmap.html`): up to four schools compared, state by state.
- **Transfer Map** (`players-transfers.html`): school-to-school moves.
- **Coaching Moves** (`staff-moves.html`): coaches moving between schools (head coach jobs, coaching jobs or any staff job).
- **Staff Directory** (`staff-directory.html`): a school's staff by season, its head coaches over time, and any
  person's career.
- **School Influence Map** (`school-influence.html`): pick a school and a season to see where everyone who had been
  there was that season, each person's career, and how the school ranks. Built in the browser from the player and
  staff data, so it needs no build step of its own.

The maps sit on a physical relief (`docs/basemap.js`): NASA's Blue Marble shaded relief and bathymetry, as web-map
tiles from FreeTiler (github.com/freetiler/nasa-bluemarble, MIT), recoloured in the browser like a physical atlas.
Zooms 0-6 are kept in the site, `docs/tiles/bluemarble` (5,461 tiles, re-saved smaller: about 30 MB), because jsDelivr
refuses that repository for being over its size limit (every tile came back 403). Rivers are drawn on top from `docs/rivers.json` (Natural Earth's 1:10m rivers and lake
centerlines, public domain, scalerank 0-8, simplified to 0.01°; smaller rivers appear as the Recruiting Map zooms in). The Recruiting Map draws the tiles as it zooms; the fixed maps (Transfer Map, Coaching Moves, School
Influence, Pro Pipeline) reproject them once per size. Footprints keeps its plain states, since it colours them by
numbers. If the tiles can't load, the maps keep their plain land.

One page covers every league: **Pro Pipeline** (`pro-pipeline.html`, linked from the globe and from the front page's
pro maps): NFL, NBA, MLB and NHL players since 2016 traced back to their college and high school, with a league
picker, a team picker, a season range, a search, and one player's path (hometown → college → teams). Teams are drawn
in their official colors (`config/shared/pro_teams.csv`). Its data is `docs/pro/pipeline.json` (`pro_rosters.py --build`).

The look: a modern, bright atlas. Colors are CSS variables at the top of `docs/common.css` (the map pages, with a
dark mode) and of `docs/index.html` (the deep-blue globe); headings use Plus Jakarta Sans, text Barlow.

Every page shares one strip of maps in its title bar (`MAPS` in `docs/common.js`, grouped into Players, Coaches and
Schools), and a map opens on the school the page is showing. A sport dropdown beside it keeps the same map and school.
Active filters show as chips with a ×. On the front page, clicking a sport lists all its maps in the globe, and Search by high school looks through `docs/high_schools.json` (written by `build.py pages`) and links to that school on each sport's Recruiting Map. `docs/sources.html` builds its list
of sports from `sports.js` and each `summary.json`, so it needs no hand editing. Inside a page, `GP.tabsHTML` makes a set of tabs; the open
tab is kept in the address (`tab=`). Styles and helpers used by more than one page belong in `docs/common.css` and
`docs/common.js`. Staff Directory shows its two tabs side by side on wide windows.

Football and baseball come in two files: the dot map opens on the D1 schools (`map_data.json`) and loads the
other divisions (`map_data_more.json`) only when a view or a search needs them. Map and staff data are packed
(`build.py`, `staff.py`) and unpacked by `docs/common.js`.

The pages show seasons as school years (2023-24); links and the data files keep the season number.

Every view is saved in the address after `#` (e.g. `players-dotmap.html?sport=football#school=Alabama&pos=QB`), so links
can be shared. Edit the pages in `docs/` directly. Each sport's own words on them (title, description, heading,
subtitle, and she/her for women's sports) and its place on the front page are in the `site` part of
`config/<sport>/settings.json`; `python3 scripts/build.py pages` copies them into `docs/sports.js` (don't edit that
file by hand; the pipeline's build step runs it). Its data is in `docs/<sport>/`. The old addresses
(`docs/football/players-dotmap.html`) are small pages that forward to the new one, also written by `build.py pages`
(`--check` only reports; a test fails if `sports.js` doesn't match the settings).

The site's icon is `docs/favicon.svg`, with `favicon-32.png` and `apple-touch-icon.png` for browsers that don't take
an SVG. A new page needs the same three `<link>` lines under its title.

**Publish:** GitHub → Settings → Pages → deploy from branch `main`, folder `/docs`. To look locally:
`cd docs && python3 -m http.server`, then http://localhost:8000.

## Running it

Setup once: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
(and `npm install` for the site's linter; it needs Node.js, `brew install node`)
(then `python3 -m playwright install chromium` once, for the browser retries and the page test).
requirements.txt includes pandas and pyarrow, which only `scripts/nba_history.py` (past NBA seasons) uses.

```
caffeinate -i python3 scripts/pipeline.py all              # every sport, every step
python3 scripts/pipeline.py softball hockey-mens           # some sports
python3 scripts/pipeline.py baseball --steps geocode,build # some steps
python3 scripts/pipeline.py football --from geocode        # start at a step
python3 scripts/pipeline.py softball --dry-run             # print the commands only
python3 -m pytest tests -q                                 # the tests (about 1 minute with the page test)
python3 -m ruff check scripts tests                         # the linter (rules in ruff.toml; --fix fixes the simple ones)
npm run lint                                               # the site's linter, ESLint (rules in eslint.config.js)
```

Steps, in order: `scrape` (quick pass) → `retry` (slow pass with a browser) → `redo-current` (only with
`--redo-current`) → `geocode` → `fix-hometowns` → `frozen` → `build` → `locations` → `staff` → `check`.
Useful options: `--rescrape` (every school again, not just what's missing), `--only "A,B"`, `--division D1`,
`--seasons 2024-2026`, `--retry-given-up`, `--keep-going`. A sport can't be run twice at once (a lock in `rosters/<sport>/`).

The terminal shows one line per school and short summaries; long lists of schools go to
`rosters/<sport>/notes_*.txt`. Each sport's full output is saved in `rosters/<sport>/pipeline.log`.

The steps one by one:

| command | does |
|---|---|
| `scrape_rosters.py --sport X` | download and read rosters (`--problems` only rewrites `MISSING_ROSTERS.md`) |
| `geocode.py --sport X` | place hometowns (`rosters/<sport>/hometowns.csv`, `unmatched_hometowns.csv`) |
| `hometown_fixes.py suggest --sport X [--accept-likely]` | suggest fixes for unplaced hometowns |
| `hometown_fixes.py spellings --sport X` | fix misspelled towns from the geocoder's table |
| `build.py frozen / map / locations / check / pages` | class-year check, map data, campus file, roster check, site pages |
| `build.py compare --sport X --school S --season Y` | a school's roster against its season before, player by player |
| `hometown_fixes.py review [--apply FILE]` | list automatic spelling fixes to check by hand, then apply your decisions |
| `staff.py scrape / build --sport X` | coaches from the roster pages, then the staff data |
| `core.py compress-cache` | compress the page cache |

## Folders

```
config/shared/         school_colors.csv, school_locations.csv, hometown_corrections.csv (every sport),
                       pro_teams.csv (each pro team's city, place on the map and two official colors)
config/<sport>/        settings.json        roster paths, roster size, positions, divisions, seasons
                       schools.csv          every college: division, conference, site, seasons, notes
                       hometown_corrections.csv   only where this sport needs a different fix from the shared one
                       wrong_seasons.csv, season_pages.csv   pages to skip or to use (optional)
rosters/<sport>/       working files, not committed: rosters_<season>.csv, scrape reports, MISSING_ROSTERS.md,
                       attempts.csv, hometowns.csv, staff_<season>.csv, notes and logs, and rosters.db (below)
docs/                  the site: index.html (the globe), the six map pages, pro-pipeline.html, sources.html,
                       common.js, common.css, basemap.js (the physical relief), tiles/bluemarble/ (its tiles) and
                       rivers.json, img/earth.jpg (the
                       globe's picture), pro/pipeline.json (the Pro Pipeline's data), and sports.js (written by
                       build.py pages from the settings);
                       docs/<sport>/ has map_data.json, names.txt, summary.json, school_locations.json,
                       staff_data.json and the old addresses' forwarding pages
scripts/               new_sports.py (the settings and schools files of the sports added Nov 2), core.py (paths,
                       downloads, season files, levels, and run_command: each file's sub-commands), sidearm.py (reading roster pages),
                       hometowns.py (reading hometown, class, height and weight fields), scrape_rosters.py,
                       scrape_reports.py (attempts.csv, the problem list, MISSING_ROSTERS.md), geocode.py (placing
                       hometowns), hometown_fixes.py, build.py, staff.py, pipeline.py, pro_rosters.py and
                       nba_history.py (below)
rosters/pro/           the pro rosters, not committed: <league>_<season>.csv and <league>_<season>_matched.csv
tests/                 test_atlas.py: the code (also checked with the linter, ruff), the parsers, the builds
                       roster_pages.zip + roster_pages_expected.json: nine real roster pages, one per kind of
                       site, and what the parser reads from each
                       test_pages.py: opens the site's pages in a headless browser and fails on any error
                       (needs `python3 -m playwright install chromium`; skipped without it)
                       sidearm_classic.html, sidearm_nextgen_table.html: two small hand-made pages
.cache/                downloaded pages (gzip) and town lists, not committed; it makes reruns fast. Plan: delete
                       it once every sport is added and checked (the next run would then download everything again)
```

## How it works

- **Schools.** `config/<sport>/schools.csv` lists every college the sport knows. Rows with a season range record
  moves between divisions, programs that started, stopped or closed ("none"), and colleges kept only so a
  transfer's old school gets a level ("level only"). A note starting "left out" means the site is never contacted.
- **Scraping.** For each school-season it tries the usual Sidearm/WMT/Presto addresses, then a browser.
  A page is rejected if it's another sport's, shows another season, is a main page still showing last
  season, or has an abnormal number of players for the sport. Schools whose site never works are skipped:
  a school-season that fails 3 runs in a row is given up (`attempts.csv`; `--retry-given-up` tries again).
  Each season has its own time limit (`--first-minutes`, 1, in the quick pass; `--season-minutes`, 3, in the retry);
  a season that reaches it keeps any roster it has, and the school's next season starts fresh. A site whose certificate
  is refused gets one try a season at that address before moving on to its `www.` addresses.
  Pages are cached, so reruns are fast; 404s are remembered for 60 days.
- **Men and women on one page.** Many track, cross country and swimming sites have one roster for both teams, and
  some have an empty or years-old men's page. With `roster_sex` in the settings, `sidearm.keep_own_sex` keeps this
  team's athletes, using the page's own marks (a person list with gender, player records, separate Men and Women
  tables, or a heading above each list). A page from a `combined_paths` address with no such marks is refused rather than guessed at.
  Checked Nov 13: wherever one page served both teams (1,873 track, 1,966 cross country, 715 swimming school-seasons),
  the split worked, except on two addresses missing from `combined_paths` (`track-field`, `swimming-diving`; added).
- **Stand-in pages.** For a season a sport has no roster, some Sidearm sites show a "General Roster" page listing
  another team. The scraper refuses it (`sidearm.stand_in_page`); the 202 saved before Nov 13 are listed in each
  sport's `wrong_seasons.csv`, so the next run drops them and tries those seasons again.
- **Jersey numbers.** Read with each player and tidied (`sidearm.clean_jersey`: "Number: 4" is 4; "RS", "INJ" or
  a year are not numbers). The map build puts a player's numbers at a school after his name in `names.txt`
  ("Ann Lee<tab>7, 12"), and the Recruiting Map shows them in player lists and careers.
- **Seasons a team doesn't have.** Seasons are scraped newest first. Once a team's roster page lists its seasons (a
  dropdown, links or its data), seasons older than the list are recorded as no team and not tried. A retry reads the
  list from the saved pages first, without downloading. It also skips seasons older than three seasons in a row with
  no roster (about 1 in 28 of those has a roster, so `--retry-given-up` or `--rescrape` tries them again). Eleven spring-named sports added Nov 2 stop at 2026 (`seasons` in their settings) until their 2027 rosters
  are posted.
- **Fixing a school.** See `rosters/<sport>/MISSING_ROSTERS.md`. Set `domain` or `roster_url` in `schools.csv`;
  list a season whose page is really another year in `wrong_seasons.csv`, or give the right page in `season_pages.csv`.
- **Hometowns.** Read from the roster text (US states, Canadian provinces, countries, hockey's three-letter
  codes like SWE/CZE), then placed with Census, USGS and GeoNames town lists. Plain "NL" is a Newfoundland town
  if one has that name, otherwise Dutch. Fixes go in `config/shared/hometown_corrections.csv`, shared by every
  sport (a sport's own file only holds the few places where it needs a different answer); `suggest --accept-likely`
  also takes clear misspellings and a wrong state only when the right one is a neighbour. Rows marked
  `manual` in `hometowns.csv` are never changed.
- **Transfers.** A player counts as a transfer if the roster names a college as his previous school, he was on
  another school's roster in this data first, or he arrives as a junior or older. Junior hockey teams ("(USHL)")
  are never colleges; for hockey only a known college counts. Old schools get a level (D1, D2, D3, NAIA,
  JUCO, club, unknown). Seasons whose class years never advance ("frozen") don't use the class-year rule.
- **The roster database.** `rosters/<sport>/rosters.db` (SQLite) holds the season files, scrape reports and hometown
  tables. The checks (`build.py check`, `frozen`) and the map build read it; it's rebuilt from the CSVs by itself
  whenever one of them changes, so the CSVs stay the files to edit. To look around: `sqlite3 rosters/softball/rosters.db`
  (tables `rosters`, `reports`, `hometowns`, `unmatched`).
- **Staff.** Coaches are read from the roster pages (or the coaches page). People are matched by name; a
  move is a person's last season at one school followed by their first at another within two seasons.
  Titles become roles (head, associate, assistant, coordinator, graduate, volunteer, support).

- **Pro rosters.** `scripts/pro_rosters.py` reads each league's rosters with every player's college, then finds him on
  that college's roster here (`matched` = by name, by last name and fitting first names, or by name and birthplace),
  so his hometown and high school come from the college data. It writes `rosters/pro/<league>_<season>.csv` and
  `<league>_<season>_matched.csv`; `--build` turns every matched file into the Pro Pipeline's data. Seasons are named by
  the year they start (NBA and NHL 2026 = 2026-27; MLB's 2027 is this winter's 40-man rosters).

  | league | this season | past seasons |
  |---|---|---|
  | NFL | nfl.com team pages | nflverse's roster files (GitHub) |
  | NBA | nba.com team pages | `scripts/nba_history.py`: hoopR's open ESPN data (GitHub; pandas and pyarrow) |
  | MLB | MLB's stats API, 40-man rosters with education | the stats API's full-season rosters |
  | NHL | the NHL's API, plus each player's career for his NCAA seasons | the NHL's API, each team's season roster, filled out from players' careers (those files are short from 2023-24 on and empty for Arizona 2023-24) |

  ```
  python3 scripts/pro_rosters.py all --refresh --build            # today's rosters, every league
  python3 scripts/pro_rosters.py nfl --season 2016-2026 --build
  python3 scripts/pro_rosters.py mlb --season 2016-2027 --build   # about 15 minutes
  python3 scripts/pro_rosters.py nhl --season 2016-2026 --build   # about 30-40 minutes (each player's career once)
  python3 scripts/nba_history.py                                  # past NBA seasons -> rosters/pro/nba_<season>.csv
  python3 scripts/pro_rosters.py nba --season 2016-2025 --match-only --build
  python3 scripts/pro_rosters.py --build                          # only rebuild the page's data
  ```

  `--match-only` redoes the matching from the saved roster files (after the college rosters change). The college
  rosters start in 2016, so players who were in college before that have a college but no hometown. A college needs a
  row in `config/shared/school_locations.csv` to get a square on the map; `--build` counts any without one. Left out: the
  WNBA (its site refuses automated visitors) and MLS (its club pages give no college).

## Adding a sport

1. Make `config/<sport>/` (name: sport, then sex if both, e.g. `basketball-womens`) with `settings.json`
   (copy one and change the roster paths, roster size, positions and divisions, and its `site` part: the words on
   the map pages and the front-page disc and ring; `core.Sport.site` explains each key) and `schools.csv`.
   `scripts/new_sports.py` writes both from the NCAA directory: add the sport to its list. A new disc also needs an
   icon in `SPORT_ICONS` in `docs/index.html`.
2. Add any new schools' colors and campuses to `config/shared/`.
3. Run `python3 scripts/build.py pages` (the sport appears on the front page as coming soon), then
   `python3 scripts/pipeline.py <sport>`. Its build step writes `docs/sports.js`, so the sport goes live on the
   front page and its map pages with nothing typed into `docs/`.

## Known issues

- Junior colleges with no known roster site are listed but not scraped; NJCAA's own stats pages could fill them.
- Coaches are matched by name only, so two people with the same name can be mixed up.
- `rosters/` was committed until Oct 28, so the git history is large (about 580 MB) until it's rewritten without it.
