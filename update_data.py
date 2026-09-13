import json, time, re, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

USER_ID = 4536361318
UNIVERSE_ID = 2440500124

PROGRESSION = [
"Welcome","Group Member","Buddy System","Back From The Dead","In Plain Sight","One Of Many","A Bone To Pick","Picking Flowers","Rebirth","Interconnected","Lost In Translation","Herb Of Viridis","Expert Technician","Improvise","Whoever Smelt It","Trespassing","Running Track","Down The Drain","Unpatched Dupe Glitch","Paperclip Challenge","Rage Room","Fried Mushrooms","Quick Purchase","Out Of My Way","You Can Run","I See You","Wrong Room","Look At Me","Eviction Notice","Dead Of Night","Rebound","Two Steps Forward","Playtime","I Don't Believe My Eyes","Just A Prank","Helping Hand","Trickshot","Trade Offer","Sshh!","Supporting Small Businesses","Pls Donate","Most Valuable Employee","Witness Protection","Limitless Paper","Hello Walker","Firewall","Crowd Watching","Perfect Memory","Carpet Burn","It's Still You","Smashing Deal","Fih Are Friends","Bubble Popping","Paparazzi","Now Served","Shock Hazard","Enlightened","Girl Dinner","Pizza Time","Gold Standard","Bad Luck","Rock Bottom","Detour","Around Back","Other Way Around","See You Soon","Touched Grass","Down The Water Spout","Forgotten Memories","Emergency Exit","Z-50","Going Down","Going Up","Evil Be Gone","Stay Out Of My Way","Unbound","Take A Breather","All Figured Out","Annihilation","Not Five Stars","Hotel Hell","Rocky Road","A Hard Place","Star Employee","MACHINE LEARNING","CLEAN RUN","PARALLEL PROCESSING","LOW LATENCY","UPTIME"]

# Exact IDs from the official DOORS Wiki's Roblox badge links.
EXACT_IDS = {
    "Improvise": 96598251144845,
    "Playtime": 3997925777959907,
    "Trade Offer": 504590930650992,
    "Rock Bottom": 2133603375,  # Rock Bottom (After HOTEL+)
    "Rocky Road": 1852452263373089,
    "A Hard Place": 820874253830339,
}

NAME_ALIASES = {
    "Down The Water Spout": ["Down The Water Sprout"],
    "CLEAN RUN": ["CLEAR RUN"],
}

def norm(s):
    s = (s or "").lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

def request_json(url, attempts=5):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"doors-star-checker/1.3"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (429,500,502,503,504):
                raise
            time.sleep(min(2**i, 15))
        except Exception as e:
            last = e
            time.sleep(min(2**i, 15))
    raise last

def paged_universe():
    out = []
    cursor = None
    while True:
        url = f"https://badges.roblox.com/v1/universes/{UNIVERSE_ID}/badges?limit=100&sortOrder=Asc"
        if cursor:
            url += "&cursor=" + urllib.parse.quote(cursor, safe="")
        j = request_json(url)
        out.extend(j.get("data", []))
        cursor = j.get("nextPageCursor")
        if not cursor:
            return out
        time.sleep(.2)

def ownership(badge_id):
    urls = [
        f"https://inventory.roblox.com/v1/users/{USER_ID}/items/Badge/{badge_id}/is-owned",
        f"https://inventory.roproxy.com/v1/users/{USER_ID}/items/Badge/{badge_id}/is-owned",
    ]
    errors = []
    for url in urls:
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent":"doors-star-checker/1.3"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    raw = r.read().decode("utf-8").strip()
                    val = json.loads(raw)
                    if isinstance(val, bool):
                        return val
                    if isinstance(val, dict):
                        if "isOwned" in val:
                            return bool(val["isOwned"])
                        if "data" in val:
                            return bool(val["data"])
                    raise RuntimeError("Unexpected ownership response: " + raw[:120])
            except urllib.error.HTTPError as e:
                errors.append(f"{url} -> HTTP {e.code}")
                if e.code == 429:
                    time.sleep(2 + attempt * 2)
                    continue
                break
            except Exception as e:
                errors.append(f"{url} -> {e}")
                time.sleep(1)
        time.sleep(.1)
    raise RuntimeError("; ".join(errors[-6:]))

def main():
    universe = paged_universe()
    by_name = {}
    by_id = {str(b.get("id")): b for b in universe}

    for b in universe:
        by_name.setdefault(norm(b.get("name")), []).append(b)

    mapped = []
    unmatched = []

    for target in PROGRESSION:
        # Hidden/currently masked Roblox badges are pinned to the exact IDs from
        # the official DOORS Wiki links instead of guessed from the "???" name.
        if target in EXACT_IDS:
            badge_id = EXACT_IDS[target]
            b = by_id.get(str(badge_id), {})
            mapped.append({
                "name": target,
                "robloxName": b.get("name") or target,
                "id": badge_id,
                "description": b.get("description", ""),
                "idSource": "official DOORS Wiki Roblox link",
            })
            continue

        candidates = []
        for n in [target] + NAME_ALIASES.get(target, []):
            candidates += by_name.get(norm(n), [])

        uniq = {str(b.get("id")): b for b in candidates}
        candidates = list(uniq.values())
        candidates.sort(key=lambda b: (not bool(b.get("enabled")), str(b.get("created", ""))))

        if candidates:
            b = candidates[0]
            mapped.append({
                "name": target,
                "robloxName": b.get("name"),
                "id": b.get("id"),
                "description": b.get("description", ""),
                "idSource": "Roblox DOORS universe catalog exact-name match",
            })
        else:
            unmatched.append(target)

    print(f"Mapped {len(mapped)}/{len(PROGRESSION)} progression badges; checking ownership...")

    for i, x in enumerate(mapped, 1):
        x["owned"] = ownership(x["id"])
        if i % 10 == 0 or i == len(mapped):
            print(f"Checked {i}/{len(mapped)}")
        time.sleep(.2)

    owned = [x for x in mapped if x["owned"]]
    missing = [x for x in mapped if not x["owned"]]
    data = {
        "user": {"id": USER_ID, "name": "ItsIsaiah000"},
        "universeId": UNIVERSE_ID,
        "target": len(PROGRESSION),
        "mapped": len(mapped),
        "ownedCount": len(owned),
        "missingCount": len(missing) + len(unmatched),
        "owned": owned,
        "missing": missing,
        "unmatched": unmatched,
        "catalogBadgeCount": len(universe),
        "checksPerformed": len(mapped),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(json.dumps({k:data[k] for k in ["target","mapped","ownedCount","missingCount","unmatched","catalogBadgeCount"]}, indent=2))

if __name__ == "__main__":
    main()
