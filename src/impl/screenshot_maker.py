import time
import asyncio
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright

class Mhtml2Png:
    def __init__(self, tmp_dir):
        self.tmp_dir = tmp_dir

    def convert(self, mhtml_path, width, chunk_height):
        return asyncio.run(self.__convert(mhtml_path, width, chunk_height))

    async def __convert(self, mhtml_path, width, chunk_height):
        output_prefix = Path(self.tmp_dir) / f"{Path(mhtml_path).stem}_{int(time.time())}"
        images_paths = []

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{Path(mhtml_path).resolve()}", wait_until="networkidle")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(500)
            await page.set_viewport_size({"width": width, "height": 800})
            full_page_image_path = f"{output_prefix}_full.png"
            await page.screenshot(path=full_page_image_path, full_page=True)
            await browser.close()
            images_paths = self.__split_image(full_page_image_path, chunk_height, output_prefix)
        return images_paths

    def __split_image(self, full_image_path, chunk_height, output_prefix):
        images_paths = []
        with Image.open(full_image_path) as img:
            width, height = img.size
            for i in range(0, height, chunk_height):
                top = i
                bottom = min(i + chunk_height, height)
                chunk = img.crop((0, top, width, bottom))
                chunk_path = f"{output_prefix}_{i // chunk_height}.png"
                chunk.save(chunk_path)
                images_paths.append(chunk_path)
        return images_paths
