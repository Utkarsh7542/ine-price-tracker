# Design note

## The problem
Getting past the store's anti-scraping was the whole assignment. Three things
made it hard:
- The price doesn't load with the page. A "Check today's price" button stays
  disabled until you move the mouse over the price box a few times and wait about
  half a second, so it's watching for a real person.
- Clicking runs a small proof-of-work puzzle and asks the server for the price,
  and that request fails on purpose some of the time ("challenge_failed").
- The visible price is booby-trapped: decoy prices sitting under the obvious
  class names, invisible characters between the real digits, and a real class
  name that changes on every load.

## How I made it reliable
I use a real browser (Playwright) only for the price, since it needs the page's
own JavaScript. Search and options just use plain HTTP requests, which is
faster; that split was the main judgment call. To unlock the button, the scraper
wiggles the mouse over the price box and waits. The random failures are handled
by retrying up to 12 times, and I record the honest outcome: "success" on the
first try, "retried" if it took more, "failed" if it never worked. Failed runs
are still saved with the price and stock blank. For the price itself I skip the
messy text and read the real value straight out of React's state, which sidesteps
the decoys, the invisible characters, and the changing class names in one move.

## Trade-offs
- Render's free tier (512 MB) is too small to run headless Chrome reliably, so
  the scheduled scrape runs on GitHub Actions instead (allowed as a "scheduled
  function", and it covers the CI/CD bonus). Render just serves the API.
- The store has no search and reshuffles its listing every request, so I cache
  the whole catalog in Supabase once and search that.
- Reading React state is a bit fragile, but it's the only way past the decoys. I
  look the data up by its shape, not variable names, so minified code doesn't
  break it.

## What AI got wrong first
I used Claude to help build this, and a few things it wrote didn't work until I
fixed them:
- The first scraper moved the mouse to random spots, so the button never
  unlocked (the page only counts movement over the price box).
- Cookie handling missed twice: it clicked "reject" once on load, but the popup
  shows up late and in a random spot, so it usually missed and blocked
  everything. I made it watch for the popup and dismiss it whenever it appears.
- It first read the price from the visible text and grabbed the decoys; reading
  React state fixed that.
- Search first hit the store live on every request, which was slow, so I cached
  the catalog.

I read through all of it and understand how each piece works.
