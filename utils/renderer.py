import asyncio
from typing import Optional


async def render_text_image(texte: str, *, width: int = 800, font_family: str = 'monospace', font_size: int = 22, bg_color: str = '#000000', text_color: str = '#FFFFFF', padding: int = 24) -> bytes:
    """Renders the given text to a PNG image using Playwright (async).

    Returns image bytes. Requires `playwright` and installed browsers (`playwright install`).
    """
    try:
        from playwright.async_api import async_playwright
    except Exception as exc:
        raise RuntimeError("playwright is not installed. Install with `pip install playwright` and run `playwright install`") from exc

    # simple HTML template
    safe_text = (texte.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>'))
    html = f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          body {{ background: {bg_color}; margin:0; padding:{padding}px; }}
          .wrapper {{ color: {text_color}; font-family: {font_family}; font-size: {font_size}px; white-space: pre-wrap; line-height: 1.35; word-wrap: break-word; }}
        </style>
      </head>
      <body>
        <div class="wrapper">{safe_text}</div>
      </body>
    </html>
    """

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": 600})
        await page.set_content(html, wait_until='networkidle')
        # compute content height
        el = await page.query_selector('.wrapper')
        if el:
            height = await el.evaluate('el => el.scrollHeight')
            # ensure min height
            h = max(200, int(height) + padding * 2)
            await page.set_viewport_size({"width": width, "height": h})
        img = await page.screenshot(type='png', full_page=True)
        await browser.close()
        return img
