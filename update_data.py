import json, time, re, urllib.request, urllib.parse
from datetime import datetime, timezone

USER_ID = 4536361318
UNIVERSE_ID = 2440500124

PROGRESSION = [
"Welcome","Group Member","Buddy System","Back From The Dead","In Plain Sight","One Of Many",
"A Bone To Pick","Picking Flowers","Rebirth","Interconnected","Lost In Translation","Herb Of Viridis",
"Expert Technician","Improvise","Whoever Smelt It","Trespassing","Running Track","Down The Drain",
"Unpatched Dupe Glitch","Paperclip Challenge","Rage Room","Fried Mushrooms","Quick Purchase",
"Out Of My Way","You Can Run","I See You","Wrong Room","Look At Me","Eviction Notice","Dead Of Night",
"Rebound","Two Steps Forward","Playtime","I Don't Believe My Eyes","Just A Prank","Helping Hand","Trickshot",
"Trade Offer","Sshh!","Supporting Small Businesses","Pls Donate","Most Valuable Employee","Witness Protection",
"Limitless Paper","Hello Walker","Firewall","Crowd Watching","Perfect Memory","Carpet Burn","It's Still You",
"Smashing Deal","Fih Are Friends","Bubble Popping","Paparazzi","Now Served","Shock Hazard","Enlightened",
"Girl Dinner","Pizza Time","Gold Standard","Bad Luck","Rock Bottom","Detour","Around Back","Other Way Around",
"See You Soon","Touched Grass","Down The Water Spout","Forgotten Memories","Emergency Exit","Z-50","Going Down",
"Going Up","Evil Be Gone","Stay Out Of My Way","Unbound","Take A Breather","All Figured Out","Annihilation",
"Not Five Stars","Hotel Hell","Rocky Road","A Hard Place","Star Employee","MACHINE LEARNING","CLEAN RUN",
"PARALLEL PROCESSING","LOW LATENCY","UPTIME"
]

NAME_ALIASES = {
    "Down The Water Spout": ["Down The Water Sprout"],
    "CLEAN RUN": ["CLEAR RUN"],
}

DESCRIPTION_ALIASES = {
    "Improvise": "I... guess that works.",
    "Playtime": "Let's play!",
    "Trade Offer": "Do you accept?",
    "Rock Bottom": "This is just the beginning.",
    "Rocky Road": "I think I'm good with vanilla.",
    "A Hard Place": "And a rock!",
}

def norm(s):
    s = (s or "").lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

def get_json(url, attempts=8):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"doors-star-checker/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            time.sleep(min(2 ** i, 30))
    raise last

def paged(base):
    out, cursor, page = [], None, 0
    while True:
        page += 1
        url = base + ("&" if "?" in base else "?") + "limit=100&sortOrder=Asc"
        if cursor:
            url += "&cursor=" + urllib.parse.quote(cursor, safe="")
        j = get_json(url)
        out.extend(j.get("data", []))
        cursor = j.get("nextPageCursor")
        if not cursor:
            return out
        time.sleep(0.7)

def main():
    universe = paged(f"https://badges.roblox.com/v1/universes/{UNIVERSE_ID}/badges?")
    user = paged(f"https://badges.roblox.com/v1/users/{USER_ID}/badges?")
    owned_ids = {str(x.get("id")) for x in user}

    by_name, by_desc = {}, {}
    for b in universe:
        by_name.setdefault(norm(b.get("name")), []).append(b)
        by_desc.setdefault(norm(b.get("description")), []).append(b)

    mapped, unmatched = [], []
    for target in PROGRESSION:
        candidates = []
        for name in [target] + NAME_ALIASES.get(target, []):
            candidates += by_name.get(norm(name), [])
        if not candidates and target in DESCRIPTION_ALIASES:
            candidates += by_desc.get(norm(DESCRIPTION_ALIASES[target]), [])
        seen = set()
        candidates = [b for b in candidates if not (str(b.get("id")) in seen or seen.add(str(b.get("id"))))]
        candidates.sort(key=lambda b: (not bool(b.get("enabled")), str(b.get("created", ""))), reverse=False)
        if candidates:
            b = candidates[0]
            mapped.append({
                "name": target,
                "robloxName": b.get("name"),
                "id": b.get("id"),
                "owned": str(b.get("id")) in owned_ids,
                "description": b.get("description", "")
            })
        else:
            unmatched.append(target)

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
        "userBadgeCountScanned": len(user),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(json.dumps({k:data[k] for k in ["target","mapped","ownedCount","missingCount","unmatched","catalogBadgeCount","userBadgeCountScanned"]}, indent=2))

if __name__ == "__main__":
    main()
