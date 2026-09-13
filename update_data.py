import json, time, re, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

USER_ID = 4536361318
UNIVERSE_ID = 2440500124
PROGRESSION = [
"Welcome","Group Member","Buddy System","Back From The Dead","In Plain Sight","One Of Many","A Bone To Pick","Picking Flowers","Rebirth","Interconnected","Lost In Translation","Herb Of Viridis","Expert Technician","Improvise","Whoever Smelt It","Trespassing","Running Track","Down The Drain","Unpatched Dupe Glitch","Paperclip Challenge","Rage Room","Fried Mushrooms","Quick Purchase","Out Of My Way","You Can Run","I See You","Wrong Room","Look At Me","Eviction Notice","Dead Of Night","Rebound","Two Steps Forward","Playtime","I Don't Believe My Eyes","Just A Prank","Helping Hand","Trickshot","Trade Offer","Sshh!","Supporting Small Businesses","Pls Donate","Most Valuable Employee","Witness Protection","Limitless Paper","Hello Walker","Firewall","Crowd Watching","Perfect Memory","Carpet Burn","It's Still You","Smashing Deal","Fih Are Friends","Bubble Popping","Paparazzi","Now Served","Shock Hazard","Enlightened","Girl Dinner","Pizza Time","Gold Standard","Bad Luck","Rock Bottom","Detour","Around Back","Other Way Around","See You Soon","Touched Grass","Down The Water Spout","Forgotten Memories","Emergency Exit","Z-50","Going Down","Going Up","Evil Be Gone","Stay Out Of My Way","Unbound","Take A Breather","All Figured Out","Annihilation","Not Five Stars","Hotel Hell","Rocky Road","A Hard Place","Star Employee","MACHINE LEARNING","CLEAN RUN","PARALLEL PROCESSING","LOW LATENCY","UPTIME"]
NAME_ALIASES={"Down The Water Spout":["Down The Water Sprout"],"CLEAN RUN":["CLEAR RUN"]}
DESCRIPTION_ALIASES={"Improvise":"I... guess that works.","Playtime":"Let's play!","Trade Offer":"Do you accept?","Rock Bottom":"This is just the beginning.","Rocky Road":"I think I'm good with vanilla.","A Hard Place":"And a rock!"}

def norm(s):
    s=(s or "").lower().replace("’","'").replace("‘","'")
    return re.sub(r"[^a-z0-9]+"," ",s).strip()

def request_json(url, attempts=5):
    last=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"doors-star-checker/1.1"})
            with urllib.request.urlopen(req,timeout=30) as r:
                raw=r.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            last=e
            if e.code not in (429,500,502,503,504): raise
            time.sleep(min(2**i,15))
        except Exception as e:
            last=e; time.sleep(min(2**i,15))
    raise last

def paged_universe():
    out=[]; cursor=None
    while True:
        url=f"https://badges.roblox.com/v1/universes/{UNIVERSE_ID}/badges?limit=100&sortOrder=Asc"
        if cursor: url += "&cursor="+urllib.parse.quote(cursor,safe="")
        j=request_json(url); out.extend(j.get("data",[])); cursor=j.get("nextPageCursor")
        if not cursor:return out
        time.sleep(.25)

def ownership(badge_id):
    paths=[
        f"https://inventory.roblox.com/v1/users/{USER_ID}/items/Badge/{badge_id}/is-owned",
        f"https://inventory.roproxy.com/v1/users/{USER_ID}/items/Badge/{badge_id}/is-owned"
    ]
    errors=[]
    for url in paths:
        for attempt in range(3):
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"doors-star-checker/1.1"})
                with urllib.request.urlopen(req,timeout=20) as r:
                    raw=r.read().decode("utf-8").strip()
                    val=json.loads(raw)
                    if isinstance(val,bool): return val
                    if isinstance(val,dict):
                        if "isOwned" in val:return bool(val["isOwned"])
                        if "data" in val:return bool(val["data"])
                    raise RuntimeError("Unexpected ownership response: "+raw[:120])
            except urllib.error.HTTPError as e:
                errors.append(f"{url} -> HTTP {e.code}")
                if e.code==429: time.sleep(3+attempt*3); continue
                break
            except Exception as e:
                errors.append(f"{url} -> {e}"); time.sleep(2)
        time.sleep(.25)
    raise RuntimeError("; ".join(errors[-6:]))

def main():
    universe=paged_universe()
    by_name={};by_desc={}
    for b in universe:
        by_name.setdefault(norm(b.get("name")),[]).append(b)
        by_desc.setdefault(norm(b.get("description")),[]).append(b)
    mapped=[];unmatched=[]
    for target in PROGRESSION:
        candidates=[]
        for n in [target]+NAME_ALIASES.get(target,[]): candidates += by_name.get(norm(n),[])
        if not candidates and target in DESCRIPTION_ALIASES: candidates += by_desc.get(norm(DESCRIPTION_ALIASES[target]),[])
        uniq={str(b.get("id")):b for b in candidates}
        candidates=list(uniq.values()); candidates.sort(key=lambda b:(not bool(b.get("enabled")),str(b.get("created",""))))
        if candidates:
            b=candidates[0]; mapped.append({"name":target,"robloxName":b.get("name"),"id":b.get("id"),"description":b.get("description","")})
        else: unmatched.append(target)
    print(f"Mapped {len(mapped)}/{len(PROGRESSION)} progression badges; checking ownership...")
    for i,x in enumerate(mapped,1):
        x["owned"]=ownership(x["id"])
        if i%10==0 or i==len(mapped): print(f"Checked {i}/{len(mapped)}")
        time.sleep(1.1)
    owned=[x for x in mapped if x["owned"]]; missing=[x for x in mapped if not x["owned"]]
    data={"user":{"id":USER_ID,"name":"ItsIsaiah000"},"universeId":UNIVERSE_ID,"target":len(PROGRESSION),"mapped":len(mapped),"ownedCount":len(owned),"missingCount":len(missing)+len(unmatched),"owned":owned,"missing":missing,"unmatched":unmatched,"catalogBadgeCount":len(universe),"checksPerformed":len(mapped),"updatedAt":datetime.now(timezone.utc).isoformat()}
    with open("data.json","w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:data[k] for k in ["target","mapped","ownedCount","missingCount","unmatched","catalogBadgeCount"]},indent=2))

if __name__=="__main__":main()
