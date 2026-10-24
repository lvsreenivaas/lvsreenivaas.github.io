#!/usr/bin/env python3
"""Generates the static pages for lvsreenivaas.github.io.

Emits plain HTML — there is no build step on GitHub Pages. Re-run this script
and commit the output if the shared nav/footer/head needs to change.
"""
import html, json, os, pathlib

OUT = pathlib.Path("/Users/lvsreenivaas/Desktop/github.io")
SITE = "https://lvsreenivaas.github.io"
NAME = "Venkata Sreenivaas Lingam"
EMAIL = "venkata_sl@berkeley.edu"
GH = "https://github.com/lvsreenivaas"
LI = "https://linkedin.com/in/sreenivaaslv"
SSRN = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7661378"
RESUME = "assets/RESUME_VENKATA_SREE_LINGAM.pdf"

# ---- placeholders the owner fills in -------------------------------------
GA4_ID = "G-XXXXXXXXXX"            # Google Analytics 4 measurement ID
GSC_TOKEN = "PASTE_SEARCH_CONSOLE_TOKEN"   # Search Console HTML-tag verification
FORMSPREE = "https://formspree.io/f/PASTE_FORM_ID"

NAV = [("index.html", "Home"), ("projects.html", "Projects"),
       ("research.html", "Research"), ("reading.html", "Reading"),
       ("contact.html", "Contact")]


# =========================================================================
# chart helpers  (palette validated: dataviz validate_palette.js
# --mode dark --surface #0d111c --pairs all  → ALL CHECKS PASS)
# =========================================================================
S1, S2, S3, NEUTRAL = "#3987e5", "#d95926", "#199e70", "#6b7280"


def _tip(x, y, lines, anchor="middle"):
    w = max(len(l) for l in lines) * 6.4 + 20
    h = 15 * len(lines) + 13
    tx = x - w / 2 if anchor == "middle" else x
    ty = y - h - 9
    txt = "".join(
        f'<text x="{tx+10:.0f}" y="{ty+19+15*i:.0f}">{html.escape(l)}</text>'
        for i, l in enumerate(lines))
    return (f'<g class="tip"><rect x="{tx:.0f}" y="{ty:.0f}" '
            f'width="{w:.0f}" height="{h:.0f}"/>{txt}</g>')


def hbar(rows, fmt, maxv=None, thresh=None, thresh_label="", unit="",
         colors=None, lw=168, h=38):
    """Horizontal bars — magnitude across named categories, one measure.

    rows: [(label, value, tooltip_extra)] ; colors: per-row hex or None (slot 1).
    """
    maxv = maxv or max(r[1] for r in rows) * 1.18
    W, pad = 640, 10
    plot = W - lw - pad
    top = 22 if thresh is not None else 6          # room for the threshold label
    H = len(rows) * h + 28 + top
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="Bar chart: {html.escape(", ".join(f"{r[0]} {fmt(r[1])}" for r in rows))}">']
    # recessive gridlines
    for f in (0, .25, .5, .75, 1):
        x = lw + plot * f
        out.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{H-28:.0f}"/>')
        out.append(f'<text class="lbl" x="{x:.1f}" y="{H-12:.0f}" text-anchor="middle">'
                   f'{fmt(maxv*f)}</text>')
    for i, r in enumerate(rows):
        label, v = r[0], r[1]
        extra = r[2] if len(r) > 2 else None
        y = top + i * h
        bw = max(3, plot * v / maxv)
        c = (colors or [S1] * len(rows))[i]
        tip = [f"{label}: {fmt(v)}{unit}"] + ([extra] if extra else [])
        vx = lw + bw + 9
        if thresh is not None:                      # avoid colliding with the alpha line
            tx = lw + plot * thresh / maxv
            if vx - 4 < tx < vx + len(fmt(v)) * 8 + 6:
                vx = tx + 10
        out.append(
            f'<g class="mark" tabindex="0" role="listitem" '
            f'aria-label="{html.escape(label)}: {fmt(v)}{html.escape(unit)}">'
            f'<rect class="hit" x="0" y="{y}" width="{W}" height="{h}"/>'
            f'<text class="lbl" x="{lw-12}" y="{y+h/2+4:.0f}" text-anchor="end">'
            f'{html.escape(label)}</text>'
            f'<rect class="bar" x="{lw}" y="{y+6}" width="{bw:.1f}" height="{h-18}" fill="{c}"/>'
            f'<text class="val" x="{vx:.1f}" y="{y+h/2+4:.0f}">{fmt(v)}</text>'
            + _tip(lw + bw / 2, y + 6, tip) + '</g>')
    if thresh is not None:
        x = lw + plot * thresh / maxv
        out.append(f'<line class="thresh" x1="{x:.1f}" y1="{top-4}" x2="{x:.1f}" '
                   f'y2="{H-28:.0f}"/>')
        out.append(f'<text class="lbl" x="{x:.1f}" y="{top-10}" text-anchor="middle" '
                   f'fill="{S2}" style="font-weight:600">'
                   f'{html.escape(thresh_label)}</text>')
    out.append(f'<line class="axis" x1="{lw}" y1="{top}" x2="{lw}" y2="{H-28}"/>')
    out.append("</svg>")
    return "".join(out)


def table_view(headers, rows, caption):
    th = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    tr = "".join("<tr>" + "".join(
        f'<td class="num">{c}</td>' if i else f"<td>{c}</td>"
        for i, c in enumerate(r)) + "</tr>" for r in rows)
    return (f'<details class="tableview"><summary>View as table</summary>'
            f'<div class="scroll-x"><table class="tbl"><caption class="note" '
            f'style="text-align:left;padding:6px 0">{html.escape(caption)}</caption>'
            f"<thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div></details>")


def figure(title, sub, svg, caption, legend="", tbl=""):
    leg = f'<div class="legend">{legend}</div>' if legend else ""
    return (f'<figure class="chart"><p class="ct">{title}</p>'
            f'<p class="cs">{sub}</p>{svg}{leg}'
            f"<figcaption>{caption}</figcaption>{tbl}</figure>")


def regime_timeline():
    """Diverging ordinal band: contraction ← neutral → expansion, 62 quarters."""
    eps = [("Neutral", 2011.00, 2011.50, NEUTRAL, "2011 Q1–Q2", 2),
           ("Contraction", 2011.50, 2013.75, S2, "2011 Q3 – 2013 Q3", 9),
           ("Neutral", 2013.75, 2020.00, NEUTRAL, "2013 Q4 – 2019 Q4", 25),
           ("Contraction", 2020.00, 2023.25, S2, "2020 Q1 – 2023 Q1", 13),
           ("Expansion", 2023.25, 2026.50, S1, "2023 Q2 – 2026 Q2", 13)]
    W, H, t0, t1 = 640, 128, 2011.0, 2026.5
    sx = lambda t: 8 + (W - 16) * (t - t0) / (t1 - t0)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Timeline: the hidden '
           f'Markov model splits 62 quarters into just five contiguous regime episodes, '
           f'mean length 12.4 quarters">']
    for name, a, b, c, when, nq in eps:
        x, w = sx(a), sx(b) - sx(a)
        out.append(
            f'<g class="mark" tabindex="0" role="listitem" aria-label="{name}, {when}, {nq} quarters">'
            f'<rect class="cell" x="{x:.1f}" y="30" width="{w:.1f}" height="44" fill="{c}" rx="4"/>'
            + (f'<text class="val" x="{x+w/2:.1f}" y="57" text-anchor="middle" '
               f'style="font-size:11px">{nq}q</text>' if w > 34 else "")
            + _tip(x + w / 2, 30, [f"{name} · {nq} quarters", when]) + "</g>")
    for yr in range(2011, 2027, 3):
        out.append(f'<line class="grid" x1="{sx(yr):.1f}" y1="78" x2="{sx(yr):.1f}" y2="84"/>')
        out.append(f'<text class="lbl" x="{sx(yr):.1f}" y="98" text-anchor="middle">{yr}</text>')
    out.append(f'<text class="lbl" x="8" y="18">62 quarters · 5 episodes · mean 12.4q</text>')
    out.append(f'<text class="lbl" x="{W-8}" y="118" text-anchor="end" fill="{S1}">'
               f'the only expansion is also the most recent period</text>')
    out.append("</svg>")
    return "".join(out)


# =========================================================================
# page shell
# =========================================================================
def head(p):
    url = f"{SITE}/" if p["file"] == "index.html" else f"{SITE}/{p['file']}"
    crumbs = [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"}]
    if p["file"] != "index.html":
        crumbs.append({"@type": "ListItem", "position": 2, "name": p["crumb"], "item": url})
    schema = [
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs}
    ] + p.get("schema", [])
    jsonld = "\n".join(
        f'<script type="application/ld+json">{json.dumps(s, separators=(",", ":"))}</script>'
        for s in schema)
    noindex = '\n  <meta name="robots" content="noindex, follow" />' if p.get("noindex") else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />

  <!-- 4. unique title · 5. meta description -->
  <title>{html.escape(p['title'])}</title>
  <meta name="description" content="{html.escape(p['desc'])}" />
  <meta name="author" content="{NAME}" />{noindex}

  <!-- 7. canonical -->
  <link rel="canonical" href="{url}" />

  <!-- 8. Open Graph / Twitter card -->
  <meta property="og:type" content="{p.get('ogtype', 'website')}" />
  <meta property="og:site_name" content="{NAME}" />
  <meta property="og:title" content="{html.escape(p['title'])}" />
  <meta property="og:description" content="{html.escape(p['desc'])}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{SITE}/assets/og-image.png" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:alt" content="{NAME} — quantitative research and trading, UC Berkeley MFE" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{html.escape(p['title'])}" />
  <meta name="twitter:description" content="{html.escape(p['desc'])}" />
  <meta name="twitter:image" content="{SITE}/assets/og-image.png" />

  <!-- 18. Search Console: replace the token, then hit Verify -->
  <meta name="google-site-verification" content="{GSC_TOKEN}" />

  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml" />
  <link rel="preload" as="image" href="assets/me.webp" fetchpriority="high" />
  <link rel="stylesheet" href="assets/style.css" />

  <!-- 14. structured data · 15. breadcrumb schema -->
{jsonld}

  <!-- 17. Analytics: replace {GA4_ID} with your GA4 measurement ID.
       Until then this loads nothing and tracks nothing. -->
  <script>
    window.GA_ID = "{GA4_ID}";
    if (window.GA_ID.indexOf("X") === -1) {{
      var s = document.createElement("script"); s.async = true;
      s.src = "https://www.googletagmanager.com/gtag/js?id=" + window.GA_ID;
      document.head.appendChild(s);
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      window.gtag = gtag; gtag("js", new Date());
      gtag("config", window.GA_ID, {{ anonymize_ip: true }});
    }}
  </script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""


def nav(cur):
    CUR = ' aria-current="page"'
    links = "".join(
        '<a href="%s"%s>%s</a>' % (f, CUR if f == cur else "", t)
        for f, t in NAV)
    return f"""<nav class="nav" aria-label="Primary">
  <div class="nav-inner">
    <a class="brand" href="index.html"><span class="dot" aria-hidden="true"></span>
      <strong>{NAME}</strong></a>
    <div class="nav-links">{links}
      <a class="btn primary sm" href="{RESUME}" target="_blank" rel="noopener">Résumé (PDF)</a>
    </div>
  </div>
</nav>
"""


def crumbs_html(p):
    if p["file"] == "index.html":
        return ""
    return (f'<nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a>'
            f'<span class="sep" aria-hidden="true">/</span>'
            f'<span aria-current="page">{html.escape(p["crumb"])}</span></nav>')


# 16. internal links — every page links to every other, plus deep links
FOOTER = f"""<footer class="wrap">
  <div class="foot">
    <div>
      <h4>{NAME}</h4>
      <p class="note">Quantitative research &amp; trading. UC Berkeley MFE, Class of 2027.
      Currently seeking full-time trading and research roles starting 2027.</p>
      <div class="cta-row">
        <a class="btn sm" href="{GH}" rel="me noopener" target="_blank">GitHub</a>
        <a class="btn sm" href="{LI}" rel="me noopener" target="_blank">LinkedIn</a>
        <a class="btn sm" href="mailto:{EMAIL}">Email</a>
      </div>
    </div>
    <div>
      <h4>Pages</h4>
      <a href="index.html">Home</a>
      <a href="projects.html">Projects</a>
      <a href="research.html">Research</a>
      <a href="reading.html">Reading</a>
      <a href="contact.html">Contact</a>
    </div>
    <div>
      <h4>Work</h4>
      <a href="projects.html#prisma">Private-markets data pipeline</a>
      <a href="projects.html#regimes">Software-cycle regimes</a>
      <a href="projects.html#gnn">Graph neural networks</a>
      <a href="projects.html#citi">BTP–Bund hedging</a>
      <a href="research.html#firms-that-look-alike">SSRN paper</a>
      <a href="{RESUME}" target="_blank" rel="noopener">Résumé (PDF)</a>
    </div>
  </div>
  <div class="foot-end">
    <span>© <span id="year">2026</span> {NAME}</span>
    <span><a href="privacy.html" style="display:inline">Privacy</a> ·
      Static HTML on GitHub Pages · no trackers beyond the analytics noted in the policy</span>
  </div>
</footer>
<script>
  document.getElementById("year").textContent = new Date().getFullYear();
</script>
</body>
</html>
"""


def page(p):
    return (head(p) + nav(p["file"]) + '<main id="main" class="wrap">'
            + crumbs_html(p) + p["body"] + "</main>" + FOOTER)


# =========================================================================
# shared schema blocks
# =========================================================================
PERSON = {
    "@context": "https://schema.org", "@type": "Person", "@id": f"{SITE}/#person",
    "name": NAME, "givenName": "Venkata Sreenivaas", "familyName": "Lingam",
    "url": f"{SITE}/", "image": f"{SITE}/assets/og-image.png",
    "email": f"mailto:{EMAIL}",
    "jobTitle": "Quantitative Researcher",
    "description": ("Quantitative researcher and UC Berkeley MFE candidate (Class of 2027) "
                    "working on regime inference, graph learning for the cross-section of "
                    "returns, and private-markets data engineering."),
    "alumniOf": [
        {"@type": "CollegeOrUniversity", "name": "Rutgers University",
         "url": "https://www.rutgers.edu/"}],
    "affiliation": {
        "@type": "EducationalOrganization",
        "name": "University of California, Berkeley — Haas School of Business",
        "url": "https://mfe.haas.berkeley.edu/",
        "department": {"@type": "EducationalOrganization",
                       "name": "Master of Financial Engineering"}},
    "knowsAbout": ["Quantitative research", "Statistical arbitrage", "Regime-switching models",
                   "Graph neural networks", "Market microstructure", "Private equity data",
                   "Fixed income hedging", "Time-series forecasting"],
    "sameAs": [GH, LI, SSRN],
    "seeks": {"@type": "Demand",
              "name": "Full-time quantitative trading and quantitative research roles"},
}

WEBSITE = {"@context": "https://schema.org", "@type": "WebSite", "@id": f"{SITE}/#website",
           "url": f"{SITE}/", "name": NAME,
           "description": "Quantitative research projects, papers and notes.",
           "inLanguage": "en-US",
           "publisher": {"@id": f"{SITE}/#person"},
           "author": {"@id": f"{SITE}/#person"}}

PAPER = {
    "@context": "https://schema.org", "@type": "ScholarlyArticle",
    "@id": f"{SITE}/research.html#firms-that-look-alike",
    "headline": "Firms That Look Alike: Characteristic Graphs and the Cross-Section of Stock Returns",
    "name": "Firms That Look Alike: Characteristic Graphs and the Cross-Section of Stock Returns",
    "author": [{"@type": "Person", "name": "Aaryen Milan Mehta"},
               {"@type": "Person", "name": "Tejas Girhe"},
               {"@type": "Person", "name": NAME, "@id": f"{SITE}/#person"}],
    "datePublished": "2026-10", "inLanguage": "en-US", "url": SSRN,
    "sameAs": SSRN, "isAccessibleForFree": True,
    "keywords": ["graph neural networks", "firm similarity", "return predictability",
                 "short-term reversal", "look-ahead bias"],
    "abstract": ("Graph neural networks forecast stock returns by passing information between "
                 "economically or statistically linked firms. We ask whether links inferred from "
                 "64 firm characteristics improve return forecasts relative to a neural network "
                 "using the same characteristics without a graph. In U.S. stocks from 2010 to "
                 "2024, characteristic neighbours act more as a reference group than as a source "
                 "of extra information."),
    "publisher": {"@type": "Organization", "name": "Social Science Research Network (SSRN)",
                  "url": "https://www.ssrn.com/"},
}

print("helpers loaded")

# =========================================================================
# CHARTS
# =========================================================================
p3 = lambda v: f"{v:.3f}"
p2 = lambda v: f"{v:.2f}"
pct = lambda v: f"{v:.0f}%"
pct1 = lambda v: f"{v:.1f}%"
mult = lambda v: f"{v:.3f}x"

CH_PVAL = figure(
    "What you permute decides what you find",
    "ΔR² of regime dummies over tvpi_w ~ age + age², n = 1,493 funds. "
    "Same estimand, four null hypotheses.",
    hbar([("Across funds (1,493 units)", 0.045,
           "The naive null. Treats every fund as independent."),
          ("Across vintages (15 units)", 0.155,
           "Respects vintage clustering."),
          ("Circular shift, episodes kept (5 units)", 0.197,
           "Respects the actual 5 regime episodes. Only 61 distinct draws exist.")],
         p3, maxv=0.26, thresh=0.05, thresh_label="α = 0.05",
         colors=[S1, S1, S1], lw=238),
    "p rises monotonically as the null respects more of the data's structure. That ordering "
    "is the signature of an inference-level error, not of a weak effect. The regime variable "
    "has roughly five independent realisations — not 1,493.",
    tbl=table_view(
        ["Null hypothesis", "Units", "Draws", "Mean ΔR²", "p"],
        [["Across funds (naive)", "1,493", "1,000", "0.00114", "<b>0.045</b>"],
         ["Across vintages", "15", "1,000", "0.00194", "0.155"],
         ["Circular shift, episodes kept", "5", "61", "0.00220", "0.197"]],
        "Observed ΔR² = 0.00351 against a baseline R² of 0.1253. "
        "Only 50 distinct randomisations exist at the episode level, so the floor p is 0.020."))

CH_TIMELINE = figure(
    "Five episodes, not sixty-two quarters",
    "Three-state Gaussian HMM fitted on five principal components of ten software-market "
    "indicators, 2011 Q1 – 2026 Q2.",
    regime_timeline(),
    "Each fund's regime label is almost perfectly determined by the year it was raised — the "
    "mean dominant-regime share inside a deal entry year is 98%. Worse, the single expansion "
    "episode is also the most recent, so \"expansion\" and \"young fund\" are the same column "
    "with two names.",
    legend=f'<span><i class="s2"></i>Contraction</span>'
           f'<span><i class="nt"></i>Neutral</span>'
           f'<span><i class="s1"></i>Expansion</span>',
    tbl=table_view(["Episode", "Regime", "Quarters"],
                   [["2011 Q1 – Q2", "Neutral", "2"],
                    ["2011 Q3 – 2013 Q3", "Contraction", "9"],
                    ["2013 Q4 – 2019 Q4", "Neutral", "25"],
                    ["2020 Q1 – 2023 Q1", "Contraction", "13"],
                    ["2023 Q2 – 2026 Q2", "Expansion", "13"]],
                   "Mean episode length 12.4 quarters. Effective sample size ≈ 5."))

CH_MISS = figure(
    "Primary disclosures are 3–4× denser than what vendors sell",
    "Share of fund records missing a usable value, pooled across IRR, TVPI, DPI and RVPI.",
    hbar([("Primary pension disclosures", 15, "Parsed directly from LP board packets."),
           ("Commercial aggregators", 60,
            "Missingness exceeds 50% on granular accounting metrics.")],
         pct, maxv=75, colors=[S1, S2], lw=215),
    "Commercial databases are routinely treated as comprehensive. Empirically they are sparse "
    "snapshots with selective completeness — and the funds they omit are the smaller, "
    "fragmented, less marketable ones, which puts structural selection bias into every "
    "downstream study built on them.",
    legend=f'<span><i class="s1"></i>Our pipeline</span><span><i class="s2"></i>Vendors</span>',
    tbl=table_view(["Source", "Approx. missingness"],
                   [["Primary pension disclosures", "~15%"],
                    ["PitchBook / Preqin", "~50–60%"]],
                   "Rounded headline figures from the head-to-head comparison; "
                   "per-metric rates vary."))

CH_JGAP = figure(
    "The benchmark is smooth in a way the underlying funds are not",
    "Mean absolute gap between the Preqin median J-curve and the median built from primary "
    "disclosures, compared at common fund ages.",
    hbar([("Buyout", 0.142, "Shape correlation 0.81 across 28 common ages. "
                            "Preqin median is 46% smoother."),
          ("VC / growth", 0.288, "Shape correlation 0.87 across 21 common ages. "
                                 "Preqin median is 72% smoother.")],
         mult, maxv=0.40, colors=[S1, S3], lw=130),
    "Both strategies show the same broad lifecycle, so Preqin is not wrong — it is filtered. "
    "The early J-curve dip is shallower in the benchmark for both (0.921x vs 1.049x for buyout; "
    "0.880x vs 0.997x for VC), which is what survivorship looks like. VC is the sharper case: "
    "roughly twice the gap, and the benchmark damps mid-life volatility rather than merely "
    "lagging it.",
    legend=f'<span><i class="s1"></i>Buyout</span><span><i class="s3"></i>VC / growth</span>',
    tbl=table_view(["Metric", "Buyout", "VC / growth"],
                   [["Common age cells", "28", "21"],
                    ["Shape correlation", "0.81", "0.87"],
                    ["Mean absolute gap", "0.142x", "0.288x"],
                    ["Median absolute gap", "0.078x", "0.246x"],
                    ["Largest gap", "0.692x (age 27)", "0.937x (age 12)"],
                    ["Preqin roughness vs ours", "46% lower", "72% lower"]],
                   "Age cells require at least five funds in each source to enter the comparison."))

CH_SHARPE = figure(
    "The graph's value was a reference group, not extra information",
    "Gross Sharpe ratio of monthly long–short decile portfolios, U.S. stocks 2010–2024.",
    hbar([("Plain neural network", 0.69, "Annualised volatility 23%."),
          ("Ranked within 20 characteristic clusters", 1.03,
           "Same forecasts, ranked peer-relative. Volatility falls to 9%."),
          ("Peer-relative reversal signal", 1.38,
           "Prior-month return vs the firm's 20 nearest characteristic neighbours.")],
         p2, maxv=1.7, colors=[S1, S1, S3], lw=258),
    "Message passing between characteristic-similar firms did not beat a plain network that "
    "saw the same 64 characteristics. What did help was using those neighbours as a "
    "normalisation device: ranking the identical forecasts inside peer clusters cut volatility "
    "from 23% to 9% and lifted Sharpe from 0.69 to 1.03. The honest reading is that the "
    "characteristics already carry most of what the links would have transmitted.",
    legend=f'<span><i class="s1"></i>Forecast model</span>'
           f'<span><i class="s3"></i>Standalone signal</span>',
    tbl=table_view(["Specification", "Sharpe", "Annualised vol"],
                   [["Plain neural network", "0.69", "23%"],
                    ["Ranked within 20 clusters", "1.03", "9%"],
                    ["Peer-relative reversal", "1.38", "—"]],
                   "Gross of costs. The deployed GNN configuration earned 1.03 / 1.11 at "
                   "message-passing depths 1–2, net of 5–7 bps per trade."))

CH_SMOOTH = figure(
    "Deeper message passing failed by oversmoothing, not by overfitting",
    "Cross-sectional dispersion of model predictions, by message-passing depth.",
    hbar([("Depth 1", 0.0350, "Train and test return correlation both 0.081."),
          ("Depth 10", 0.0017, "Train and test return correlation still both 0.081.")],
         lambda v: f"{v:.4f}", maxv=0.046, colors=[S1, S2], lw=90),
    "A 20× collapse in prediction dispersion while train and test correlations stayed equal at "
    "0.081. If the deep model were overfitting, training correlation would have pulled away "
    "from test. It did not — the model simply averaged every firm towards the same number as "
    "information propagated across more hops.",
    legend=f'<span><i class="s1"></i>Depth 1</span><span><i class="s2"></i>Depth 10</span>')

CH_CITI = figure(
    "A static hedge ratio fails exactly when it is needed",
    "Variance reduction on the largest 5% of Italy–Germany spread-move days, out-of-sample.",
    hbar([("Static covariance-ratio hedge", 7,
           "The textbook minimum-variance ratio, estimated unconditionally."),
          ("Regime-aware hedge ratio", 9,
           "Updated for regime-specific vol, correlation, holding time and transition jumps.")],
         pct, maxv=14, colors=[S1, S1], lw=215),
    "Both numbers are small, and that is the result. Adding three Bund options to hedge the "
    "nonlinear exposure cut residual jump variance a further 13.6% across the 2018, 2020 and "
    "2022 crises — but 19% of initial risk stayed stubbornly BTP-specific. A spanning argument "
    "explains why: seven futures cannot cover the 20 transition shocks in a five-regime model, "
    "which needs at least 19 instruments for arbitrary jumps.",
    tbl=table_view(["Hedge", "Variance reduction"],
                   [["Static covariance ratio", "7%"],
                    ["Regime-aware ratio", "9%"],
                    ["+ three Bund options (residual jump variance)", "13.6%"],
                    ["Irreducible BTP-specific residual", "19% of initial risk"]],
                   "Out-of-sample, team tests. The third row is a different estimand "
                   "(residual jump variance) and is not directly comparable to the first two."))
print("charts built")

PHOTO = ('<picture>'
         '<source srcset="assets/me-440.webp 440w, assets/me.webp 880w" '
         'sizes="(max-width:860px) 100vw, 230px" type="image/webp">'
         '<img src="assets/me-880.jpg" width="880" height="904" '
         'alt="Venkata Sreenivaas Lingam, standing outdoors in a dark jacket" '
         'fetchpriority="high" decoding="async">'
         '</picture>')

# =========================================================================
# INDEX
# =========================================================================
INDEX_BODY = f"""
<section class="section" style="padding-top:26px">
  <div class="card">
    <div class="hero-content">
      <div class="avatar">{PHOTO}</div>
      <div>
        <p class="eyebrow">Quantitative research &amp; trading</p>
        <h1>Hi, I'm Venkata.</h1>
        <p class="lead">
          I'm a <b>Master of Financial Engineering</b> candidate at <b>UC Berkeley's Haas School
          of Business</b> (Class of 2027), and one of three managers of the Berkeley MFE
          Investment Fund. I'm <b>actively seeking full-time quantitative trading and
          quantitative research roles</b> starting in 2027.
        </p>
        <p class="lead">
          My work keeps circling the same question: <i>how much of an apparent edge survives
          once you count how many independent observations you actually have?</i> That has taken
          me through regime-switching models of private-equity returns, graph neural networks on
          the cross-section of stock returns, regime-aware sovereign bond hedging at Citi, and a
          pipeline that scrapes the private-markets data everyone assumed you had to pay for.
          Several of those projects ended in a negative result. I think those were the useful ones.
        </p>

        <div class="badges">
          <span class="badge"><span class="pill" aria-hidden="true"></span>
            <b>Open to full-time</b> · Trading &amp; Research · 2027</span>
          <span class="badge"><b>UC Berkeley MFE</b> ·
            <a class="link" href="https://mfe.haas.berkeley.edu/" target="_blank"
               rel="noopener">Haas</a></span>
          <span class="badge">Berkeley MFE Investment Fund · 1 of 3 managers</span>
        </div>

        <div class="cta-row">
          <a class="btn primary" href="projects.html">Explore the work</a>
          <a class="btn" href="research.html">Read the paper</a>
          <a class="btn" href="contact.html">Get in touch</a>
        </div>

        <div class="meta" aria-label="Core tools">
          <span>Python</span><span>PyTorch</span><span>C++</span><span>SQL</span>
          <span>pandas</span><span>statsmodels</span><span>LightGBM</span><span>JAX</span>
          <span>Lean</span><span>Git</span>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="grid">
    <div class="card col-7">
      <h2>What I actually do</h2>
      <p class="muted">Three habits show up in every project on this site.</p>
      <div class="callout">
        <h4>Count the independent observations first</h4>
        <p>A sixteen-year regime variable with five episodes has an effective sample size of
        five, no matter how many funds you stack underneath it. Most of the "significant"
        results I've chased died here, and finding out why was the contribution.</p>
      </div>
      <div class="callout find">
        <h4>Go to the primary source</h4>
        <p>Public pension funds publish their entire private-equity book quarterly, in PDFs,
        for free. Commercial vendors resell a smoothed, sparser version of it for six figures.
        Building the parser was the easy part; knowing it was worth building was the work.</p>
      </div>
      <div class="callout warn">
        <h4>Diagnose the failure, don't just report it</h4>
        <p>When the deep graph model stopped working, the useful finding wasn't that it stopped
        — it was that prediction dispersion collapsed 20× while train and test correlations
        stayed identical. That's oversmoothing, not overfitting, and it points at a different fix.</p>
      </div>
    </div>

    <div class="card col-5">
      <h2>Interests</h2>
      <p class="muted">
        Within markets: <b>regime inference and the statistics of small samples</b>,
        <b>the cross-section of returns</b>, <b>market microstructure</b>, and
        <b>private-markets data</b> — which is the rare corner where the bottleneck is still
        data engineering rather than modelling.
      </p>
      <p class="muted">
        Outside them: <b>horology</b> (mechanical movements are the original systems-thinking
        problem), <b>poker</b> — SIG qualifier, top 25%, and a Berkeley Poker Club member —
        <b>karting</b>, <b>weightlifting</b>, and <b>cricket</b>, which I played at state
        under-16 level.
      </p>
      <hr class="rule">
      <h3>Currently reading</h3>
      <p class="muted"><i>Thinking in Bets</i> — Annie Duke.</p>
      <p class="note">Decision quality and outcome quality are different things. Useful in a
      field where you find out whether you were right years after you had to commit — and where
      a good process can still lose.
      <a class="link" href="reading.html">See the full reading list →</a></p>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="numbers-h">
  <div class="card">
    <h2 id="numbers-h">The work in four numbers</h2>
    <p class="muted">One figure from each project below, so the scale is clear before you
      read the write-ups.</p>
    <div class="stats" style="margin-top:14px">
      <a class="stat" href="projects.html#prisma">
        <span class="p">Private-markets pipeline</span>
        <span class="n">1,493</span>
        <span class="l">private-equity and venture funds, parsed out of 462 public pension
          filings into a single queryable panel</span></a>
      <a class="stat" href="projects.html#gnn">
        <span class="p">Graph neural networks</span>
        <span class="n">~150k</span>
        <span class="l">out-of-sample firm-months of U.S. stocks, 2010&ndash;2024</span></a>
      <a class="stat" href="research.html">
        <span class="p">SSRN paper</span>
        <span class="n">1.03</span>
        <span class="l">Sharpe ratio once forecasts are ranked against peer firms &mdash;
          up from 0.69 without that step</span></a>
      <a class="stat" href="projects.html#gnn">
        <span class="p">Supply-chain graph</span>
        <span class="n">3,138</span>
        <span class="l">counterparties in the point-in-time graph I rebuilt, up from the
          original 940</span></a>
    </div>
  </div>
</section>

<section class="section">
  <div class="card">
    <h2>Selected work</h2>
    <p class="muted">Four projects, in reverse chronological order. Each one has a full
      write-up — including what didn't work.</p>

    <div class="grid" style="margin-top:14px">
      <div class="col-6"><div class="proj" style="height:100%">
        <p class="eyebrow">Citi · Oct–Dec 2026</p>
        <h3>Hedging BTPs with Bund futures across regimes</h3>
        <p class="muted">A minimum-variance hedge that works until Italy–Germany spreads jump.
        I proved the optimality conditions, then showed a spanning argument for why seven
        futures cannot span twenty transition shocks.</p>
        <div class="tags"><span class="tag">Fixed income</span><span class="tag">Regime jumps</span>
          <span class="tag">No-arbitrage</span></div>
        <div class="row"><a class="link" href="projects.html#citi">Read the write-up →</a></div>
      </div></div>

      <div class="col-6"><div class="proj" style="height:100%">
        <p class="eyebrow">UC Berkeley MFE · Aug–Oct 2026</p>
        <h3>Firms that look alike</h3>
        <p class="muted">Do characteristic-similar firms transmit return information? Mostly
        no — but they make an excellent reference group. Now on SSRN.</p>
        <div class="tags"><span class="tag">Graph neural networks</span>
          <span class="tag">Cross-section</span><span class="tag">PyTorch</span></div>
        <div class="row"><a class="link" href="projects.html#gnn">Read the write-up →</a>
          <a class="link" href="research.html">Paper →</a></div>
      </div></div>

      <div class="col-6"><div class="proj" style="height:100%">
        <p class="eyebrow">Prisma AI × Berkeley Haas MFE · 2026</p>
        <h3>The private-markets data nobody collected</h3>
        <p class="muted">90+ pension fund sites, seven consultant-specific PDF parsers, OCR for
        the scanned packets, and a Postgres panel that is 3–4× denser than what PitchBook and
        Preqin sell.</p>
        <div class="tags"><span class="tag">Data engineering</span><span class="tag">PDF/OCR</span>
          <span class="tag">Postgres</span><span class="tag">Benchmarking</span></div>
        <div class="row"><a class="link" href="projects.html#prisma">Read the write-up →</a></div>
      </div></div>

      <div class="col-6"><div class="proj" style="height:100%">
        <p class="eyebrow">Corsair Capital · Mar–Sep 2026</p>
        <h3>Software cycles and private-equity returns</h3>
        <p class="muted">A clean, significant result that dissolved under a permutation test
        respecting the data's real structure. Anatomy of how inference manufactures significance.</p>
        <div class="tags"><span class="tag">Hidden Markov models</span><span class="tag">PCA</span>
          <span class="tag">Permutation inference</span></div>
        <div class="row"><a class="link" href="projects.html#regimes">Read the write-up →</a></div>
      </div></div>
    </div>

    <div class="row"><a class="btn primary" href="projects.html">All projects, in depth</a></div>
  </div>
</section>

<section class="section">
  <div class="card">
    <h2>One figure, if you only look at one</h2>
    <p class="muted">This is the chart behind most of what I believe about research hygiene.</p>
    {CH_PVAL}
    <div class="row"><a class="link" href="projects.html#regimes">The full write-up →</a></div>
  </div>
</section>
"""
print("index body built")

# =========================================================================
# PROJECTS
# =========================================================================
PROJECTS_BODY = f"""
<section class="section">
  <h1>Projects</h1>
  <p class="lead">Six projects in depth — the question, the method, the number, and the part
  that didn't work. Several of these ended in negative results; those write-ups are the longest,
  because the interesting content is <i>why</i> the first answer was wrong.</p>
  <div class="tabs" role="tablist" aria-label="Filter projects by area">
    <button class="tab active" data-filter="all" role="tab" aria-selected="true">All</button>
    <button class="tab" data-filter="equities" role="tab" aria-selected="false">Equities</button>
    <button class="tab" data-filter="rates" role="tab" aria-selected="false">Rates</button>
    <button class="tab" data-filter="privatemkts" role="tab" aria-selected="false">Private markets</button>
    <button class="tab" data-filter="systems" role="tab" aria-selected="false">Systems</button>
  </div>
</section>

<!-- ============ CITI ============ -->
<article class="card proj" id="citi" data-cat="rates" style="margin-top:4px">
  <div class="proj-head">
    <div>
      <p class="eyebrow">Citi · UC Berkeley industry project · Supervisor: Peter Decrem</p>
      <h2 style="margin-bottom:4px">Hedging Italian sovereign risk with Bund futures,
        across regimes</h2>
    </div>
    <span class="proj-when">Oct – Dec 2026</span>
  </div>
  <p class="muted"><b>The question.</b> Italian government bonds (BTPs) are routinely hedged with
  German Bund futures on a covariance ratio estimated over a long window. That ratio is a
  minimum-variance solution to a problem that assumes the Italy–Germany relationship is stable.
  It is not. The whole value of the hedge is concentrated in the days when the spread jumps —
  and those are precisely the days the static estimate is wrong about.</p>

  <p class="muted"><b>What I did.</b> I formulated the hedge as a minimum-variance problem and
  proved its optimality conditions, then derived the jump-adjusted no-arbitrage drift for a
  regime-switching spread process. I modelled regime-specific volatility, correlation, expected
  holding time and transition jump sizes, and let the hedge ratio update on the inferred regime
  rather than on a single unconditional covariance.</p>

  {CH_CITI}

  <div class="callout warn">
    <h4>The result that mattered was a spanning argument</h4>
    <p>In a five-regime model there are 20 possible transition shocks. A hedger holding seven
    futures contracts has seven instruments. A spanning argument shows those seven cannot cover
    all 20 — hedging arbitrary jumps requires at least 19 instruments. This isn't a calibration
    problem that more data fixes; it's a rank problem. It explains the 19% of initial risk that
    stayed BTP-specific no matter what we did with futures.</p>
  </div>

  <p class="muted"><b>So we went nonlinear.</b> If the futures can't span the jump space, the
  remaining lever is convexity. I optimised a three-option Bund structure against the nonlinear
  jump exposure, which cut residual jump variance by a further 13.6% across the 2018, 2020 and
  2022 crisis episodes.</p>

  <p class="muted"><b>What I'd flag.</b> Going from 7% to 9% variance reduction is not a
  headline, and I'd rather present it as one honest number than dress it up. The genuinely
  transferable output is the spanning result: it tells a desk how many instruments a
  regime-aware hedge <i>needs</i> before anyone spends time estimating ratios.</p>

  <div class="tags">
    <span class="tag on">Minimum-variance hedging</span><span class="tag on">Regime switching</span>
    <span class="tag">Jump-adjusted no-arbitrage drift</span><span class="tag">Spanning arguments</span>
    <span class="tag">Option overlay</span><span class="tag">BTP–Bund</span>
  </div>
</article>

<!-- ============ GNN ============ -->
<article class="card proj" id="gnn" data-cat="equities">
  <div class="proj-head">
    <div>
      <p class="eyebrow">UC Berkeley MFE · with Aaryen Mehta and Tejas Girhe</p>
      <h2 style="margin-bottom:4px">Firms that look alike: graph neural networks and the
        cross-section of returns</h2>
    </div>
    <span class="proj-when">Aug – Oct 2026</span>
  </div>
  <p class="muted"><b>The question.</b> There's a well-established literature showing return
  predictability flows along economic links — customers and suppliers, shared analysts,
  technological relatedness. Graph neural networks are the natural way to exploit that. But
  observed links aren't available for every firm in every period. So: can you build the graph
  out of <i>firm characteristics</i> instead, and does that graph add anything over a plain
  neural network that already sees the same characteristics?</p>

  <p class="muted"><b>Setup.</b> U.S. stocks, 2010–2024, roughly 150,000 out-of-sample
  firm-months. 64 firm characteristics. TransformerConv models trained across six
  message-passing depths, against a characteristics-only neural network baseline. We tested both
  a simple nearest-neighbour graph and a learned graph.</p>

  {CH_SHARPE}

  <div class="callout find">
    <h4>The answer is a reframe, not a yes or a no</h4>
    <p>Message passing between characteristic-similar firms was <b>not consistently superior</b>
    to the plain network. The learned graph helped in one specification and not across others.
    The reason shows up in the raw data: the comovement between characteristic neighbours is
    largely <i>accounted for by the characteristics that defined them</i>, so there is little
    residual information left for the graph to transmit. Characteristic neighbours work better
    as a <b>reference group</b> than as a channel.</p>
    <p style="margin-top:8px">Ranking the same forecasts within 20 characteristic clusters took
    annualised volatility from 23% to 9% and the Sharpe ratio from 0.69 to 1.03 — no new
    information, just a better denominator. And a standalone peer-relative reversal signal (a
    firm's prior-month return against its 20 nearest neighbours) ran a gross Sharpe of 1.38,
    concentrated in the short leg and in small firms.</p>
  </div>

  {CH_SMOOTH}

  <p class="muted"><b>My contributions specifically.</b> I fixed excess-return targeting and
  look-ahead bias in the Ridge/LASSO baselines; expanded the point-in-time graph from 940 to
  3,138 counterparties and built an SEC filings pipeline that added 14,339 edge rows; ran the
  six-benchmark spanning tests (incremental signal at four of six depths); and diagnosed the
  deeper-model failure as oversmoothing rather than overfitting.</p>

  <div class="callout">
    <h4>A reproduction note worth more than the result</h4>
    <p>The lead–lag computation is a float32 mean, and exact ties at the decile cut made results
    platform-dependent — the same code gave different deciles on different machines. Sorting
    each firm's neighbours by similarity before averaging reproduces the published series
    bit-exactly. Separately, 10 of the 64 characteristics turned out to be constant within every
    month, so only 54 actually vary cross-sectionally. Neither fact changes the headline;
    both change how much you should trust a single run.</p>
  </div>

  <div class="row">
    <a class="btn primary sm" href="research.html#firms-that-look-alike">Paper &amp; abstract</a>
    <a class="btn sm" href="{SSRN}" target="_blank" rel="noopener">View on SSRN</a>
    <a class="btn sm" href="assets/firms-that-look-alike-ssrn-7661378.pdf"
       target="_blank" rel="noopener">Download PDF</a>
  </div>
  <div class="tags">
    <span class="tag on">Graph neural networks</span><span class="tag on">TransformerConv</span>
    <span class="tag">PyTorch</span><span class="tag">Cross-sectional returns</span>
    <span class="tag">Oversmoothing</span><span class="tag">Look-ahead bias</span>
    <span class="tag">CRSP / WRDS</span>
  </div>
</article>

<!-- ============ PRISMA ============ -->
<article class="card proj" id="prisma" data-cat="privatemkts">
  <div class="proj-head">
    <div>
      <p class="eyebrow">Prisma AI × UC Berkeley Haas MFE</p>
      <h2 style="margin-bottom:4px">The private-markets dataset that was public the whole time</h2>
    </div>
    <span class="proj-when">2026</span>
  </div>
  <p class="muted"><b>The observation.</b> Every U.S. public pension fund posts its complete
  private-equity book every quarter. Fund name, vintage, commitment, paid-in, distributions,
  NAV, DPI, TVPI, net IRR — all of it, in board meeting materials, free to anyone. Across 28+
  funds that's a $4T+ addressable universe of LP-reported performance. PitchBook and Preqin
  charge $20K–$250K a year for a <i>worse</i> version of the same information.</p>

  <div class="callout">
    <h4>Why nobody had built it</h4>
    <p>Three barriers, none of them technical. The data is fragmented across 90+ sites, each
    with its own format and schedule — no API, no bulk export, no single source. It's
    PDF-native rather than data-native, living inside board packets as tables. And the toolset
    to extract it (Python, pdfplumber, regex, Tesseract) has been free for a decade. The scarce
    resource was never the engineering. It was recognising that LP-reported net IRR is
    categorically more accurate than anything a vendor aggregates from GP self-reports.</p>
  </div>

  <h3 style="margin-top:20px">What unsupervised LLMs got wrong</h3>
  <p class="muted">We started where everyone starts: paste the PDF, ask the model, get the IRR.
  It does not work, and no amount of prompt engineering fixed it. Three distinct failure modes:</p>
  <ul class="list">
    <li><b>Tables are not text.</b> pdfplumber reads left-to-right across the page, so a
      four-column PE schedule arrives as garbled interleaved rows. A language model cannot
      reconstruct the original grid from a character stream.</li>
    <li><b>Format heterogeneity.</b> Verus reports differ fundamentally from Callan, NEPC,
      Aksia and StepStone — different column order, header names and footnote placement.</li>
    <li><b>Hallucination at scale.</b> On long board packets the models invented IRR values,
      swapped DPI and TVPI, and pinned performance to the wrong vintage year. No warning, no
      error flag. Just wrong numbers that look right — the worst possible failure mode for a
      dataset you intend to run regressions on.</li>
  </ul>

  <p class="muted"><b>The fix: deterministic code where it matters, intelligence where it
  scales.</b> Seven consultant-specific parsers (Verus, Callan, NEPC, Aksia, Meketa, StepStone,
  AON), bounding-box extraction rather than linear text, and a regex normalisation layer mapping
  raw text into a nine-field schema per fund record. Scanned packets with no text layer get
  rasterised and run through Tesseract OCR, then re-enter the same pipeline. Footnotes bleeding
  into the last fund row — corrupting NAV and DPI with disclaimer text — were killed by a
  two-pass scan that detects the footnote boundary via font-size drop and clips above it. And
  number chaos got its own layer: <code>(14.2)</code> became <code>-14.2</code>, currency and
  percent symbols stripped, and <code>N/A</code>, an em dash, an empty string and a null
  collapsed into one NULL. Whatever survived that and still broke got a hardcoded rule.</p>

  <p class="muted">The output lands in Postgres behind a FastAPI backend, with a Retool UI as
  the human QA and validation layer. The schema is modelled on PCRI — the Private Capital
  Research Institute dataset that Harvard, Stanford and Yale researchers use as the academic
  gold standard — which is roughly 4,000 funds from 40 LP contributors, updated infrequently,
  academic access only. Same schema. More funds. Better sourcing. Fully automated.</p>

  <h3 style="margin-top:22px">Then we benchmarked it against what people pay for</h3>
  <p class="muted">The interesting half of the project wasn't the pipeline — it was the
  head-to-head against PitchBook and Preqin on coverage density, sparsity, accounting
  consistency and reporting fidelity.</p>

  {CH_MISS}

  <div class="callout warn">
    <h4>Vendor records fail arithmetic that cannot fail</h4>
    <p>TVPI = DPI + RVPI. That's an accounting identity, not an empirical claim. Vendor records
    violate it — stale fields, asynchronous updates and reconciliation errors produce fund rows
    that look coherent and are not. We also found "Frankenstein" records: semantically identical
    funds that the vendor failed to reconcile, so a single row is stitched together from
    reporting cycles months apart. Aggregate correlation with primary data stays high, which
    is exactly what makes this dangerous — the distortion is concentrated at the fund level,
    in unrealised valuations, which is where capital allocation decisions actually happen.</p>
  </div>

  <h3 style="margin-top:22px">Making the two sources comparable at all</h3>
  <p class="muted">Before you can compare, you have to fix the clock. PE funds report at
  different frequencies (quarterly, semiannual, effectively annual) with different lags, so two
  values observed on different dates may describe completely different points in a fund's life.
  A 1.2x TVPI at age 2 is not a 1.2x TVPI at age 6. Comparing unmatched timing mistakes a
  reporting artifact for performance. So every dated observation gets mapped onto a fund-age
  axis (report year minus vintage year), medians are taken per age cell, and only cells with at
  least five funds in <i>each</i> source enter the comparison — 651 buyout observations from 429
  funds and 338 VC observations from 219 funds on our side, against 2,904 and 3,476 Preqin
  observations respectively.</p>

  {CH_JGAP}

  <p class="muted"><b>Fund paths versus snapshots.</b> The second test was fund-level rather
  than aggregate. Our data often carries repeated dated marks for the same fund; Preqin
  typically contributes one. So the fair comparison isn't curve-versus-curve, it's
  path-versus-point: fit a cubic spline to our observations only, evaluate it at Preqin's single
  snapshot date, and compare. Of 53 modelled fund paths (31 buyout, 22 VC with at least four
  marks), 16 cases had the Preqin date falling strictly <i>inside</i> our observation window —
  true interpolation, the cleanest possible evidence. Those residuals were small: mean absolute
  0.040x, median 0.020x, interquartile range −0.023x to +0.002x. Extrapolation cases (37 of
  them) were reported separately, at 0.093x.</p>

  <div class="callout find">
    <h4>The limitation became the finding</h4>
    <p>Preqin's fund-level snapshots are not systematically wrong — on clean same-date
    comparisons they're close. What they are is <b>sparse as a time series</b>. One dated point
    per fund means you cannot build a Preqin fund-level trajectory at all. So the honest
    conclusion isn't "our data is more accurate"; it's that the two sources support different
    questions. Ours supports trajectories; Preqin supports checkpoints. Downstream analytics
    that need movement over time — spline interpolation, J-curve modelling — structurally
    require primary data to function.</p>
  </div>

  <div class="stats" style="margin-top:16px">
    <div class="stat"><div class="n">90+</div><div class="l">Pension fund sites in scope</div></div>
    <div class="stat"><div class="n">7</div><div class="l">Consultant-specific parsers</div></div>
    <div class="stat"><div class="n">62%</div><div class="l">Universe coverage achieved</div></div>
    <div class="stat"><div class="n">30–60d</div><div class="l">Freshness post quarter-end,
      vs a 2–3 quarter vendor lag</div></div>
  </div>

  <p class="note" style="margin-top:16px">Built in the first semester of the MFE programme,
  with free tools, alongside a full course load.</p>

  <div class="tags">
    <span class="tag on">Postgres</span><span class="tag on">FastAPI</span>
    <span class="tag">pdfplumber</span><span class="tag">PyMuPDF</span>
    <span class="tag">pytesseract OCR</span><span class="tag">Retool</span>
    <span class="tag">Cubic splines</span><span class="tag">Benchmark validation</span>
  </div>
</article>

<!-- ============ REGIMES ============ -->
<article class="card proj" id="regimes" data-cat="privatemkts">
  <div class="proj-head">
    <div>
      <p class="eyebrow">Corsair Capital · UC Berkeley MFE industry project · with Aaryen Mehta</p>
      <h2 style="margin-bottom:4px">Software-cycle regimes and private-equity returns —
        anatomy of a result that wasn't there</h2>
    </div>
    <span class="proj-when">Mar – Sep 2026</span>
  </div>
  <p class="muted"><b>The question.</b> Do software-market conditions at the time a PE fund
  invests predict the fund's eventual TVPI? It's a natural question with an obvious research
  design, and the obvious research design gives you a significant answer. It took most of the
  project to work out that the answer was an artifact.</p>

  <p class="muted"><b>Construction.</b> A 1,493-fund panel built from 462 pension filings. Ten
  correlated software-market indicators reduced by PCA to five components explaining 92.1% of
  variance. A three-state Gaussian hidden Markov model selected by BIC, classifying each quarter
  from 2011 Q1 to 2026 Q2 as contraction, neutral or expansion. Then: regress winsorised TVPI on
  fund age, age², and regime dummies, and test whether the regime dummies add explanatory power.</p>

  {CH_TIMELINE}

  <div class="callout warn">
    <h4>Sixty-two quarters is not sixty-two observations</h4>
    <p>The HMM produces five contiguous episodes with a mean length of 12.4 quarters. Regime is
    therefore almost a relabelling of calendar time — the mean dominant-regime share inside a
    deal entry year is 98%. And because the single expansion episode is also the most recent
    one, "invested during an expansion" and "is a young fund" are structurally confounded.</p>
    <p style="margin-top:8px">You can see the confound directly in the exit rates. Deal exit
    rate falls monotonically from 33.0% for 2014 entries to 0.2% for 2024 entries — that's pure
    exposure time. Sliced by regime it reads 20.6% neutral, 4.2% contraction, 0.4% expansion.
    Same column, relabelled.</p>
  </div>

  <h3 style="margin-top:20px">The contradiction that forced the issue</h3>
  <p class="muted">Two inference procedures on the same 15 vintage clusters disagreed. Vintage-
  <i>clustered</i> standard errors said significant (p = 0.011 / 0.023) and described themselves
  as the honest inference. Vintage-<i>permutation</i> on the identical grouping said null
  (p = 0.141). Both can't be right.</p>
  <p class="muted">Clustered sandwich standard errors are asymptotic in the <i>number of
  clusters</i>, not the number of observations. With G = 15 they over-reject — this is the
  Bertrand–Duflo–Mullainathan result, and the Cameron–Gelbach–Miller rule of thumb wants G in
  the 30–50 range before you trust them. The permutation test makes no such asymptotic
  assumption. The permutation test wins.</p>

  <h3 style="margin-top:20px">So I built a ladder of nulls</h3>
  <p class="muted">The cleanest way to show what's happening is to hold the estimand fixed —
  ΔR² of the regime dummies over <code>tvpi_w ~ age + age²</code>, observed value 0.00351
  against a baseline R² of 0.1253 — and vary only what the null hypothesis is permitted to
  permute.</p>

  {CH_PVAL}

  <div class="callout find">
    <h4>Monotone p is a diagnostic</h4>
    <p>When p climbs steadily as the null respects more of the data's real dependence structure,
    you are not looking at a weak effect. You are looking at an inference-level error: the
    earlier, lower p-values were borrowing significance from units that were never independent.
    The episode-level null is 1.7× wider than the naive one. And there are only 50 distinct
    randomisations available at that level, which puts a hard floor of p = 0.020 on anything
    this design can ever detect.</p>
  </div>

  <p class="muted"><b>What the deal-level analysis added.</b> A parallel 73,806-company Preqin
  deal panel gave p &lt; 0.0001, which looks decisive and isn't: it's a Moulton problem stacked
  on the exposure-time artifact above. I'd also flag that the fund-level universe (LP
  disclosures) and the deal-level universe (the full Preqin tech universe) were never matched to
  each other — they answer different questions about different populations, and the write-up
  needs to say so rather than let the reader assume continuity.</p>

  <div class="callout">
    <h4>What would actually fix the design</h4>
    <p>Lengthen the estimation window back to 1995, which takes the episode count from ~5 to
    ~15 and the floor p from 0.020 to roughly 0.007. Break the age–regime confound by
    restricting to funds aged 8+ or switching the outcome to DPI on realised capital. Match the
    Preqin deals to the LP fund universe so the two analyses describe one population. And refit
    the HMM on expanding windows with filtered rather than smoothed posteriors — the current fit
    uses the full window, which is an in-sample association and biases <i>towards</i> finding
    an effect, making the null result stronger rather than weaker.</p>
  </div>

  <p class="muted"><b>The contribution, stated honestly.</b> The deliverable is the negative
  result plus its anatomy: a regime variable estimated on a sixteen-year window has roughly five
  independent realisations, and conducting inference at the fund, vintage or deal level
  manufactures significance that the data does not contain. That is a reusable warning about an
  entire class of regime-conditioning studies, which I'd argue is worth more than a p-value
  of 0.045 would have been.</p>

  <div class="row">
    <a class="btn sm" href="https://claude.ai/artifact/TczaJEM5rhagbnLZYqvDf6"
       target="_blank" rel="noopener">Interactive walkthrough</a>
  </div>
  <div class="tags">
    <span class="tag on">Hidden Markov models</span><span class="tag on">Permutation inference</span>
    <span class="tag">PCA</span><span class="tag">Clustered standard errors</span>
    <span class="tag">Circular-shift tests</span><span class="tag">Survival analysis</span>
    <span class="tag">PostgreSQL</span>
  </div>
</article>

<!-- ============ ALLSHIFTS ============ -->
<article class="card proj" id="allshifts" data-cat="systems">
  <div class="proj-head">
    <div>
      <p class="eyebrow">AllShifts · Data Engineering &amp; Revenue Analyst</p>
      <h2 style="margin-bottom:4px">Forecasting and credit systems at a healthcare staffing
        marketplace</h2>
    </div>
    <span class="proj-when">Oct 2023 – Feb 2026</span>
  </div>
  <p class="muted">Two and a half years of turning messy operational data into things the
  business actually ran on. Less glamorous than research, and the single best training I've had
  in the gap between a model that validates and a model that survives contact with users.</p>
  <ul class="list">
    <li><b>Stochastic pricing optimiser.</b> Facility-by-nurse-type ARIMA demand scenarios
      combined with seasonal rate fill curves, maximising expected fills subject to contract and
      margin constraints. Forecasts validated against 2024–2025 actuals.</li>
    <li><b>Credit risk model.</b> Logistic regression on 6- and 12-month delinquency and
      billing-to-payment histories. Validated on 400 clients, deployed to 1,700+. Post-rollout,
      defaults fell 17% and payments arrived two weeks sooner.</li>
    <li><b>Cash collection forecasting.</b> LightGBM on billing lags, accounts-receivable aging
      cohorts and calendar effects, predicting daily collections one to three weeks out at
      4.8% out-of-sample MAPE.</li>
    <li><b>Revenue-risk monitor.</b> A four-week rolling view using STL to strip seasonality
      and LightGBM to flag client-level declines in orders, billings and payments before they
      showed up in the headline number.</li>
  </ul>
  <div class="stats" style="margin-top:14px">
    <div class="stat"><div class="n">−17%</div><div class="l">Client defaults after
      credit-model rollout</div></div>
    <div class="stat"><div class="n">2 wks</div><div class="l">Faster payment arrival</div></div>
    <div class="stat"><div class="n">4.8%</div><div class="l">Out-of-sample MAPE on daily
      cash collections</div></div>
    <div class="stat"><div class="n">1,700+</div><div class="l">Clients scored in
      production</div></div>
  </div>
  <div class="tags">
    <span class="tag on">LightGBM</span><span class="tag on">ARIMA</span><span class="tag">STL</span>
    <span class="tag">Logistic regression</span><span class="tag">Stochastic optimisation</span>
    <span class="tag">SQL</span>
  </div>
</article>

<!-- ============ POKER ============ -->
<article class="card proj" id="poker" data-cat="systems">
  <div class="proj-head">
    <div><p class="eyebrow">Side project</p>
      <h2 style="margin-bottom:4px">Poker equity calculator</h2></div>
    <span class="proj-when">Ongoing</span>
  </div>
  <p class="muted">A Streamlit Texas Hold'em equity calculator built on Monte Carlo simulation
  via <code>treys</code>. It models opponents as random hands, returns equity against that
  range, and converts it into a pot-odds / expected-value call-or-fold recommendation. Modelling
  opponents as uniformly random is the obvious limitation and the obvious next thing to fix —
  range construction is where the real work is.</p>
  <div class="row">
    <a class="btn sm" href="https://github.com/lvsreenivaas/Poker-Equity-Calculator"
       target="_blank" rel="noopener">Repository</a>
  </div>
  <div class="tags"><span class="tag on">Monte Carlo</span><span class="tag">Streamlit</span>
    <span class="tag">Pot odds / EV</span><span class="tag">treys</span></div>
</article>

<section class="section">
  <div class="card">
    <h2>Related</h2>
    <p class="muted">The graph neural network project is now a working paper —
      <a class="link" href="research.html">read the abstract and download the PDF</a>. For the
      full employment history and coursework, see the
      <a class="link" href="{RESUME}" target="_blank" rel="noopener">résumé</a>. If any of this
      is relevant to a role you're hiring for,
      <a class="link" href="contact.html">get in touch</a>.</p>
  </div>
</section>

<script>
  (function () {{
    var tabs = Array.prototype.slice.call(document.querySelectorAll(".tab"));
    var cards = Array.prototype.slice.call(document.querySelectorAll("article.proj"));
    tabs.forEach(function (t) {{
      t.addEventListener("click", function () {{
        var f = t.dataset.filter;
        tabs.forEach(function (x) {{
          var on = x === t;
          x.classList.toggle("active", on);
          x.setAttribute("aria-selected", on ? "true" : "false");
        }});
        cards.forEach(function (c) {{
          c.hidden = !(f === "all" || c.dataset.cat === f);
        }});
      }});
    }});
  }})();
</script>
"""
print("projects body built")

# =========================================================================
# RESEARCH
# =========================================================================
RESEARCH_BODY = f"""
<section class="section">
  <h1>Research</h1>
  <p class="lead">Working papers and research output. Everything here is open access.</p>
</section>

<article class="card" id="firms-that-look-alike" style="margin-top:4px">
  <p class="eyebrow">Working paper · SSRN · October 2026</p>
  <h2 style="font-size:25px;line-height:1.25;margin-bottom:10px">
    Firms That Look Alike: Characteristic Graphs and the Cross-Section of Stock Returns</h2>
  <p class="muted" style="margin-bottom:6px">
    Aaryen Milan Mehta · Tejas Girhe · <b>Venkata Sreenivaas Lingam</b><br>
    <span class="note">UC Berkeley, Haas School of Business</span></p>

  <div class="row" style="margin-top:16px">
    <a class="btn primary sm" href="{SSRN}" target="_blank" rel="noopener">View on SSRN</a>
    <a class="btn sm" href="assets/firms-that-look-alike-ssrn-7661378.pdf"
       target="_blank" rel="noopener">Download PDF</a>
    <a class="btn sm" href="projects.html#gnn">Project write-up</a>
  </div>

  <hr class="rule">
  <h3>Abstract</h3>
  <p class="muted">Graph neural networks (GNNs) forecast stock returns by passing information
  between economically or statistically linked firms. We ask whether links inferred from 64 firm
  characteristics can improve return forecasts relative to a neural network that uses the same
  characteristics without a graph. In U.S. stocks from 2010 to 2024, a simple neighbor graph is
  not consistently superior to a basic neural network, and a learned neighbor graph results in a
  positive annual-return difference for one specification, but not consistently across a range
  of specifications. This is mirrored in the raw comovement between characteristic neighbours,
  with the characteristics used to define them accounting for much of the information in the raw
  data, leaving less information to be leveraged by graph-based message passing. This may be
  because characteristic-based neighbours are more likely to serve as a reference group than as
  a source of extra information: in the reported specification, the annualised volatility of the
  plain network drops from 23% to 9%, while the Sharpe ratio increases from 0.69 to 1.03 when
  ranking the forecasts within 20 characteristic clusters. A strategy using the previous month's
  return of a firm compared with its 20 closest characteristic-based neighbours shows
  peer-relative return reversal with a gross Sharpe ratio of 1.38, and the signal is focused in
  the short leg and small firms.</p>

  <p class="note"><b>Keywords:</b> graph neural networks, firm similarity, return predictability,
  short-term reversal, look-ahead bias. &nbsp;·&nbsp; <b>JEL:</b> C45, C55, G11, G12, G14.</p>

  <hr class="rule">
  <h3>The headline figure</h3>
  {CH_SHARPE}

  <hr class="rule">
  <h3>What I contributed</h3>
  <ul class="list">
    <li>Fixed excess-return targeting and look-ahead bias in the Ridge/LASSO baselines.</li>
    <li>Expanded the point-in-time counterparty graph from 940 to 3,138 firms, and built an SEC
      filings pipeline contributing 14,339 edge rows.</li>
    <li>Ran six-benchmark spanning tests across message-passing depths.</li>
    <li>Diagnosed the deep-model failure as oversmoothing rather than overfitting — prediction
      dispersion collapsed from 0.035 at depth one to 0.0017 at depth ten while train and test
      return correlations stayed equal at 0.081.</li>
  </ul>
  <p class="note" style="margin-top:14px">For the longer methodological discussion, including the
  float32 tie-breaking issue that made decile cuts platform-dependent, see the
  <a class="link" href="projects.html#gnn">project write-up</a>.</p>
</article>

<section class="section">
  <div class="card">
    <h2>In progress</h2>
    <p class="muted">Robustness work on the paper is ongoing — in particular, re-running the
    within-cluster depth-1 comparison across multiple random seeds, where the measured gain is
    considerably less stable than a single run suggests. I'd rather publish the corrected
    version than the flattering one.</p>
    <p class="muted">Other active threads: extending the private-markets panel backwards to
    lengthen the regime estimation window (see the
    <a class="link" href="projects.html#regimes">regime project</a> for why that matters), and
    continued work on statistical arbitrage and volatility research.</p>
  </div>
</section>
"""

# =========================================================================
# READING
# =========================================================================
PREV = ["<i>The Misbehavior of Markets</i> — Benoit B. Mandelbrot with Richard L. Hudson",
        "<i>Deep Work</i> — Cal Newport",
        "<i>Surely You're Joking, Mr. Feynman!</i> — Richard P. Feynman",
        "<i>Options, Futures, and Other Derivatives</i> — John C. Hull",
        "<i>Principles: Life and Work</i> — Ray Dalio",
        "<i>The Man Who Solved the Market</i> — Gregory Zuckerman",
        "<i>The Man Who Loved Only Numbers</i> — Paul Hoffman",
        "<i>Scale</i> — Geoffrey West",
        "<i>Nudge</i> — Richard H. Thaler &amp; Cass R. Sunstein",
        "<i>Steve Jobs</i> — Walter Isaacson",
        "<i>Elon Musk</i> — Walter Isaacson",
        "<i>More Money Than God</i> — Sebastian Mallaby",
        "<i>The Quants</i> — Scott Patterson",
        "<i>Business Cycles and Equilibrium</i> — Fischer Black",
        "<i>Applied Econometric Time Series</i> — Walter Enders",
        "<i>Algorithmic Trading</i> — Ernest P. Chan",
        "<i>The Coddling of the American Mind</i> — Greg Lukianoff &amp; Jonathan Haidt"]

READING_BODY = f"""
<section class="section">
  <h1>Reading</h1>
  <p class="lead">Markets, probability, and decision-making under uncertainty — plus whatever
  else holds my attention. Recommendations genuinely welcome.</p>
</section>

<section class="section">
  <div class="grid">
    <div class="card col-5">
      <p class="eyebrow">Currently reading</p>
      <h2 style="font-size:23px">Thinking in Bets</h2>
      <p class="muted" style="margin-bottom:14px">Annie Duke</p>
      <p class="muted">Duke's central separation is between <b>decision quality</b> and
      <b>outcome quality</b> — a good decision can lose and a terrible one can win, and
      conflating the two ("resulting") is how people learn the wrong lesson from their own track
      record.</p>
      <p class="muted">It lands hard in quantitative research, where feedback is slow, noisy and
      arrives long after you had to commit. Most of the projects on this site are cases where
      the outcome looked fine and the decision process was the thing that needed auditing — a
      significant p-value from a null that was never defensible is a won hand played badly.</p>
      <div class="row"><a class="link" href="projects.html#regimes">The project this book
        describes →</a></div>
    </div>

    <div class="card col-7">
      <h2>Previously read</h2>
      <p class="note">Roughly in the order I got to them.</p>
      <ul class="list">{"".join(f"<li>{b}</li>" for b in PREV)}</ul>
      <hr class="rule">
      <h3>Suggest one</h3>
      <p class="muted">If you think I'd like something in markets, probability, macro, or
      decision-making under uncertainty — <a class="link" href="contact.html">send it my
      way</a>. I read most of what people send.</p>
    </div>
  </div>
</section>
"""

# =========================================================================
# CONTACT
# =========================================================================
CONTACT_BODY = f"""
<section class="section">
  <h1>Get in touch</h1>
  <p class="lead">I'm actively looking for <b>full-time quantitative trading and quantitative
  research roles</b> starting in 2027, and I'm always happy to talk about any of the work on
  this site — especially if you think I got something wrong.</p>
</section>

<section class="section">
  <div class="grid">
    <div class="card col-7">
      <h2>Send a message</h2>
      <form action="{FORMSPREE}" method="POST" id="contactForm">
        <div class="field">
          <label for="cname">Name</label>
          <input id="cname" type="text" name="name" autocomplete="name" required
                 maxlength="120" placeholder="Your name">
        </div>
        <div class="field">
          <label for="cemail">Email</label>
          <input id="cemail" type="email" name="email" autocomplete="email" required
                 maxlength="200" placeholder="you@company.com">
        </div>
        <div class="field">
          <label for="csubj">Subject</label>
          <input id="csubj" type="text" name="_subject" maxlength="160"
                 placeholder="What's this about?">
        </div>
        <div class="field">
          <label for="cmsg">Message</label>
          <textarea id="cmsg" name="message" required maxlength="4000"
                    placeholder="Say as much or as little as you like."></textarea>
        </div>
        <!-- honeypot: bots fill this, humans never see it -->
        <div class="hp" aria-hidden="true">
          <label for="company_website">Leave this empty</label>
          <input id="company_website" type="text" name="_gotcha" tabindex="-1"
                 autocomplete="off">
        </div>
        <button class="btn primary" type="submit">Send message</button>
        <p class="formnote" id="formStatus" role="status" aria-live="polite"></p>
        <p class="formnote">Submissions are handled by Formspree and forwarded to my inbox.
        See the <a class="link" href="privacy.html">privacy policy</a> for what that means for
        your data. Prefer email? <a class="link" href="mailto:{EMAIL}">{EMAIL}</a>.</p>
      </form>
    </div>

    <div class="card col-5">
      <h2>Direct</h2>
      <div class="cta-row" style="margin-top:4px">
        <a class="btn" href="mailto:{EMAIL}">Email</a>
        <a class="btn" href="{LI}" target="_blank" rel="me noopener">LinkedIn</a>
        <a class="btn" href="{GH}" target="_blank" rel="me noopener">GitHub</a>
      </div>
      <hr class="rule">
      <h3>For recruiters</h3>
      <ul class="list">
        <li><b>Seeking:</b> full-time quantitative trading and quantitative research,
          starting 2027</li>
        <li><b>Graduating:</b> March 2027, UC Berkeley MFE</li>
        <li><b>Work authorisation:</b> USA F-1 OPT / STEM OPT eligible · cap-exempt H-1B</li>
        <li><b>Based:</b> Berkeley, CA — open to relocating</li>
        <li><b>Résumé:</b> <a class="link" href="{RESUME}" target="_blank"
          rel="noopener">PDF</a></li>
      </ul>
      <hr class="rule">
      <h3>Elsewhere on this site</h3>
      <p class="muted"><a class="link" href="projects.html">Projects</a> ·
        <a class="link" href="research.html">Research</a> ·
        <a class="link" href="reading.html">Reading</a></p>
    </div>
  </div>
</section>

<script>
  (function () {{
    var f = document.getElementById("contactForm");
    var s = document.getElementById("formStatus");
    if (!f) return;
    if (f.action.indexOf("PASTE_FORM_ID") !== -1) {{
      s.textContent = "Form endpoint not configured yet \\u2014 please email directly.";
      return;
    }}
    f.addEventListener("submit", function (e) {{
      e.preventDefault();
      s.textContent = "Sending\\u2026";
      fetch(f.action, {{
        method: "POST", body: new FormData(f), headers: {{ Accept: "application/json" }}
      }}).then(function (r) {{
        if (r.ok) {{ f.reset(); s.textContent = "Thanks \\u2014 message sent. I'll reply soon."; }}
        else {{ s.textContent = "Something went wrong. Please email me directly."; }}
      }}).catch(function () {{
        s.textContent = "Network error. Please email me directly.";
      }});
    }});
  }})();
</script>
"""
print("research/reading/contact built")

# =========================================================================
# PRIVACY
# =========================================================================
PRIVACY_BODY = f"""
<section class="section">
  <h1>Privacy policy</h1>
  <p class="lead">Short version: this is a personal site. I collect as little as possible, I
  don't sell anything, and the only data that reaches me is what you choose to send.</p>
  <p class="note">Last updated: 24 October 2026.</p>
</section>

<section class="section">
  <div class="card prose">
    <h2>Who runs this site</h2>
    <p>This site is operated by {NAME} as a personal portfolio. You can reach me at
      <a class="link" href="mailto:{EMAIL}">{EMAIL}</a> about anything on this page.</p>

    <h2>Hosting</h2>
    <p>The site is static HTML hosted on <b>GitHub Pages</b> (GitHub, Inc.). GitHub records
    standard server access logs, which include visitor IP addresses, for security and abuse
    prevention. I have no access to those logs and cannot retrieve, export or delete them. See
    GitHub's <a class="link" href="https://docs.github.com/site-policy/privacy-policies/github-privacy-statement"
    target="_blank" rel="noopener">privacy statement</a>.</p>

    <h2>Analytics</h2>
    <p>This site uses <b>Google Analytics 4</b> to count visits and see which pages are read.
    IP anonymisation is enabled, so your address is truncated before storage. Analytics tells me
    aggregate things — which write-ups get read, roughly where readers are — and nothing that
    identifies you personally.</p>
    <p>If you'd rather not be counted, any of these works: browser "Do Not Track" or
    tracking-protection settings, a content blocker, or Google's
    <a class="link" href="https://tools.google.com/dlpage/gaoptout" target="_blank"
    rel="noopener">opt-out browser add-on</a>. Nothing on this site is gated behind analytics,
    so blocking it costs you nothing.</p>
    <p class="note">Analytics is loaded only when a measurement ID is configured. If none is
    set, no analytics script loads and no analytics cookies are written.</p>

    <h2>Cookies</h2>
    <p>I set no cookies of my own. Google Analytics, when active, sets its standard first-party
    cookies (<code>_ga</code> and related) to distinguish repeat visits. There is no
    advertising, no remarketing, no cross-site tracking, and nothing is shared with data
    brokers.</p>

    <h2>The contact form</h2>
    <p>The form on the <a class="link" href="contact.html">contact page</a> is processed by
    <b>Formspree</b>, which receives what you type — your name, email address, subject and
    message — and forwards it to my inbox. I use it to reply to you, and for nothing else. I
    don't add you to a mailing list, because I don't have one.</p>
    <p>Formspree's handling of submissions is governed by its own
    <a class="link" href="https://formspree.io/legal/privacy-policy/" target="_blank"
    rel="noopener">privacy policy</a>. If you'd rather skip the third party entirely, email me
    directly at <a class="link" href="mailto:{EMAIL}">{EMAIL}</a>.</p>
    <p>Messages stay in my email. I'll delete yours on request — just ask.</p>

    <h2>External links and embeds</h2>
    <p>Links to GitHub, LinkedIn, SSRN and similar sites take you to services with their own
    privacy practices, which I don't control. This site embeds no third-party fonts, no social
    widgets and no trackers beyond the analytics described above; every asset other than the
    analytics script is served from this domain.</p>

    <h2>Your rights</h2>
    <p>Depending on where you live — the EEA, the UK and California all have relevant law — you
    may have the right to access, correct or delete personal data relating to you, and to object
    to its processing. Given how little this site holds, that usually amounts to deleting an
    email you sent me. Write to <a class="link" href="mailto:{EMAIL}">{EMAIL}</a> and I'll
    handle it.</p>

    <h2>Children</h2>
    <p>This site isn't directed at children under 13, and I don't knowingly collect data
    from them.</p>

    <h2>Changes</h2>
    <p>If this policy changes I'll update the date at the top. There's no version history worth
    maintaining for a page this short.</p>
  </div>
</section>
"""

# =========================================================================
# 404
# =========================================================================
NOTFOUND_BODY = f"""
<section class="section center-page">
  <div>
    <p class="big404">404</p>
    <h1 style="font-size:26px;margin-top:10px">This page doesn't exist</h1>
    <p class="lead" style="margin:0 auto 20px">The link may be out of date, or I may have moved
    something. Here's everything that does exist:</p>
    <div class="cta-row" style="justify-content:center">
      <a class="btn primary" href="index.html">Home</a>
      <a class="btn" href="projects.html">Projects</a>
      <a class="btn" href="research.html">Research</a>
      <a class="btn" href="reading.html">Reading</a>
      <a class="btn" href="contact.html">Contact</a>
    </div>
    <p class="note" style="margin-top:22px">Think something should be here?
      <a class="link" href="contact.html">Tell me</a> and I'll fix the link.</p>
  </div>
</section>
"""

# =========================================================================
# PAGE REGISTRY
# =========================================================================
PAGES = [
  dict(file="index.html", crumb="Home",
       title=f"{NAME} — Quantitative Research & Trading | UC Berkeley MFE",
       desc=("Quantitative researcher and UC Berkeley MFE candidate (Class of 2027), seeking "
             "full-time trading and research roles. Work on regime inference, graph neural "
             "networks for the cross-section of returns, and private-markets data engineering."),
       body=INDEX_BODY, ogtype="profile", schema=[PERSON, WEBSITE],
       prio="1.0", freq="monthly"),

  dict(file="projects.html", crumb="Projects",
       title="Projects — Regime Inference, Graph Learning & Private-Markets Data | " + NAME,
       desc=("In-depth write-ups of six quantitative research projects: BTP-Bund regime-aware "
             "hedging at Citi, graph neural networks on 150k firm-months, a private-markets "
             "PDF-to-Postgres pipeline, and a permutation-test post-mortem on software-cycle "
             "regimes and PE returns."),
       body=PROJECTS_BODY, schema=[
         {"@context": "https://schema.org", "@type": "CollectionPage",
          "name": "Projects", "url": f"{SITE}/projects.html",
          "author": {"@id": f"{SITE}/#person"},
          "isPartOf": {"@id": f"{SITE}/#website"}}],
       prio="0.9", freq="monthly"),

  dict(file="research.html", crumb="Research",
       title="Research — Firms That Look Alike (SSRN Working Paper) | " + NAME,
       desc=("Firms That Look Alike: Characteristic Graphs and the Cross-Section of Stock "
             "Returns — SSRN working paper by Mehta, Girhe and Lingam. Abstract, figures and "
             "full PDF. Characteristic neighbours act as a reference group rather than an "
             "information channel."),
       body=RESEARCH_BODY, ogtype="article", schema=[PAPER],
       prio="0.9", freq="monthly"),

  dict(file="reading.html", crumb="Reading",
       title="Reading List — Markets, Probability & Decision-Making | " + NAME,
       desc=("Currently reading Thinking in Bets by Annie Duke, plus a running list of books "
             "on markets, probability, econometrics and decision-making under uncertainty. "
             "Recommendations welcome."),
       body=READING_BODY, prio="0.6", freq="monthly"),

  dict(file="contact.html", crumb="Contact",
       title="Contact — Open to Full-Time Trading & Research Roles | " + NAME,
       desc=("Get in touch with Venkata Sreenivaas Lingam. Seeking full-time quantitative "
             "trading and research roles starting 2027. Graduating March 2027 from the UC "
             "Berkeley MFE. Cap-exempt H-1B, F-1 OPT / STEM OPT eligible."),
       body=CONTACT_BODY, schema=[
         {"@context": "https://schema.org", "@type": "ContactPage",
          "name": "Contact", "url": f"{SITE}/contact.html",
          "mainEntity": {"@id": f"{SITE}/#person"}}],
       prio="0.8", freq="yearly"),

  dict(file="privacy.html", crumb="Privacy policy",
       title="Privacy Policy | " + NAME,
       desc=("How this site handles data: GitHub Pages hosting logs, Google Analytics with IP "
             "anonymisation, and Formspree for the contact form. No advertising, no "
             "cross-site tracking, no data sales."),
       body=PRIVACY_BODY, prio="0.3", freq="yearly"),

  dict(file="404.html", crumb="Page not found",
       title="Page Not Found (404) | " + NAME,
       desc="That page doesn't exist. Links to everything that does.",
       body=NOTFOUND_BODY, noindex=True),
]

# =========================================================================
# WRITE
# =========================================================================
for p in PAGES:
    (OUT / p["file"]).write_text(page(p), encoding="utf-8")
    print("  wrote", p["file"], f"({len(page(p))//1024} KB)")

# ---- 2. robots.txt ----
(OUT / "robots.txt").write_text(f"""# robots.txt — {SITE}
User-agent: *
Allow: /
Disallow: /404.html

# Crawl the PDFs too — the paper and resume should be findable.
Allow: /assets/

Sitemap: {SITE}/sitemap.xml
""", encoding="utf-8")
print("  wrote robots.txt")

# ---- 3. sitemap.xml ----
import datetime
today = datetime.date.today().isoformat()
urls = "".join(
    f"\n  <url>\n    <loc>{SITE}/{'' if p['file']=='index.html' else p['file']}</loc>"
    f"\n    <lastmod>{today}</lastmod>"
    f"\n    <changefreq>{p['freq']}</changefreq>"
    f"\n    <priority>{p['prio']}</priority>\n  </url>"
    for p in PAGES if not p.get("noindex"))
(OUT / "sitemap.xml").write_text(
    f'<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}\n</urlset>\n',
    encoding="utf-8")
print("  wrote sitemap.xml")

# ---- 10. redirects (see notes: GitHub Pages cannot emit a real 301) ----
REDIRECTS = {"resume.html": "index.html#main"}
for src, dst in REDIRECTS.items():
    tgt = f"{SITE}/{dst.split('#')[0]}"
    (OUT / src).write_text(f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Redirecting to {dst} | {NAME}</title>
  <!-- GitHub Pages serves static files only and cannot send a real HTTP 301.
       rel=canonical + meta refresh is the supported equivalent: search engines
       consolidate ranking signals onto the canonical target, and visitors are
       forwarded immediately. -->
  <link rel="canonical" href="{tgt}">
  <meta name="robots" content="noindex, follow">
  <meta http-equiv="refresh" content="0; url={dst}">
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <main class="wrap center-page">
    <div>
      <h1 style="font-size:24px">This page has moved</h1>
      <p class="lead">Taking you to <a class="link" href="{dst}">{dst}</a>&hellip;</p>
      <p class="note">Not redirected? <a class="link" href="{dst}">Follow this link.</a></p>
    </div>
  </main>
  <script>location.replace("{dst}");</script>
</body>
</html>
""", encoding="utf-8")
    print(f"  wrote {src} -> {dst} (soft 301)")

# ---- favicon ----
(OUT / "assets" / "favicon.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#7C5CFF"/><stop offset="1" stop-color="#38BDF8"/>'
    '</linearGradient></defs>'
    '<rect width="64" height="64" rx="15" fill="#070A12"/>'
    '<circle cx="32" cy="32" r="13" fill="url(#g)"/>'
    '<path d="M10 46 L22 30 L32 38 L54 14" stroke="url(#g)" stroke-width="4" '
    'fill="none" stroke-linecap="round" stroke-linejoin="round" opacity=".85"/>'
    '</svg>', encoding="utf-8")
print("  wrote assets/favicon.svg")

# ---- .nojekyll: serve files verbatim, no Jekyll processing ----
(OUT / ".nojekyll").write_text("", encoding="utf-8")
print("\nDone.")
