#!/usr/bin/env python3
"""Static site generator for Tech2You.

Reads prompts/examples/*.yaml and topic_radar/digests/*.md and renders a
plain static site into docs/ — no build tooling, no JS framework (one small
inline script for a cursor-tracked card glow), so it can be previewed by
opening docs/index.html directly, or served for free via GitHub Pages
(repo settings -> Pages -> serve from /docs on main).

Usage: python site/generate.py
"""

import html
import shutil
from pathlib import Path

import markdown as md
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts" / "examples"
DIGESTS_DIR = ROOT / "topic_radar" / "digests"
OUT_DIR = ROOT / "docs"

yaml = YAML()

NAV = [("index.html", "Home"), ("prompts.html", "Prompt Library"), ("digests.html", "Topic Radar")]

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700'
    '&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
)

CSS = """
:root {
  --bg: #05060a;
  --border: rgba(255,255,255,0.09);
  --text: #eef1f8;
  --text-dim: #8990a8;
  --accent-1: #4dd8ff;
  --accent-2: #a78bfa;
  --accent-3: #ff6ec7;
  --gradient: linear-gradient(120deg, var(--accent-1), var(--accent-2));
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: 'Space Grotesk', -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
}
.bg-grid {
  position: fixed; inset: 0; z-index: -2;
  background-image:
    linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 75% 55% at 50% 0%, #000 40%, transparent 100%);
  -webkit-mask-image: radial-gradient(ellipse 75% 55% at 50% 0%, #000 40%, transparent 100%);
}
.bg-glow { position: fixed; z-index: -1; border-radius: 50%; filter: blur(120px); opacity: .32; animation: drift 20s ease-in-out infinite alternate; }
.bg-glow.a { width: 520px; height: 520px; background: var(--accent-1); top: -180px; left: -140px; }
.bg-glow.b { width: 480px; height: 480px; background: var(--accent-2); bottom: -200px; right: -160px; animation-delay: -8s; }
@keyframes drift { from { transform: translate(0,0); } to { transform: translate(50px,60px); } }

a { color: var(--accent-1); text-decoration: none; }
a:hover { text-decoration: underline; }
code, pre, .badge, .kicker, .mono { font-family: 'JetBrains Mono', Consolas, monospace; }

header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1.1rem 2rem;
  position: sticky; top: 0; z-index: 10;
  background: rgba(5,6,10,0.7);
  backdrop-filter: blur(14px) saturate(140%);
  border-bottom: 1px solid var(--border);
}
.brand {
  font-weight: 700; font-size: 1.2rem; letter-spacing: -0.02em;
  background: var(--gradient); -webkit-background-clip: text; background-clip: text; color: transparent;
}
header nav a {
  color: var(--text-dim); margin-left: .35rem; font-size: .85rem; font-weight: 500;
  padding: .45rem .85rem; border-radius: 8px; transition: color .2s ease, background .2s ease;
}
header nav a:hover { color: var(--text); background: rgba(255,255,255,0.06); text-decoration: none; }
header nav a.active { color: #05060a; background: var(--gradient); }

main { max-width: 920px; margin: 0 auto; padding: 3rem 1.75rem 6rem; }

.kicker {
  display: inline-flex; align-items: center; gap: .5rem;
  font-size: .74rem; letter-spacing: .14em; text-transform: uppercase;
  color: var(--accent-1);
  padding: .4rem .8rem; border-radius: 999px;
  border: 1px solid rgba(77,216,255,.3); background: rgba(77,216,255,.06);
}
.kicker .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent-1); box-shadow: 0 0 8px var(--accent-1); animation: pulse 1.6s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .3; } }

.hero { padding: 1.5rem 0 3rem; }
.hero h1 {
  font-size: clamp(2.6rem, 6vw, 4.2rem); font-weight: 700; letter-spacing: -0.03em;
  margin: 1rem 0 1rem; line-height: 1.05;
  background: linear-gradient(120deg, #fff 10%, var(--accent-1) 55%, var(--accent-2) 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { color: var(--text-dim); font-size: 1.08rem; max-width: 620px; }

.pillars { display: grid; grid-template-columns: 1fr 1fr; gap: 1.1rem; margin-top: 2.5rem; }
@media (max-width: 680px) { .pillars { grid-template-columns: 1fr; } }

.card {
  --mx: 50%; --my: 50%;
  position: relative; overflow: hidden;
  background: linear-gradient(180deg, rgba(255,255,255,.045), rgba(255,255,255,.015));
  border: 1px solid var(--border); border-radius: 16px;
  padding: 1.6rem 1.7rem; backdrop-filter: blur(12px);
  transition: transform .3s ease, border-color .3s ease, box-shadow .3s ease;
  margin-bottom: 1.1rem;
}
.card::before {
  content: ""; position: absolute; inset: 0; pointer-events: none; opacity: 0;
  background: radial-gradient(280px circle at var(--mx) var(--my), rgba(77,216,255,.16), transparent 60%);
  transition: opacity .3s ease;
}
.card:hover { transform: translateY(-5px); border-color: rgba(77,216,255,.35); box-shadow: 0 24px 60px -24px rgba(77,216,255,.35); }
.card:hover::before { opacity: 1; }
.card > * { position: relative; z-index: 1; }
.card h3 { margin: 0 0 .5rem; font-size: 1.08rem; letter-spacing: -0.01em; }
.card p { color: var(--text-dim); margin: 0 0 .8rem; font-size: .93rem; }

.badge {
  display: inline-block; font-size: .7rem; font-weight: 500; text-transform: uppercase; letter-spacing: .06em;
  color: var(--accent-1); background: rgba(77,216,255,.08); border: 1px solid rgba(77,216,255,.3);
  border-radius: 6px; padding: .2rem .55rem; margin: 0 .4rem .4rem 0;
}
.badge.alt { color: var(--accent-2); background: rgba(167,139,250,.08); border-color: rgba(167,139,250,.3); }

.empty {
  color: var(--text-dim); font-size: .95rem; padding: 2rem 1.5rem; text-align: center;
  border: 1px dashed var(--border); border-radius: 14px;
}

.terminal { border-radius: 14px; overflow: hidden; border: 1px solid var(--border); background: #0a0c12; margin: 1rem 0 1.5rem; }
.terminal .bar { display: flex; gap: 6px; padding: .65rem .9rem; background: rgba(255,255,255,.03); border-bottom: 1px solid var(--border); }
.terminal .bar span { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.terminal .bar span:nth-child(1) { background: #ff5f57; }
.terminal .bar span:nth-child(2) { background: #febc2e; }
.terminal .bar span:nth-child(3) { background: #28c840; }
.terminal pre { margin: 0; border: none; border-radius: 0; background: transparent; padding: 1.15rem; }
pre { background: #0a0c12; border: 1px solid var(--border); border-radius: 12px; padding: 1.1rem; overflow-x: auto; font-size: .85rem; color: #d7dce6; }

.meta { color: var(--text-dim); font-size: .85rem; margin-bottom: 1.4rem; }
.meta code { color: var(--text); }
h2 { font-size: 1.3rem; margin-top: 2.4rem; letter-spacing: -0.01em; }
.back { display: inline-flex; align-items: center; gap: .35rem; margin-bottom: 1.75rem; color: var(--text-dim); font-size: .88rem; transition: color .2s; }
.back:hover { color: var(--accent-1); text-decoration: none; }

footer {
  max-width: 920px; margin: 0 auto; padding: 2.5rem 1.75rem;
  border-top: 1px solid var(--border); color: var(--text-dim); font-size: .82rem;
}
"""

SPOTLIGHT_JS = """
document.querySelectorAll('.card').forEach(function (el) {
  el.addEventListener('mousemove', function (e) {
    var r = el.getBoundingClientRect();
    el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
    el.style.setProperty('--my', (e.clientY - r.top) + 'px');
  });
});
"""


def layout(title: str, body: str, active: str) -> str:
    nav_html = "".join(
        f'<a href="{href}"{" class=active" if href == active else ""}>{label}</a>' for href, label in NAV
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · Tech2You</title>
{FONTS}
<style>{CSS}</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow a"></div>
<div class="bg-glow b"></div>
<header>
  <a class="brand" href="index.html">tech2you</a>
  <nav>{nav_html}</nav>
</header>
<main>
{body}
</main>
<footer class="mono">&gt; tech2you --status active · AI literacy hub · generated by site/generate.py</footer>
<script>{SPOTLIGHT_JS}</script>
</body>
</html>"""


def load_prompts() -> list:
    prompts = []
    if PROMPTS_DIR.exists():
        for path in sorted(PROMPTS_DIR.glob("*.yaml")):
            with open(path, encoding="utf-8") as f:
                data = yaml.load(f)
            data["_slug"] = path.stem
            prompts.append(data)
    return prompts


def load_digests() -> list:
    digests = []
    if DIGESTS_DIR.exists():
        for path in sorted(DIGESTS_DIR.glob("*.md"), reverse=True):
            digests.append(path)
    return digests


def build_index(prompts: list, digests: list) -> str:
    body = f"""
<div class="hero">
  <span class="kicker"><span class="dot"></span>ai literacy hub</span>
  <h1>Tech2You</h1>
  <p>Reusable prompt building blocks for agents and pipelines, plus an LLM-curated
  radar of trending AI topics worth making a video about.</p>
</div>
<div class="pillars">
  <div class="card">
    <h3>Prompt Library</h3>
    <p>{len(prompts)} prompt/agent recipe{"s" if len(prompts) != 1 else ""} — composable, graph-aware,
    scored by an LLM eval harness.</p>
    <a href="prompts.html">Browse prompts &rarr;</a>
  </div>
  <div class="card">
    <h3>Topic Radar</h3>
    <p>{len(digests)} digest{"s" if len(digests) != 1 else ""} — trending AI topics pulled from free
    APIs, curated into video angles.</p>
    <a href="digests.html">Browse digests &rarr;</a>
  </div>
</div>
"""
    return layout("Home", body, "index.html")


def build_prompts_list(prompts: list) -> str:
    if not prompts:
        cards = '<div class="empty">No prompts yet — add one under <code>prompts/examples/</code>.</div>'
    else:
        cards = ""
        for p in prompts:
            eval_block = p.get("eval") or {}
            score = eval_block.get("score")
            badge = f'<span class="badge">{p.get("category", "")}</span>'
            if score is not None:
                badge += f'<span class="badge alt">score {score}/5</span>'
            cards += f"""<div class="card">
  <h3><a href="prompt-{p['_slug']}.html">{html.escape(p.get('title', p['_slug']))}</a></h3>
  <p>{html.escape(p.get('description', ''))}</p>
  {badge}
</div>
"""
    body = f'<span class="kicker"><span class="dot"></span>prompt library</span><h1>Composable prompts</h1>{cards}'
    return layout("Prompt Library", body, "prompts.html")


def build_prompt_detail(p: dict) -> str:
    graph = p.get("graph")
    graph_html = ""
    if graph:
        graph_html = f"""<h2>Graph position</h2>
<p class="meta">This prompt is a <code>{p.get('type')}</code> node: <code>{graph.get('position')}</code>
&mdash; upstream: <code>{', '.join(graph.get('upstream') or []) or 'none'}</code>,
downstream: <code>{', '.join(graph.get('downstream') or []) or 'none'}</code></p>"""

    variables = p.get("variables") or []
    var_rows = "".join(
        f"<li><code>{v.get('name')}</code> ({v.get('type')}{', required' if v.get('required') else ''}) — "
        f"{html.escape(v.get('description', ''))}</li>"
        for v in variables
    )

    eval_block = p.get("eval") or {}
    eval_html = ""
    if eval_block.get("last_run"):
        eval_html = f"""<h2>Latest eval</h2>
<p class="meta">Score: <code>{eval_block.get('score')}/5</code> &middot; Last run: <code>{eval_block.get('last_run')}</code></p>
<p class="meta">{html.escape(eval_block.get('notes') or '')}</p>"""

    body = f"""
<a class="back" href="prompts.html">&larr; All prompts</a>
<h1>{html.escape(p.get('title', p['_slug']))}</h1>
<p class="meta">
  <span class="badge">{p.get('category', '')}</span>
  <span class="badge alt">{(p.get('model') or {}).get('recommended', '')}</span>
</p>
<p>{html.escape(p.get('description', ''))}</p>
{graph_html}
<h2>Variables</h2>
<ul>{var_rows or '<li>none</li>'}</ul>
<h2>Prompt template</h2>
<div class="terminal">
  <div class="bar"><span></span><span></span><span></span></div>
  <pre><code>{html.escape(p.get('prompt', ''))}</code></pre>
</div>
{eval_html}
"""
    return layout(p.get("title", p["_slug"]), body, "prompts.html")


def build_digests_list(digests: list) -> str:
    if not digests:
        cards = (
            '<div class="empty">No digests yet — run '
            '<code>python topic_radar/digest.py</code> to generate one.</div>'
        )
    else:
        cards = ""
        for path in digests:
            cards += f"""<div class="card">
  <h3><a href="digest-{path.stem}.html">{path.stem}</a></h3>
</div>
"""
    body = f'<span class="kicker"><span class="dot"></span>topic radar</span><h1>Video topic feed</h1>{cards}'
    return layout("Topic Radar", body, "digests.html")


def build_digest_detail(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    rendered = md.markdown(content)
    body = f'<a class="back" href="digests.html">&larr; All digests</a>\n{rendered}'
    return layout(path.stem, body, "digests.html")


def main():
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    prompts = load_prompts()
    digests = load_digests()

    (OUT_DIR / "index.html").write_text(build_index(prompts, digests), encoding="utf-8")
    (OUT_DIR / "prompts.html").write_text(build_prompts_list(prompts), encoding="utf-8")
    (OUT_DIR / "digests.html").write_text(build_digests_list(digests), encoding="utf-8")

    for p in prompts:
        (OUT_DIR / f"prompt-{p['_slug']}.html").write_text(build_prompt_detail(p), encoding="utf-8")

    for path in digests:
        (OUT_DIR / f"digest-{path.stem}.html").write_text(build_digest_detail(path), encoding="utf-8")

    print(f"Built {3 + len(prompts) + len(digests)} pages into {OUT_DIR}")


if __name__ == "__main__":
    main()
