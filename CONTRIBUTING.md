# Contributing to the lab website

This repo is the source of lybargerlanguagelab.org. Everything under `site/` deploys as-is to GitHub Pages on every push to `main`; there is no build step and no JavaScript. The one exception is the publications page, which is generated (see below).

## How to make a change

1. Clone the repo and create a branch.
2. Edit the files. Open the page you changed in a browser (double-click the HTML file) to check it.
3. Commit, push the branch, and open a pull request. Kevin reviews and merges. The site updates a minute or two after the merge.

## Your page

You have a page at `site/<your-slug>.html`, for example `site/hadeel-elyazori.html`. It is yours to edit. Add sections (Education, Selected Publications, Teaching, Talks, Projects, News), change the bio, add photos, make it longer or shorter. A few constraints keep it consistent with the rest of the site:

- Keep the header, nav, and footer as they are. They match every other page and are edited for all pages at once.
- Plain HTML only: `<h2>` for section headings, `<p>`, `<ul>`, `<a>`, and so on. No scripts, no external stylesheets, no frameworks. The site stylesheet (`site/assets/css/styles.css`) already styles these; you should not need to add CSS. If you do want something styled differently, ask, and it becomes a site-wide class.
- Images go in `site/assets/images/`, 1000px maximum on the long side, with a real `alt` attribute. PDFs go in `site/assets/docs/`.
- Update the `<meta name="description">` near the top, and the matching `og:description` below it, if the page's focus changes.
- The `<script type="application/ld+json">` block in the `<head>` is structured data for search engines, not JavaScript. Leave it in. If your role or links change, update `jobTitle` and `sameAs` there to match.

## Your card on the People page

Your entry on `site/people.html` is a short card: photo, name, role, a one-sentence teaser, a short interests list, and icon links. Edit the teaser, interests, and links freely. Leave the `id` on the `<li>` alone; other pages link to it. Your CV PDF is `site/assets/docs/<your-slug>-cv.pdf`; overwrite it when your CV changes.

## Adding a news item

News lives in two places that must be updated together, in one commit:

1. Add an `<article class="news-item">` at the top of the list in `site/news.html`, with an `id` in the form `YYYY-MM-DD-short-slug`, a `<time>` element, and one to three sentences stating the fact being announced. Copy the shape of the item above it.
2. Add a matching entry at the top of the news strip on `site/index.html`, with the headline linking to `news.html#<that id>`, and drop the oldest entry so the strip stays the same length.

Ids are permanent once published; do not rename one to fix a typo in the title. News announces only things that are already public (a paper accepted or published, an award announced, a defense held). Write in the lab's voice, not first person.

## Check with Kevin first

Some changes need a decision before anyone builds them. Raise these in an issue or at lab meeting. A branch with a mockup is a good way to make the case, but it will not be merged until the decision is made:

- A new page, or a new kind of page (project pages, research-area pages). Every page carries its own copy of the header, nav, and footer and needs an entry in `site/sitemap.xml`, so the page count stays deliberate.
- Any JavaScript, including filters, toggles, and search. The site has none today.
- Changes to the publications page, including tags, filters, and per-paper buttons. These are made in `tools/build_publications.py`, never in the generated HTML.
- Changes to `site/assets/css/styles.css`.

## Do not hand-edit

- `site/publications.html`. It is generated from `tools/publications.bib` by `tools/build_publications.py`, and any manual edit is overwritten on the next build. Publication corrections go to Kevin, who fixes the canonical bib.
- The block between `<!-- TALKS:BEGIN -->` and `<!-- TALKS:END -->` in `site/kevin-lybarger.html`. Same generator, same rule.
- The header, nav, and footer on any page. A change there is made to every page in one commit.

## Writing

Plain, concrete, written for a public academic audience. No marketing language. Nothing unpublished, no results that are not yet public, no contact details beyond what the person has agreed to publish.
