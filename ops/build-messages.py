#!/usr/bin/env python3
"""Build the message knowledge base from ops/messages.json.

One data file, two views: ops/MESSAGES.md (grep it on the host at 3am) and
ops/messages.html (a searchable page -- paste a message, read its meaning and
fix). Edit messages.json, re-run this, commit both outputs.

    ./ops/build-messages.py

No dependencies beyond the standard library.
"""
from __future__ import annotations

import html
import json
import pathlib
import re
from collections import Counter
from datetime import date

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "messages.json"

LAYERS = [
    ("laptop", "Your laptop"),
    ("host-scripts", "Host scripts"),
    ("app", "The app — boot & runtime"),
    ("substrate", "Substrate CLI"),
    ("container-db", "Containers & database"),
    ("external", "External tools — git, uv, podman, nginx"),
]
LAYER_LABEL = dict(LAYERS)
SEV_ORDER = ["critical", "action", "warning", "info"]
SEV_LABEL = {"critical": "Critical", "action": "Needs action", "warning": "Warning", "info": "Info"}
WHERE_LABEL = {"laptop": "laptop", "host": "host", "both": "either"}


def load() -> list[dict]:
    entries = json.loads(DATA.read_text())
    order = {k: i for i, (k, _) in enumerate(LAYERS)}
    sev = {s: i for i, s in enumerate(SEV_ORDER)}
    entries.sort(key=lambda e: (order.get(e["layer"], 99), sev.get(e["sev"], 99), e["id"]))
    return entries


def code_span(text: str) -> str:
    """Wrap `text` in a markdown code span long enough to contain it.

    A fixed pair of backticks is wrong whenever the text holds one of its own:
    the span closes at the inner backtick and the remainder renders as prose,
    which it did for nine entries -- every message whose `match` quoted a
    command. CommonMark's answer is that a span may be fenced by any backtick
    run longer than the longest run inside it, so the fence is measured rather
    than assumed. The space padding is the same specification's rule for text
    that itself begins or ends with a backtick, and is stripped on render.
    """
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * (longest + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def build_md(entries: list[dict]) -> str:
    counts = Counter(e["sev"] for e in entries)
    out: list[str] = []
    out.append("# The 3am Almanac — a podpack message knowledge base\n")
    out.append(
        "> **Generated from [`messages.json`](messages.json) by "
        "[`build-messages.py`](build-messages.py). Edit the JSON, not this file.**\n"
    )
    out.append(
        f"Every message this system is likely to put in front of you — {len(entries)} of them — "
        "with where it comes from, how serious it is, and what to do. "
        "At 3am: search this file for the fixed part of the message you're staring at "
        "(`<angle-brackets>` mark the variable bits). The browsable, filterable version is "
        "[`messages.html`](messages.html).\n"
    )
    out.append("**Severity** — "
               f"🔴 critical ({counts['critical']}) an outage, or data/secrets at risk · "
               f"🟠 needs action ({counts['action']}) a step failed or a decision is needed · "
               f"🟡 warning ({counts['warning']}) worth a look · "
               f"🔵 info ({counts['info']}) normal, listed so you can confirm it's benign.\n")
    out.append("**Where** — *laptop* (your machine, dev & deploy) · *host* (the Opalstack "
               "deploy host) · *either*.\n")
    dot = {"critical": "🔴", "action": "🟠", "warning": "🟡", "info": "🔵"}
    for key, label in LAYERS:
        group = [e for e in entries if e["layer"] == key]
        if not group:
            continue
        out.append(f"\n## {label}\n")
        for e in group:
            out.append(f"### {dot[e['sev']]} {e['id']}")
            out.append(f"{code_span(e['match'])}\n")
            out.append(f"- **{SEV_LABEL[e['sev']]}** · **where:** {WHERE_LABEL[e['where']]} "
                       f"· **from:** `{e['source']}`")
            out.append(f"- **Means:** {e['means']}")
            out.append(f"- **Do:** {e['do']}\n")
    return "\n".join(out) + "\n"


TEMPLATE = r"""<title>The 3am Almanac</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<style>
:root{
  --bg:#eef1f4; --surface:#ffffff; --surface-2:#f6f8fb; --ink:#172029; --muted:#5c6672;
  --line:#dde3ea; --line-strong:#c8d1db; --accent:#0d6e78; --accent-ink:#0a565e;
  --crit:#bb2f36; --crit-bg:#fbe9ea; --act:#a55600; --act-bg:#fbeede;
  --warn:#7e6400; --warn-bg:#f6efcf; --info:#37589a; --info-bg:#e9eef8;
  --shadow:0 1px 2px rgba(23,32,41,.06),0 6px 20px rgba(23,32,41,.06);
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --bg:#0c1015; --surface:#141a22; --surface-2:#1a212b; --ink:#e6ebf2; --muted:#8b97a6;
  --line:#242e39; --line-strong:#33404d; --accent:#2bb3c0; --accent-ink:#79dbe4;
  --crit:#ff6b71; --crit-bg:#2b1517; --act:#f2ac52; --act-bg:#2a1f0f;
  --warn:#e0c94c; --warn-bg:#241f0d; --info:#8aa9ea; --info-bg:#151d2c;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 26px rgba(0,0,0,.36);
}}
:root[data-theme="dark"]{
  --bg:#0c1015; --surface:#141a22; --surface-2:#1a212b; --ink:#e6ebf2; --muted:#8b97a6;
  --line:#242e39; --line-strong:#33404d; --accent:#2bb3c0; --accent-ink:#79dbe4;
  --crit:#ff6b71; --crit-bg:#2b1517; --act:#f2ac52; --act-bg:#2a1f0f;
  --warn:#e0c94c; --warn-bg:#241f0d; --info:#8aa9ea; --info-bg:#151d2c;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 26px rgba(0,0,0,.36);
}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,sans-serif;
  line-height:1.5;-webkit-font-smoothing:antialiased;}
.wrap{max-width:900px;margin:0 auto;padding:28px 20px 80px;}
.mono{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;}
a{color:var(--accent-ink);}

header{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:4px;}
h1{font-size:clamp(1.7rem,4vw,2.3rem);font-weight:700;letter-spacing:-.02em;margin:0;text-wrap:balance;}
h1 .clock{color:var(--accent);font-variant-numeric:tabular-nums;}
.lede{color:var(--muted);max-width:62ch;margin:.5rem 0 0;}
.lede b{color:var(--ink);font-weight:600;}
.themebtn{flex:none;border:1px solid var(--line-strong);background:var(--surface);color:var(--muted);
  border-radius:9px;width:38px;height:38px;font-size:1rem;cursor:pointer;display:grid;place-items:center;}
.themebtn:hover{color:var(--ink);border-color:var(--accent);}

.tools{position:sticky;top:0;z-index:5;background:var(--bg);
  padding:16px 0 12px;margin:18px 0 6px;border-bottom:1px solid var(--line);}
.searchrow{position:relative;}
#q{width:100%;font:500 1.02rem/1.4 "IBM Plex Mono",monospace;color:var(--ink);
  background:var(--surface);border:1.5px solid var(--line-strong);border-radius:11px;
  padding:14px 44px 14px 16px;box-shadow:var(--shadow);}
#q::placeholder{color:var(--muted);font-weight:400;}
#q:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 22%,transparent);}
.searchrow .slash{position:absolute;right:12px;top:50%;transform:translateY(-50%);
  border:1px solid var(--line-strong);border-radius:6px;padding:1px 7px;color:var(--muted);
  font:600 .78rem/1.4 "IBM Plex Mono",monospace;pointer-events:none;}
.filters{display:flex;flex-wrap:wrap;gap:7px;margin-top:12px;align-items:center;}
.chip{font:600 .8rem/1 "IBM Plex Sans",sans-serif;border:1px solid var(--line-strong);
  background:var(--surface);color:var(--muted);border-radius:999px;padding:7px 12px;cursor:pointer;
  display:inline-flex;gap:7px;align-items:center;white-space:nowrap;user-select:none;}
.chip:hover{color:var(--ink);}
.chip .n{font-variant-numeric:tabular-nums;opacity:.7;}
.chip[aria-pressed="true"]{color:var(--ink);border-color:currentColor;}
.chip.sev-critical[aria-pressed="true"]{color:var(--crit);background:var(--crit-bg);}
.chip.sev-action[aria-pressed="true"]{color:var(--act);background:var(--act-bg);}
.chip.sev-warning[aria-pressed="true"]{color:var(--warn);background:var(--warn-bg);}
.chip.sev-info[aria-pressed="true"]{color:var(--info);background:var(--info-bg);}
.chip.where[aria-pressed="true"]{color:var(--accent-ink);border-color:var(--accent);
  background:color-mix(in srgb,var(--accent) 12%,transparent);}
.dot{width:8px;height:8px;border-radius:50%;flex:none;}
.dot.critical{background:var(--crit);} .dot.action{background:var(--act);}
.dot.warning{background:var(--warn);} .dot.info{background:var(--info);}
.sep{width:1px;align-self:stretch;background:var(--line);margin:2px 4px;}
.count{color:var(--muted);font-size:.86rem;margin:14px 2px 2px;font-variant-numeric:tabular-nums;}

.group{margin-top:26px;}
.group > h2{font-size:.82rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
  color:var(--muted);margin:0 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line);}
.cards{display:flex;flex-direction:column;gap:10px;}
.card{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--sev);
  border-radius:12px;padding:14px 16px;box-shadow:var(--shadow);}
.card.critical{--sev:var(--crit);} .card.action{--sev:var(--act);}
.card.warning{--sev:var(--warn);} .card.info{--sev:var(--info);}
.badges{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin-bottom:9px;}
.badge{font:600 .72rem/1 "IBM Plex Sans",sans-serif;letter-spacing:.02em;
  border-radius:6px;padding:4px 8px;display:inline-flex;gap:5px;align-items:center;}
.badge.sev{background:var(--sev-bg);color:var(--sev-fg);}
.card.critical .badge.sev{--sev-bg:var(--crit-bg);--sev-fg:var(--crit);}
.card.action .badge.sev{--sev-bg:var(--act-bg);--sev-fg:var(--act);}
.card.warning .badge.sev{--sev-bg:var(--warn-bg);--sev-fg:var(--warn);}
.card.info .badge.sev{--sev-bg:var(--info-bg);--sev-fg:var(--info);}
.badge.where{color:var(--muted);border:1px solid var(--line-strong);}
.src{margin-left:auto;color:var(--muted);font:500 .78rem/1 "IBM Plex Mono",monospace;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:46%;}
.msg{font:500 .92rem/1.5 "IBM Plex Mono",monospace;color:var(--ink);background:var(--surface-2);
  border:1px solid var(--line);border-radius:8px;padding:9px 11px;overflow-x:auto;
  white-space:pre-wrap;word-break:break-word;}
.msg mark{background:color-mix(in srgb,var(--accent) 30%,transparent);color:inherit;border-radius:3px;padding:0 1px;}
.mn{margin:.6rem 0 0;font-size:.92rem;} .mn b{color:var(--muted);font-weight:600;}
.mn.do{margin-top:.35rem;} .mn.do b{color:var(--accent-ink);}
.empty{text-align:center;color:var(--muted);padding:50px 20px;}
.empty .mono{color:var(--ink);}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:.82rem;}
@media (max-width:560px){ .src{max-width:100%;margin:6px 0 0;} .badges{gap:6px;} }
@media (prefers-reduced-motion:no-preference){ .card,.chip,#q{transition:border-color .15s,background .15s,color .15s;} }
</style>

<div class="wrap">
  <header>
    <div>
      <h1>The&nbsp;<span class="clock">3am</span>&nbsp;Almanac</h1>
      <p class="lede">Every message this podpack site is likely to put in front of you, with
        <b>where it came from</b>, <b>how worried to be</b>, and <b>what to do</b>. Paste the
        message you're staring at, or type any part of it.</p>
    </div>
    <button class="themebtn" id="theme" title="Toggle light / dark" aria-label="Toggle theme">◐</button>
  </header>

  <div class="tools">
    <div class="searchrow">
      <input id="q" type="search" autocomplete="off" spellcheck="false"
             placeholder="Paste a message, or a phrase from it…" aria-label="Search messages">
      <span class="slash">/</span>
    </div>
    <div class="filters" id="sevfilters"></div>
    <div class="filters" id="wherefilters" style="margin-top:8px"></div>
  </div>
  <div class="count" id="count"></div>
  <div id="results"></div>

  <footer>
    <span id="meta"></span> · Grep the same catalogue on the host in
    <span class="mono">ops/MESSAGES.md</span>. Built from
    <span class="mono">ops/messages.json</span>.
  </footer>
</div>

<script>
const MESSAGES = __DATA__;
const META = __META__;
const LAYERS = __LAYERS__;
const SEV = ["critical","action","warning","info"];
const SEV_LABEL = {critical:"Critical", action:"Needs action", warning:"Warning", info:"Info"};
const WHERE_LABEL = {laptop:"laptop", host:"host", both:"either"};

const state = {q:"", sev:new Set(), where:new Set()};
const $ = s => document.querySelector(s);
const esc = s => s.replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

function terms(){ return state.q.toLowerCase().split(/\s+/).filter(Boolean); }
function haystack(m){ return (m.match+" "+m.means+" "+m.do+" "+m.source+" "+m.id).toLowerCase(); }
function matches(m){
  if(state.sev.size && !state.sev.has(m.sev)) return false;
  if(state.where.size && m.where!=="both" && !state.where.has(m.where)) return false;
  return terms().every(t => haystack(m).includes(t));
}
function highlight(text){
  const ts = terms(); let out = esc(text);
  for(const t of ts.sort((a,b)=>b.length-a.length)){
    if(t.length<2) continue;
    const re = new RegExp("("+t.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+")","ig");
    out = out.replace(re, "\x01$1\x02");
  }
  return out.replace(/\x01/g,"<mark>").replace(/\x02/g,"</mark>");
}

function card(m){
  return `<div class="card ${m.sev}">
    <div class="badges">
      <span class="badge sev"><span class="dot ${m.sev}"></span>${SEV_LABEL[m.sev]}</span>
      <span class="badge where">${WHERE_LABEL[m.where]}</span>
      <span class="src mono">${esc(m.source)}</span>
    </div>
    <div class="msg mono">${highlight(m.match)}</div>
    <p class="mn"><b>Means&nbsp;</b>${esc(m.means)}</p>
    <p class="mn do"><b>Do&nbsp;</b>${esc(m.do)}</p>
  </div>`;
}

function render(){
  const shown = MESSAGES.filter(matches);
  const res = $("#results"); res.innerHTML = "";
  $("#count").textContent = shown.length===MESSAGES.length
    ? `${MESSAGES.length} messages`
    : `${shown.length} of ${MESSAGES.length} messages`;
  if(!shown.length){
    res.innerHTML = `<div class="empty">No message matches <span class="mono">${esc(state.q)||"that"}</span>.<br>Try fewer words, or the fixed part of the line.</div>`;
    return;
  }
  for(const [key,label] of LAYERS){
    const group = shown.filter(m => m.layer===key);
    if(!group.length) continue;
    const g = document.createElement("section"); g.className="group";
    g.innerHTML = `<h2>${label} · ${group.length}</h2><div class="cards">${group.map(card).join("")}</div>`;
    res.appendChild(g);
  }
}

function chip(cls, label, n, on){
  const b = document.createElement("button");
  b.className = "chip "+cls; b.setAttribute("aria-pressed","false");
  b.innerHTML = label + (n!=null?` <span class="n">${n}</span>`:"");
  b.addEventListener("click", ()=>{ on(b.getAttribute("aria-pressed")!=="true"); b.setAttribute("aria-pressed", b.getAttribute("aria-pressed")!=="true"); render(); });
  return b;
}
function buildFilters(){
  const sf = $("#sevfilters");
  for(const s of SEV){
    const n = MESSAGES.filter(m=>m.sev===s).length;
    sf.appendChild(chip("sev-"+s, `<span class="dot ${s}"></span>${SEV_LABEL[s]}`, n, on=>{ on?state.sev.add(s):state.sev.delete(s); }));
  }
  const wf = $("#wherefilters");
  for(const w of ["laptop","host"]){
    const n = MESSAGES.filter(m=>m.where===w||m.where==="both").length;
    wf.appendChild(chip("where", `on the ${w}`, n, on=>{ on?state.where.add(w):state.where.delete(w); }));
  }
}

// theme toggle, persisted per viewer (fails silent in private windows)
const themeBtn = $("#theme");
themeBtn.addEventListener("click", ()=>{
  const cur = document.documentElement.getAttribute("data-theme");
  const sysDark = matchMedia("(prefers-color-scheme:dark)").matches;
  const next = cur ? (cur==="dark"?"light":"dark") : (sysDark?"light":"dark");
  document.documentElement.setAttribute("data-theme", next);
  try{ localStorage.setItem("almanac-theme", next); }catch(e){}
});
try{ const t=localStorage.getItem("almanac-theme"); if(t) document.documentElement.setAttribute("data-theme", t); }catch(e){}

const q = $("#q");
q.addEventListener("input", ()=>{ state.q=q.value; render(); });
addEventListener("keydown", e=>{
  if(e.key==="/" && document.activeElement!==q){ e.preventDefault(); q.focus(); }
  else if(e.key==="Escape" && document.activeElement===q){ q.value=""; state.q=""; render(); }
});
$("#meta").textContent = META.count + " messages · updated " + META.updated;
buildFilters(); render(); q.focus({preventScroll:true});
</script>
"""


def build_html(entries: list[dict]) -> str:
    meta = {"count": len(entries), "updated": date.today().isoformat()}
    return (TEMPLATE
            .replace("__DATA__", json.dumps(entries, ensure_ascii=False))
            .replace("__META__", json.dumps(meta))
            .replace("__LAYERS__", json.dumps(LAYERS)))


def main() -> None:
    entries = load()
    (HERE / "MESSAGES.md").write_text(build_md(entries))
    (HERE / "messages.html").write_text(build_html(entries))
    counts = Counter(e["sev"] for e in entries)
    print(f"wrote MESSAGES.md and messages.html: {len(entries)} messages "
          f"({counts['critical']} critical, {counts['action']} action, "
          f"{counts['warning']} warning, {counts['info']} info)")


if __name__ == "__main__":
    main()
