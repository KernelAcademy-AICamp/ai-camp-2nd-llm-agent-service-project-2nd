import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rules = json.loads((ROOT / "data" / "recommender_rules.v2_12.json").read_text(encoding="utf-8"))
precedents = json.loads((ROOT / "data" / "precedent_index.v2_12.json").read_text(encoding="utf-8"))["precedents"]

authorities = [
  {"authority_id":"CIVIL_840","authority_code":"CIVIL_840","title":"민법 제840조 (재판상 이혼원인)","tags":["CIVIL","G1","G2","G3","G4","G5","G6"]},
  {"authority_id":"CIVIL_834","authority_code":"CIVIL_834","title":"민법 제834조 (협의상 이혼)","tags":["CIVIL","CONSENSUAL"]},
  {"authority_id":"CIVIL_836_2","authority_code":"CIVIL_836_2","title":"민법 제836조의2 (숙려기간)","tags":["CIVIL","CONSENSUAL"]},
  {"authority_id":"FAMILY_LIT_50","authority_code":"FAMILY_LIT_50","title":"가사소송법 제50조 (조정전치주의)","tags":["FAMILY_LIT","JUDICIAL"]}
]

ctx = {
  "case_id": "CASE_DEMO",
  "divorce_type": "JUDICIAL",
  "ground_scores": {"G3": 95, "G6": 60},
  "keypoints": [
    {"kind":"POLICE_CASE","value":{"case_no":"112-XXXX"},"materiality":90,"ground_tags":["G3"]},
    {"kind":"MEDICAL","value":{"hospital":"OO병원"},"materiality":85,"ground_tags":["G3"]}
  ]
}

def derive_tags(ctx):
  derived_tags=[]
  kp_total=0
  kp_boosts = rules["signals"]["keypoints"]
  for kp in ctx["keypoints"]:
    r = kp_boosts.get(kp["kind"])
    if r:
      kp_total += r.get("boost",0)
      derived_tags += r.get("adds_tags",[])
  return list(dict.fromkeys(derived_tags)), kp_total

def top_grounds(ctx):
  return sorted(ctx["ground_scores"].items(), key=lambda x:x[1], reverse=True)[:2]

def score_item(item, base, d_tags, kp_total, tg, g_keywords, required, proc_boost):
  tags=item.get("tags",[])
  title=item.get("title","") or item.get("gist","")
  s=base + proc_boost + kp_total
  reasons=[]
  hits=set(tags).intersection(set(d_tags + [g for g,_ in tg]))
  if hits:
    s += 8*len(hits); reasons.append("tag:"+",".join(sorted(hits)))
  kw=[k for k in g_keywords if k in title]
  if kw:
    s += 5*len(kw); reasons.append("kw:"+",".join(kw[:3]))
  if item.get("authority_code") in required:
    s += 50; reasons.append("required")
  if kp_total:
    reasons.append(f"keypoints+{kp_total}")
  return s, reasons[:5]

if __name__ == "__main__":
  d_tags, kp_total = derive_tags(ctx)
  tg = top_grounds(ctx)
  ground_sig = rules["signals"]["grounds"]
  g_keywords=[]
  g_boost=0
  for g,_ in tg:
    g_keywords += ground_sig.get(g,{}).get("keywords",[])
    g_boost += ground_sig.get(g,{}).get("boost",0)
  g_keywords=list(dict.fromkeys(g_keywords))
  proc = rules["signals"]["process"][ctx["divorce_type"]]
  required=set(proc.get("required_authorities",[]))
  proc_boost=proc.get("boost",0)

  auth_rank=[]
  for a in authorities:
    s,r = score_item(a,50+g_boost,d_tags,kp_total,tg,g_keywords,required,proc_boost)
    auth_rank.append((s,a["title"],r))
  auth_rank.sort(reverse=True, key=lambda x:x[0])

  prec_rank=[]
  for p in precedents:
    p2=dict(p); p2["title"]=p.get("gist","")
    s,r = score_item(p2,40+g_boost,d_tags,kp_total,tg,g_keywords,required,proc_boost)
    prec_rank.append((s,p.get("gist",""),r))
  prec_rank.sort(reverse=True, key=lambda x:x[0])

  print("Authorities:")
  for s,t,r in auth_rank[:5]:
    print("-", int(s), t, r)
  print("\nPrecedents:")
  for s,t,r in prec_rank[:5]:
    print("-", int(s), t, r)
