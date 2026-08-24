#!/usr/bin/env python3
"""Render ops/rebuild.md as a page whose commands can be copied with a click.

The markdown is the source. This exists so that the browser version cannot
drift from it -- two hand-maintained copies of one procedure is precisely the
arrangement that let `operations.md` claim for four releases that this site
lacked a script it already had.

Two things the page does that the markdown cannot. Every command block gets a
copy button, because a rebuild is timed and retyping is where the time goes.
And a block consisting only of `export` lines becomes a small form: the values
that vary between one rebuild and the next are the only text a reader has to
supply, so they are the only text that should look supply-able. Values entered
in one such block appear in every other, since `WEB_PORT` means the same thing
on every page it occurs.

    python3 ops/render-rebuild.py > rebuild.html
"""

import html
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE / "rebuild.md"

EXPORT_LINE = re.compile(r"^export ([A-Z_][A-Z0-9_]*)=(.*)$")


def inline(text: str) -> str:
    """Markdown's inline forms, in the order that stops them eating each other.

    Code spans are extracted first and put back last: their contents are
    literal, and running the emphasis or link patterns over them would turn a
    shell glob into markup.
    """
    spans: list[str] = []

    def stash(match: re.Match[str]) -> str:
        spans.append(html.escape(match.group(1)))
        return f"\x00{len(spans) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{spans[int(m.group(1))]}</code>", text)


def code_block(lines: list[str], index: int) -> str:
    """A command block: a form if it only assigns, a copyable listing if not."""
    assignments = [EXPORT_LINE.match(line) for line in lines if line.strip()]
    if lines and all(assignments):
        fields = "".join(
            f'<label class="field"><span class="var">{m.group(1)}</span>'
            f'<input data-var="{m.group(1)}" value="{html.escape(m.group(2))}" '
            f'spellcheck="false" autocomplete="off"></label>'
            for m in assignments
            if m is not None
        )
        return (
            f'<div class="block form-block" data-block="{index}">'
            f'<div class="block-head"><span class="tag">fill in</span>'
            f'<button class="copy" type="button">copy</button></div>'
            f'<div class="fields">{fields}</div></div>'
        )
    body = html.escape("\n".join(lines))
    return (
        f'<div class="block" data-block="{index}">'
        f'<div class="block-head"><span class="tag">run</span>'
        f'<button class="copy" type="button">copy</button></div>'
        f"<pre><code>{body}</code></pre></div>"
    )


def table(rows: list[str]) -> str:
    """A pipe table. The second row is the alignment rule and is discarded."""
    def cells(row: str) -> list[str]:
        return [c.strip() for c in row.strip().strip("|").split("|")]

    head, body = cells(rows[0]), [cells(r) for r in rows[2:]]
    ths = "".join(f"<th>{inline(c)}</th>" for c in head)
    trs = "".join(
        "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in body
    )
    return f'<div class="tablewrap"><table><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>'


def render(text: str) -> str:
    out: list[str] = []
    lines = text.split("\n")
    i, blocks = 0, 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append(code_block(lines[i + 1 : j], blocks))
            blocks += 1
            i = j + 1
            continue

        if line.startswith("|"):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            out.append(table(lines[i:j]))
            i = j
            continue

        if line.startswith(">"):
            j = i
            gathered = []
            while j < len(lines) and lines[j].startswith(">"):
                gathered.append(lines[j].lstrip("> ").rstrip())
                j += 1
            out.append(f"<blockquote><p>{inline(' '.join(gathered))}</p></blockquote>")
            i = j
            continue

        if line.startswith("- "):
            j = i
            items = []
            while j < len(lines) and (lines[j].startswith("- ") or lines[j].startswith("  ")):
                if lines[j].startswith("- "):
                    items.append(lines[j][2:].strip())
                else:
                    items[-1] += " " + lines[j].strip()
                j += 1
            out.append("<ul>" + "".join(f"<li>{inline(t)}</li>" for t in items) + "</ul>")
            i = j
            continue

        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            out.append(f"<h{level}>{inline(line[level:].strip())}</h{level}>")
            i += 1
            continue

        if line.strip() == "---":
            out.append("<hr>")
            i += 1
            continue

        if line.strip() == "":
            i += 1
            continue

        j = i
        para = []
        while j < len(lines) and lines[j].strip() and not lines[j][0] in "#|>`-":
            para.append(lines[j].strip())
            j += 1
        if not para:  # a line starting with a marker char we do not handle
            para, j = [lines[i].strip()], i + 1
        joined = " ".join(para)
        css = " class=\"record\"" if joined.startswith("`☐`") else ""
        out.append(f"<p{css}>{inline(joined)}</p>")
        i = j

    return "\n".join(out)


# Raw, so that a backslash escape in the JavaScript below reaches the browser
# instead of being interpreted here. Without the `r` prefix `join("\n")`
# becomes a real newline inside a string literal, and the whole script dies
# with a syntax error -- silently, since a page with a broken script still
# renders perfectly. Every copy button was inert for exactly that reason.
TEMPLATE = r"""<meta charset="utf-8">
<title>Rebuild Checklist</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap">
<style>
:root {
  --paper:#F1F3F2; --surface:#FBFCFB; --sunk:#E8EBE9; --ink:#111917;
  --muted:#58635F; --rule:#D3D9D6; --rule-soft:#E2E7E4;
  --accent:#1F5C63; --accent-dim:#2E767E; --warning:#8A6110; --critical:#9E2F1D;
  --serif:"Newsreader",Georgia,serif;
  --sans:"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper:#0E1513; --surface:#16201D; --sunk:#1C2724; --ink:#E3E9E6;
    --muted:#93A09B; --rule:#2A3733; --rule-soft:#212D29;
    --accent:#6FB4BB; --accent-dim:#559AA1; --warning:#D3A244; --critical:#E0725C;
  }
}
:root[data-theme="dark"] {
  --paper:#0E1513; --surface:#16201D; --sunk:#1C2724; --ink:#E3E9E6;
  --muted:#93A09B; --rule:#2A3733; --rule-soft:#212D29;
  --accent:#6FB4BB; --accent-dim:#559AA1; --warning:#D3A244; --critical:#E0725C;
}
* { box-sizing:border-box; }
body {
  margin:0; background:var(--paper); color:var(--ink);
  font-family:var(--sans); font-size:16.5px; line-height:1.62;
  -webkit-font-smoothing:antialiased;
}
.wrap { max-width:48rem; margin:0 auto; padding:clamp(2rem,5vw,4rem) clamp(1.1rem,4vw,2rem) 6rem; }
h1 { font-family:var(--serif); font-weight:500; font-size:clamp(2rem,5vw,2.8rem);
  line-height:1.1; letter-spacing:-.015em; margin:0 0 1.2rem; text-wrap:balance; }
h2 { font-family:var(--serif); font-weight:500; font-size:1.5rem; line-height:1.2;
  margin:2.6rem 0 .9rem; padding-top:1.1rem; border-top:1px solid var(--rule); text-wrap:balance; }
h3 { font-family:var(--sans); font-weight:600; font-size:1.02rem; margin:2rem 0 .8rem; }
p { margin:0 0 .9rem; text-wrap:pretty; }
hr { border:none; border-top:1px solid var(--rule); margin:2.2rem 0; }
a { color:var(--accent); text-underline-offset:2px; }
a:focus-visible, button:focus-visible, input:focus-visible {
  outline:2px solid var(--accent); outline-offset:2px; border-radius:3px; }
code { font-family:var(--mono); font-size:.87em; background:var(--sunk);
  padding:.1em .34em; border-radius:3px; overflow-wrap:break-word; }
td code, th code { overflow-wrap:normal; }
strong { font-weight:600; }
ul { margin:0 0 1rem; padding-left:1.2rem; }
li { margin-bottom:.4rem; }
blockquote { margin:0 0 1.1rem; padding:.85rem 1.1rem; background:var(--surface);
  border:1px solid var(--rule); border-left:2px solid var(--warning);
  border-radius:3px; font-size:.94rem; }
blockquote p { margin:0; }
.tablewrap { overflow-x:auto; border:1px solid var(--rule); border-radius:4px;
  background:var(--surface); margin:0 0 1.2rem; }
table { border-collapse:collapse; width:100%; font-size:.89rem; min-width:30rem; }
th { text-align:left; font-family:var(--mono); font-weight:500; font-size:.67rem;
  letter-spacing:.12em; text-transform:uppercase; color:var(--muted);
  padding:.7rem .85rem; border-bottom:1px solid var(--rule); }
td { padding:.7rem .85rem; border-bottom:1px solid var(--rule-soft); vertical-align:top; }
tbody tr:last-child td { border-bottom:none; }
p.record { font-family:var(--mono); font-size:.82rem; color:var(--muted);
  border-bottom:1px dashed var(--rule); padding-bottom:.5rem; margin-bottom:1.4rem; }

.block { margin:0 0 1.1rem; border:1px solid var(--rule); border-radius:4px;
  background:var(--surface); overflow:hidden; }
.block-head { display:flex; align-items:center; justify-content:space-between;
  gap:1rem; padding:.35rem .55rem .35rem .85rem;
  border-bottom:1px solid var(--rule-soft); background:var(--sunk); }
.tag { font-family:var(--mono); font-size:.62rem; letter-spacing:.14em;
  text-transform:uppercase; color:var(--muted); }
.form-block .tag { color:var(--warning); }
button.copy { font-family:var(--mono); font-size:.68rem; letter-spacing:.08em;
  text-transform:uppercase; color:var(--accent); background:none;
  border:1px solid var(--rule); border-radius:3px; padding:.2rem .6rem;
  cursor:pointer; transition:background .12s, color .12s; }
button.copy:hover { background:var(--accent); color:var(--surface); border-color:var(--accent); }
button.copy.done { color:var(--surface); background:var(--accent-dim); border-color:var(--accent-dim); }
button.copy.failed { color:var(--warning); border-color:var(--warning); background:none; }
pre.fallback { border-top:1px solid var(--rule-soft); user-select:all; }
.block pre { margin:0; padding:.8rem .85rem; overflow-x:auto;
  font-family:var(--mono); font-size:.82rem; line-height:1.6; }
.block pre code { background:none; padding:0; font-size:inherit; }
.fields { display:flex; flex-direction:column; gap:.4rem; padding:.75rem .85rem; }
.field { display:grid; grid-template-columns:minmax(7rem,auto) 1fr; gap:.75rem;
  align-items:center; }
.var { font-family:var(--mono); font-size:.78rem; color:var(--accent); }
.field input { font-family:var(--mono); font-size:.82rem; color:var(--ink);
  background:var(--paper); border:1px solid var(--rule); border-radius:3px;
  padding:.3rem .5rem; width:100%; }
.field input:placeholder-shown, .field input[value=""] { border-color:var(--warning); }

@media print {
  .block-head { display:none; }
  .block, .tablewrap, blockquote { break-inside:avoid; }
  body { font-size:10.5pt; background:#fff; color:#000; }
}
</style>
<div class="wrap">
__BODY__
</div>
<script>
(function () {
  // Copying is attempted three ways, most reliable first, and every outcome
  // says so on the button. The first version of this used only
  // navigator.clipboard.writeText() with no rejection handler: inside an
  // iframe without clipboard-write in its permissions policy that rejects,
  // and the failure was completely silent -- the button did not even flicker.
  //
  // execCommand goes first despite being deprecated, because it must run
  // inside the click's own task to be allowed, and by the time a rejected
  // promise brings us back the user gesture may no longer count.
  function attempt(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.cssText = "position:fixed;top:0;left:0;width:1px;height:1px;opacity:0";
    document.body.appendChild(area);
    area.select();
    area.setSelectionRange(0, text.length);
    var copied = false;
    try { copied = document.execCommand("copy"); } catch (e) { copied = false; }
    document.body.removeChild(area);
    return copied;
  }

  function settle(button, ok, label, hold) {
    button.textContent = label;
    button.classList.toggle("done", ok);
    button.classList.toggle("failed", !ok);
    setTimeout(function () {
      button.textContent = "copy";
      button.classList.remove("done", "failed");
    }, hold);
  }

  // Last resort: put the text on the page and select it, so the reader can
  // press the shortcut themselves. Better than a button that does nothing.
  function offer(block, button, text) {
    var pre = block.querySelector("pre");
    if (!pre) {
      pre = document.createElement("pre");
      pre.className = "fallback";
      pre.textContent = text;
      block.appendChild(pre);
    }
    var range = document.createRange();
    range.selectNodeContents(pre);
    var selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    settle(button, false, "selected \u2014 copy it", 4000);
  }

  function shared(name, value) {
    document.querySelectorAll('input[data-var="' + name + '"]').forEach(function (other) {
      if (other.value !== value) other.value = value;
    });
  }

  document.querySelectorAll(".fields input").forEach(function (input) {
    input.addEventListener("input", function () { shared(input.dataset.var, input.value); });
  });

  document.querySelectorAll("button.copy").forEach(function (button) {
    button.addEventListener("click", function () {
      var block = button.closest(".block");
      var pre = block.querySelector("pre:not(.fallback)");
      var text = pre
        ? pre.innerText
        : Array.prototype.map.call(block.querySelectorAll(".field"), function (field) {
            return "export " + field.querySelector(".var").textContent +
                   "=" + field.querySelector("input").value;
          }).join("\n");

      if (attempt(text)) { settle(button, true, "copied", 1200); return; }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(
          function () { settle(button, true, "copied", 1200); },
          function () { offer(block, button, text); }
        );
      } else {
        offer(block, button, text);
      }
    });
  });
})();
</script>
"""


def main() -> None:
    if not SOURCE.is_file():
        sys.exit(f"no such file: {SOURCE}")
    sys.stdout.write(TEMPLATE.replace("__BODY__", render(SOURCE.read_text())))


if __name__ == "__main__":
    main()
