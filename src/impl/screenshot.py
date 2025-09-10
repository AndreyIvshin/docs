import asyncio
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright

class Html2Png:

    def convert(self, html_path, prefix, width, height):
        async def process():
            image_prefix = html_path.parent / prefix
            image_paths = []
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(f"file://{Path(html_path).resolve()}", wait_until="networkidle")
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(500)
                await page.set_viewport_size({"width": width, "height": 800})
                full_image_path = f"{image_prefix}_full.png"
                await page.screenshot(path=full_image_path, full_page=True)
                await browser.close()
                with Image.open(full_image_path) as img:
                    img_width, img_height = img.size
                    for i in range(0, img_height, height):
                        top = i
                        bottom = min(i + height, img_height)
                        chunk = img.crop((0, top, img_width, bottom))
                        image_path = f"{image_prefix}_{i // height}.png"
                        chunk.save(image_path)
                        image_paths.append(image_path)
            return image_paths
        return asyncio.run(process())
