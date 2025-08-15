/**
 * screenshot.js
 *
 * This utility script drives a headless Chromium browser via Puppeteer to
 * generate screenshots of ShotGeek pages.  The script is intentionally small
 * and focused so it can be reused in different CI contexts without extra
 * dependencies.
 *
 * Usage:
 *   node scripts/screenshot.js <url> <outputPath>
 *
 * - <url>        The page to visit. Defaults to http://localhost:8000.
 * - <outputPath> Where to write the screenshot file. Defaults to
 *                screenshots/homepage.png.
 *
 * The function below performs four straightforward steps:
 *   1. Launch a headless browser. `--no-sandbox` and
 *      `--disable-setuid-sandbox` flags are passed because GitHub Actions
 *      runners do not provide a usable Chromium sandbox
 *      (see https://pptr.dev/troubleshooting#chrome-headless-doesnt-launch-on-linux).
 *   2. Navigate to the requested URL and wait for network quiescence.
 *   3. Ensure the destination directory exists.
 *   4. Capture a full-page PNG screenshot and close the browser.
 *
 * Keeping the logic in a single async function (`captureScreenshot`) avoids
 * unnecessary complexity and makes future enhancements—such as adding more
 * pages or tweaking viewport sizes—easier to manage.
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

/**
 * Capture a screenshot of the given URL and save it to outputPath.
 *
 * @param {string} url - Absolute URL of the page to capture.
 * @param {string} outputPath - Path to write the PNG file.
 */
async function captureScreenshot(url, outputPath) {
  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle0' });
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  await page.screenshot({ path: outputPath, fullPage: true });
  await browser.close();
}

const targetUrl = process.argv[2] || 'http://localhost:8000';
const outputPath = process.argv[3] || 'screenshots/homepage.png';

captureScreenshot(targetUrl, outputPath).catch((err) => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
