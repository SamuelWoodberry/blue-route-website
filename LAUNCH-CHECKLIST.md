# Launch checklist: Blue Route Logistics

## Information you still need to provide
These are hidden on the site until you add them to `site.config.json`. Nothing has been invented.

- [ ] **Confirm the domain.** You wrote "blue route.us.com"; the site assumes `blueroute.us.com`.
- [ ] **Legal LLC name** exactly as filed with Florida Sunbiz (used in copyright line, Privacy Policy, Terms)
- [ ] **Business phone number**
- [ ] **Business email** (e.g. dispatch@ or info@ your domain)
- [ ] **Business hours**
- [ ] **Social media / Google Business Profile links** (optional; hidden if none)
- [ ] **Logo approval.** The logo in `static/img/` is a *proposed concept pending your approval*.
- [ ] **Policy effective date**, plus attorney review of the Privacy Policy and Terms of Use (both are drafts)
- [ ] **Any real business photos** (optional; the design works without stock photography)

## Business decisions to confirm against the website copy
- [ ] Same-day and next-day prescription delivery are listed as services. Confirm you can offer both at launch.
- [ ] "Delivery confirmation and documentation for every stop." Confirm your process supports this.
- [ ] The Services page says clinical/laboratory specimen transport is not currently offered, and that controlled and temperature-sensitive deliveries are "available for discussion, subject to operational approval." Confirm that wording.
- [ ] Backup and overflow coverage is described as "subject to availability."
- [ ] Commercial auto and general liability insurance is in place before signing contracts (the site says service begins once insurance is confirmed).

## Technical setup
- [ ] Site deployed on Netlify from GitHub
- [ ] Form detection enabled, site redeployed, `quote` and `contact` forms visible in Netlify
- [ ] Email notifications set for both forms
- [ ] Test submission of each form on the live site: email received, success message shown
- [ ] Custom domain connected; `www` redirects to the main domain (Netlify does this automatically)
- [ ] HTTPS certificate active; `http://` redirects to `https://`
- [ ] Business email working, with SPF, DKIM and DMARC records added
- [ ] Google Search Console verified (DNS TXT method), `sitemap.xml` submitted
- [ ] Google Business Profile created as a service-area business (address hidden)
- [ ] Optional: Plausible analytics domain set
- [ ] Run `python3 tools/check_site.py`: "All checks passed"

## Already done in the build
- Six main pages plus Privacy Policy, Terms of Use, Thank-you and 404 pages
- Responsive layouts tested at 390px (phone) and 1440px (desktop); mobile menu supports keyboard and the Escape key
- Unique titles and meta descriptions, canonical URLs, Open Graph and Twitter cards, a 1200×630 share image
- LocalBusiness structured data (city, state and service areas only; no street address), `sitemap.xml`, `robots.txt`
- Self-hosted fonts (no Google Fonts tracking), and about 200 KB for the home page including fonts
- Security headers: Content-Security-Policy, HSTS, nosniff, frame protection
- Accessibility: skip link, visible focus states, labeled fields, error messages announced and linked to fields, reduced-motion support, all key text contrast ratios ≥ 4.5:1
- Testimonial component built but hidden until real, approved feedback is added
