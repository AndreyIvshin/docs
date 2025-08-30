import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


class MhtmlManipulator:
    def __init__(self, tmp_dir):
        self.tmp_dir = tmp_dir

    def exec(self, mhtml_path, script):
        return asyncio.run(self.__exec(mhtml_path, script))

    async def __exec(self, mhtml_path, script):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{Path(mhtml_path).resolve()}", wait_until="networkidle")
            await page.wait_for_load_state("networkidle")
            console_output = await page.evaluate(script)
            client = await page.context.new_cdp_session(page)
            snapshot = await client.send("Page.captureSnapshot", {"format": "mhtml"})
            with open(mhtml_path, "w", encoding="utf-8") as file:
                file.write(snapshot["data"])
            await browser.close()
        return console_output
