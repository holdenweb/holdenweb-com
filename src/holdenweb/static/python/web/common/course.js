/* ============================================================================
   course.js — progressive enhancement for the republished Python courses.

   Adds a three-way view switch (changes / prior / updated) to every "Code"
   box that contains edit markup (<ins> / <del>):

     changes  — the code as presented, additions and deletions both shown
     prior    — the code before the edit: plain text + deleted code, kept
     updated  — the code after the edit:  plain text + inserted code, kept

   Switching view animates over two seconds: removed code shrinks to nothing,
   revealed code grows in. To make a whole removed line reclaim its vertical
   space cleanly (a newline alone leaves a strut-height blank line), each line
   is wrapped in a block element and the collapse is driven at the block level.

   It also adds a per-statement "copy" button to every "Code and output" (REPL)
   box: each >>> statement (with its ... continuation lines) can be copied with
   one click, prompts stripped and the code's own indentation preserved.

   No dependencies. Safe to load with `defer`. Does nothing if a Code box has
   no <ins>/<del>, or a Code-and-output box has no >>> prompt. Observe boxes are
   left untouched. Clipboard uses navigator.clipboard with an execCommand
   fallback for pages opened via file://.
   ========================================================================== */
(function () {
  "use strict";

  /* Split one node into per-line fragments, preserving inline markup
     (colour spans, nested tags) by re-wrapping each line in a shallow clone. */
  function splitLines(node) {
    if (node.nodeType === 3) {
      return node.data.split("\n").map(function (s) {
        return s === "" ? [] : [document.createTextNode(s)];
      });
    }
    if (node.nodeType === 1) {
      var lines = [[]];
      Array.prototype.slice.call(node.childNodes).forEach(function (child) {
        splitLines(child).forEach(function (seg, i) {
          if (i > 0) lines.push([]);
          seg.forEach(function (n) { lines[lines.length - 1].push(n); });
        });
      });
      return lines.map(function (ln) {
        var clone = node.cloneNode(false);
        ln.forEach(function (n) { clone.appendChild(n); });
        return [clone];
      });
    }
    return [[]];
  }

  /* A line whose only non-whitespace content is a <del> (or an <ins>) is a
     whole-line removal (or addition); tag it so CSS can collapse the block.
     Leading indentation outside the tag is ignored. */
  function classify(line) {
    var hasText = false, dels = 0, ins = 0, other = 0;
    Array.prototype.slice.call(line.childNodes).forEach(function (n) {
      if (n.nodeType === 3) { if (n.data.replace(/\s/g, "") !== "") hasText = true; }
      else if (n.nodeName === "DEL") dels++;
      else if (n.nodeName === "INS") ins++;
      else other++;
    });
    if (!hasText && !other && dels && !ins) line.setAttribute("data-diff", "del");
    else if (!hasText && !other && ins && !dels) line.setAttribute("data-diff", "ins");
  }

  /* Rebuild a <pre> as one block span per source line, dropping the literal
     newlines (block layout supplies the breaks). */
  function linify(pre) {
    var lines = [[]];
    Array.prototype.slice.call(pre.childNodes).forEach(function (child) {
      splitLines(child).forEach(function (seg, i) {
        if (i > 0) lines.push([]);
        seg.forEach(function (n) { lines[lines.length - 1].push(n); });
      });
    });
    while (lines.length > 1 && lines[lines.length - 1].length === 0) lines.pop();
    pre.textContent = "";
    lines.forEach(function (nodes) {
      var span = document.createElement("span");
      span.className = "cl";
      nodes.forEach(function (n) { span.appendChild(n); });
      classify(span);
      pre.appendChild(span);
    });
  }

  /* True if, after removing every <tag> subtree, any non-whitespace text remains. */
  function remainsAfterRemoving(pre, tag) {
    var clone = pre.cloneNode(true);
    Array.prototype.slice.call(clone.querySelectorAll(tag)).forEach(function (e) {
      e.parentNode.removeChild(e);
    });
    return clone.textContent.replace(/\s/g, "") !== "";
  }

  function setState(pre, state, tabs) {
    pre.classList.remove("is-changes", "is-prior", "is-updated");
    pre.classList.add("is-" + state);
    tabs.forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-state") === state ? "true" : "false");
    });
  }

  function enhance(box) {
    var pre = box.querySelector(".listing pre");
    if (!pre || pre.classList.contains("diff-pre")) return;
    if (!pre.querySelector("ins, del")) return;

    /* Decide which views are meaningful for this box. "prior" is plain + deleted
       code; "updated" is plain + inserted code. A view that would render empty
       (e.g. "prior" of an entirely-new box) stays visible but disabled. */
    var enabled = {
      changes: true,
      prior: remainsAfterRemoving(pre, "ins"),    /* plain + del survive */
      updated: remainsAfterRemoving(pre, "del")   /* plain + ins survive */
    };

    pre.classList.add("diff-pre");
    linify(pre);

    var tabs = [];
    var title = box.querySelector(".listingTitle");
    if (title) {
      var group = document.createElement("span");
      group.className = "diff-tabs";
      group.setAttribute("role", "group");
      group.setAttribute("aria-label", "Show changes, prior version, or updated version");
      ["changes", "prior", "updated"].forEach(function (state) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "diff-tab";
        b.setAttribute("data-state", state);
        b.textContent = state;
        if (enabled[state]) {
          b.addEventListener("click", function () { setState(pre, state, tabs); });
        } else {
          b.disabled = true;
          b.setAttribute("aria-disabled", "true");
          b.title = "Not applicable — this snippet is entirely " +
            (state === "prior" ? "new" : "removed") + " code";
        }
        group.appendChild(b);
        tabs.push(b);
      });
      title.appendChild(group);
    }
    setState(pre, "changes", tabs);
  }

  /* ----- Per-statement copy buttons for "Code and output" (REPL) boxes -----
     The entered code is the lines beginning with a >>> prompt plus any
     following ... continuation lines; everything else is output. Each such
     "piece" gets a copy button that copies just the code, prompts stripped. */

  var PROMPT = /^(>>>|\.\.\.) ?/;

  function lineText(nodes) {
    return nodes.map(function (n) { return n.textContent; }).join("");
  }

  /* Split a <pre> into an array of per-line node lists (reusing splitLines). */
  function lineList(pre) {
    var lines = [[]];
    Array.prototype.slice.call(pre.childNodes).forEach(function (child) {
      splitLines(child).forEach(function (seg, i) {
        if (i > 0) lines.push([]);
        seg.forEach(function (n) { lines[lines.length - 1].push(n); });
      });
    });
    while (lines.length > 1 && lines[lines.length - 1].length === 0) lines.pop();
    return lines;
  }

  function blockLine(nodes) {
    var span = document.createElement("span");
    span.className = "cl";
    nodes.forEach(function (n) { span.appendChild(n); });
    return span;
  }

  function legacyCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.cssText = "position:fixed;top:-1000px;left:-1000px";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta);
  }
  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).catch(function () { legacyCopy(text); });
    } else {
      legacyCopy(text);
    }
  }

  function enhanceInteractive(box) {
    var pre = box.querySelector(".interactive pre");
    if (!pre || pre.classList.contains("repl-pre")) return;
    if (!/(^|\n)>>>/.test(pre.textContent)) return;   /* no REPL input: leave alone */

    var lines = lineList(pre);
    pre.textContent = "";
    pre.classList.add("repl-pre");

    var i = 0;
    while (i < lines.length) {
      if (/^>>>/.test(lineText(lines[i]))) {
        var piece = [lines[i]];           /* a >>> line + its ... continuations */
        var j = i + 1;
        while (j < lines.length && /^\.\.\./.test(lineText(lines[j]))) {
          piece.push(lines[j]); j++;
        }
        var code = piece.map(function (ns) {
          return lineText(ns).replace(PROMPT, "");
        }).join("\n").replace(/[ \t]*\n+$/, "");

        var wrap = document.createElement("span");
        wrap.className = "repl-piece";
        piece.forEach(function (ns) { wrap.appendChild(blockLine(ns)); });

        if (code.replace(/\s/g, "") !== "") {
          var btn = document.createElement("button");
          btn.type = "button";
          btn.className = "repl-copy";
          btn.textContent = "copy";
          btn.setAttribute("aria-label", "Copy this code");
          (function (code, btn) {
            btn.addEventListener("click", function (e) {
              e.stopPropagation();
              copyToClipboard(code);
              btn.classList.add("copied");
              btn.textContent = "copied";
              setTimeout(function () {
                btn.classList.remove("copied");
                btn.textContent = "copy";
              }, 1400);
            });
          })(code, btn);
          wrap.appendChild(btn);
        }
        pre.appendChild(wrap);
        i = j;
      } else {
        pre.appendChild(blockLine(lines[i]));
        i++;
      }
    }
  }

  /* Add a "Contents" link (to the course's index.html) to each lesson's
     prev/next nav. Index pages have no .lesson-nav, so they're unaffected. */
  function addContentsLinks() {
    Array.prototype.slice.call(document.querySelectorAll(".lesson-nav")).forEach(function (nav) {
      if (nav.querySelector(".contents")) return;
      var a = document.createElement("a");
      a.className = "contents";
      a.href = "index.html";
      a.textContent = "Contents";
      nav.appendChild(a);
    });
  }

  function init() {
    Array.prototype.slice.call(document.querySelectorAll(".listingBox")).forEach(enhance);
    Array.prototype.slice.call(document.querySelectorAll(".interactiveBox")).forEach(enhanceInteractive);
    addContentsLinks();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
