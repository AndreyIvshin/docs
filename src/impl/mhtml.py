from pathlib import Path
import shutil, email, html, re

class MhtmlParser():
    def parse(self, mhtml_path, output_dir):
        work_dir = self.__prepare_work_dir(mhtml_path, output_dir)
        location_to_asset = self.__extract_assets(work_dir)
        html_path, location_to_asset = self.__prepare_html(work_dir, location_to_asset)
        self.__fix_html(html_path, location_to_asset)
        self.__fix_css(work_dir, location_to_asset)
    
    def __prepare_work_dir(self, mhtml_path, output_dir):
        work_dir = Path(output_dir).resolve()/Path(mhtml_path).resolve().stem
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir()
        shutil.copy(mhtml_path, work_dir/"index.mhtml")
        return work_dir

    def __extract_assets(self, work_dir):
        assets_dir = work_dir/"assets"
        assets_dir.mkdir()
        location_to_asset = {}
        counters = {}
        with open(work_dir/"index.mhtml", "r", encoding="utf-8") as mhtml:
            message = email.message_from_file(mhtml)
        for part in message.walk():
            content_type = part.get_content_type()
            content_location = part.get("Content-Location")
            bytes = part.get_payload(decode=True)
            if bytes:
                split = content_type.split("/")
                data_type, extension = split[0], split[-1].split("+")[0]
                counters[data_type] = counters.get(data_type, 0) + 1
                filename = f"{data_type}-{counters[data_type]}.{extension}"
                with open(assets_dir/filename, "wb") as file:
                    file.write(bytes)
                location_to_asset[content_location] = f"assets/{filename}"
        return location_to_asset
    
    def __prepare_html(self, work_dir, location_to_asset):
        html_asset = "assets/text-1.html"
        with open(work_dir/html_asset, "r") as file:
            content = file.read()
        html_path = work_dir/"index.html"
        with open(html_path, 'w') as file:
            file.write(content)
        return html_path, {l: "index.html" if a == html_asset else a for l, a in location_to_asset.items()}    
    
    def __fix_html(self, html_path, location_to_asset):
        with open(html_path, "r") as file:
            content = file.read()
        for location, asset in location_to_asset.items():
            content = content.replace(html.escape(location), asset)
        with open(html_path, 'w') as file:
            file.write(content)
    
    def __fix_css(self, work_dir, location_to_asset):
        pattern = r'url\(["\']?([^"\')\s]+)["\']?\)'
        css_files = []
        for location, asset in location_to_asset.items():
            if asset.endswith(".css"):
                css_files.append(work_dir/asset)
        for css_file in css_files:
            with open(css_file, "r") as file:
                content = file.read()
            for url in re.findall(pattern, content):
                for location, asset in location_to_asset.items():
                    if url in location:
                        content = content.replace(f'url("{url}")', f'url("{asset[7:]}")')
                        break;
            with open(css_file, 'w') as file:
                file.write(content)
