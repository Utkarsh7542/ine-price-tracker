# Design note

## The problem
The store hides the price behind a few tricks, and getting past them reliably
was the whole point of the assignment. What I found:

- The price doesn't load with the page. There's a "Check today's price" button
  that stays disabled until you move the mouse over the price box a few times
  and wait about half a second. It's checking for a real person.
- Once you click, the page runs a small proof-of-work puzzle and asks the server
  for the price. That request fails on purpose some of the time (it comes back
  as `challenge_failed`).
- The price on the page is booby-trapped. There are hidden decoy prices that use
  the obvious class names, the real price has invisible characters stuffed
  between the digits, and the real element's class name changes on every load.

## How I made it reliable
- I use a real browser (Playwright) for the price, because it genuinely needs
  the page's own JavaScript to run. Everything that isn't guarded (searching
  products, reading a product's options) uses plain HTTP requests instead, which
  is faster and lighter. That split was the main judgment call.
- To unlock the button, the scraper moves the mouse over the price box in small
  random steps and waits, which is what the page is looking for.
- The random `challenge_failed` is handled by retrying. Each scrape tries up to
  12 times before giving up. First try working is "success", more than one is
  "retried", never working is "failed". Failed scrapes still get saved with
  price and stock left empty, so the history stays honest instead of hiding the
  misses.
- For the price itself, instead of reading the messy on-screen text I read the
  real price object out of React's internal state, which is the decrypted value
  the page already computed. That gets past the decoys, the invisible
  characters, and the changing class names all at once.

## Trade-offs
- Running the scheduled scrape on Render's free tier would mean a headless
  Chrome in 512 MB of RAM, which is tight and likely to fail when nobody's
  watching. So the scheduled scrape runs on GitHub Actions instead, which the
  assignment allows ("a scheduled function") and which also covers the CI/CD
  bonus. The Render backend only serves the API, so it stays light.
- The store has no search API and shuffles its listing on every request, so
  paging through it live is slow and never quite complete. I fetch the whole
  catalog once and cache it in Supabase, so search is a quick database lookup.
- Reading React's internal state is a little fragile. If the store rewrote its
  frontend it could break. I went with it anyway because it's the only way to
  get the true price past the decoys, and I look up the data by its shape rather
  than by variable names, so it survives the code being minified.

## What AI got wrong first, and how I fixed it
I used Claude to help build this. A few things it produced didn't work until I
corrected them:

- The first scraper moved the mouse to random spots and then clicked. The button
  never unlocked, because the page only counts mouse movement over the price box
  itself. I changed it to move over that box.
- Cookie handling was wrong twice. The first version clicked "reject" once, right
  after load. But the cookie popup shows up at a random time and place, so the
  click usually missed and the popup blocked everything behind it. The fix was to
  watch for the popup's dark backdrop and dismiss it whenever it appears, and to
  re-check before every scrape click.
- The first attempt read the price from the visible text, which pulled in the
  decoys and the invisible characters. Reading React's state instead fixed it.
- Search first hit the store's catalog live on every request, which was slow on
  the free-tier server. Caching the catalog in Supabase fixed it.

I read through all of the code and understand how each part works.
