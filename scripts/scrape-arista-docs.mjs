import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const OUT_DIR = join(import.meta.dirname, '..', 'docs', 'arista-scraped');
mkdirSync(OUT_DIR, { recursive: true });

const pages = [
  { url: 'https://www.arista.com/en/um-eos/eos-static-inter-vrf-route', file: 'static-inter-vrf-route.md' },
  { url: 'https://www.arista.com/en/um-eos/eos-inter-vrf-local-route-leaking', file: 'inter-vrf-local-route-leaking.md' },
  { url: 'https://www.arista.com/en/um-eos/eos-policy-based-routing', file: 'policy-based-routing.md' },
  { url: 'https://www.arista.com/en/um-eos/eos-traffic-management', file: 'traffic-management.md' },
  { url: 'https://www.arista.com/en/um-eos/eos-policy-based-routing-pbr', file: 'pbr.md' },
  { url: 'https://www.arista.com/en/um-eos/eos-configuring-vrf-instances', file: 'configuring-vrf.md' },
  { url: 'https://www.arista.com/en/um-eos/eos-gre-tunnels', file: 'gre-tunnels.md' },
  { url: 'https://www.arista.com/en/um-eos/eos-access-control-lists', file: 'access-control-lists.md' },
  { url: 'https://www.arista.com/en/um-eos/eos-static-routes', file: 'static-routes.md' },
  { url: 'https://www.arista.com/en/um-eos/eos-configuration-sessions', file: 'configuration-sessions.md' },
  { url: 'https://www.arista.com/en/um-eos/eos-checkpoint-and-rollback', file: 'checkpoint-rollback.md' },
  { url: 'https://www.arista.com/en/um-eos', file: '_index.md' },
];

async function scrapePage(page, url, filename) {
  console.log(`Scraping: ${url}`);
  try {
    const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    console.log(`  Status: ${resp.status()}`);

    // Wait for JS to render
    await page.waitForTimeout(8000);

    // Check for CAPTCHA
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 200));
    if (bodyText.includes('CAPTCHA') || bodyText.includes("couldn't load")) {
      console.log(`  BLOCKED by CAPTCHA/anti-bot on ${filename}`);
      writeFileSync(join(OUT_DIR, filename), `# BLOCKED BY CAPTCHA\n\nURL: ${url}\nThe Arista docs site requires CAPTCHA verification for headless browsers.\n`);
      return false;
    }

    // Extract content
    const content = await page.evaluate(() => {
      const selectors = [
        '#content', '.article-content', '.content-area', '#main-content',
        'article', '.item-page', '#sp-component', '.com-content-article',
        'main', '#sp-main-body',
      ];

      let el = null;
      for (const sel of selectors) {
        el = document.querySelector(sel);
        if (el && el.textContent.trim().length > 100) break;
      }
      if (!el) el = document.body;

      function nodeToMd(node) {
        if (node.nodeType === Node.TEXT_NODE) return node.textContent;
        if (node.nodeType !== Node.ELEMENT_NODE) return '';
        const tag = node.tagName.toLowerCase();
        if (['nav', 'footer', 'script', 'style', 'noscript', 'iframe'].includes(tag)) return '';
        if (node.classList && (node.classList.contains('nav') || node.classList.contains('sidebar') ||
            node.classList.contains('menu') || node.classList.contains('footer') ||
            node.classList.contains('header'))) return '';
        let children = Array.from(node.childNodes).map(c => nodeToMd(c)).join('');
        switch (tag) {
          case 'h1': return `\n# ${children.trim()}\n\n`;
          case 'h2': return `\n## ${children.trim()}\n\n`;
          case 'h3': return `\n### ${children.trim()}\n\n`;
          case 'h4': return `\n#### ${children.trim()}\n\n`;
          case 'p': return `\n${children.trim()}\n\n`;
          case 'br': return '\n';
          case 'li': return `- ${children.trim()}\n`;
          case 'ul': case 'ol': return `\n${children}\n`;
          case 'pre': return `\n\`\`\`\n${children.trim()}\n\`\`\`\n\n`;
          case 'code': return `\`${children.trim()}\``;
          case 'strong': case 'b': return `**${children.trim()}**`;
          case 'em': case 'i': return `*${children.trim()}*`;
          case 'table': return `\n${children}\n`;
          case 'tr': return `${children}|\n`;
          case 'th': case 'td': return `| ${children.trim()} `;
          case 'a': {
            const href = node.getAttribute('href');
            if (href && !href.startsWith('#') && !href.startsWith('javascript'))
              return `[${children.trim()}](${href})`;
            return children;
          }
          default: return children;
        }
      }
      return nodeToMd(el);
    });

    const cleaned = content.replace(/\n{4,}/g, '\n\n\n').replace(/[ \t]+$/gm, '').trim();
    const header = `<!-- Source: ${url} -->\n<!-- Scraped: ${new Date().toISOString()} -->\n\n`;
    writeFileSync(join(OUT_DIR, filename), header + cleaned + '\n');
    console.log(`  Saved ${filename} (${cleaned.length} chars)`);
    return true;
  } catch (e) {
    console.error(`  FAILED: ${e.message}`);
    writeFileSync(join(OUT_DIR, filename), `# FAILED TO LOAD\n\nURL: ${url}\nError: ${e.message}\n`);
    return false;
  }
}

async function main() {
  // Launch with stealth-like settings
  const browser = await chromium.launch({
    headless: false,  // Use headed mode via Xvfb if available, else new headless
    args: [
      '--headless=new',  // New headless mode (less detectable)
      '--disable-blink-features=AutomationControlled',
      '--no-sandbox',
    ],
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    locale: 'en-US',
    timezoneId: 'America/New_York',
    viewport: { width: 1920, height: 1080 },
  });

  // Remove webdriver property
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => false });
    // Override permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
      parameters.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : originalQuery(parameters);
  });

  const page = await context.newPage();

  let anySuccess = false;
  for (const { url, file } of pages) {
    const ok = await scrapePage(page, url, file);
    if (ok) anySuccess = true;
    // Add delay between requests
    await page.waitForTimeout(2000);
  }

  if (!anySuccess) {
    console.log('\nAll pages blocked by CAPTCHA. Arista docs require human verification.');
  }

  await browser.close();
  console.log('\nDone!');
}

main().catch(e => { console.error(e); process.exit(1); });
