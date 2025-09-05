import email, os, json, html, re

class HtmlConverter:
    def __init__(self, mhtml_manipulator, html_manipulator):
        self.mhtml_manipulator = mhtml_manipulator
        self.html_manipulator = html_manipulator
    
    def exec(self, mhtml_path):
        html_path = self.__create_html(mhtml_path)
        location_to_asset = self.__load_assets(mhtml_path)
        with open(f"{os.path.dirname(html_path)}/assets/text-1.html", "r") as file:
            content = file.read()
        with open(html_path, 'w') as file:
            file.write(content)
        self.__fix_css(html_path, location_to_asset)
        self.__fix_html(html_path, location_to_asset)
        self.__fix_link_crossorigin(html_path)
        self.__fix_fonts(html_path, location_to_asset)

    def __create_html(self, mhtml_path):
        dirname = os.path.dirname(mhtml_path)
        filename = os.path.basename(mhtml_path)[:-6] + ".html"
        html_path = f"{dirname}/{filename}"
        with open(html_path, "w", encoding="utf-8") as file:
            file.write("")
        if not os.path.exists(f"{dirname}/assets"):
            os.makedirs(f"{dirname}/assets")
        return html_path

    def __load_assets(self, mhtml_path):
        location_to_asset = {}
        counter = 0
        with open(mhtml_path, "r", encoding="utf-8") as mhtml:
            msg = email.message_from_file(mhtml)
        types = {}
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type in types:
                types[content_type] = types[content_type] + 1
            else:
                types[content_type] = 1
            content_location = part.get("Content-Location")
            bytes = part.get_payload(decode=True)
            if bytes:
                counter += 1
                asset_path = f"assets/{content_type.split("/")[0]}-{counter}.{content_type.split("/")[-1]}"
                local_path = f"{os.path.dirname(mhtml_path)}/{asset_path}"
                with open(local_path, "wb") as img_file:
                    img_file.write(bytes)
                location_to_asset[content_location] = {}
                location_to_asset[content_location]["asset"] = asset_path
        return location_to_asset
    
    def __fix_css(self, html_path, location_to_asset):
        css_images = {}
        css_files = []
        for location, data in location_to_asset.items():
            asset = data["asset"]
            if "/css/v2/images/" in location:
                css_images[location.split("/css/v2/")[-1]] = asset
            if asset.endswith(".css"):
                css_files.append(f"{os.path.dirname(html_path)}/{asset}")
        for css_file in css_files:
            with open(css_file, "r") as file:
                content = file.read()
            for url, asset in css_images.items():
                content = content.replace(f'url("{url}")', f'url("{asset[7:]}")')
            with open(css_file, 'w') as file:
                file.write(content)
    
    def __fix_html(self, html_path, location_to_asset):
        with open(html_path, "r") as file:
            content = file.read()
        for location, data in location_to_asset.items():
            content = content.replace(f'{html.escape(location)}', f'{data["asset"]}')
        with open(html_path, 'w') as file:
            file.write(content)

    def __fix_link_crossorigin(self, html_path):
        return self.html_manipulator.exec(html_path, """
            (function() {
                counter = 0;
                const cssLinks = document.querySelectorAll('link[rel="stylesheet"][crossorigin]');
                cssLinks.forEach(link => {
                    link.removeAttribute('crossorigin');
                });
                const allElements = document.querySelectorAll('*');
                allElements.forEach(element => {
                    if (!element.id) {
                        element.id = `a11ypoc_marker_id_${counter++}`;
                    }
                });
                return counter;
            })();
        """)
    
    def __fix_fonts(self, html_path, location_to_asset):
        self.html_manipulator.exec(html_path, """
            (function() {
                counter = 0;
                const head = document.querySelector('head');
                if (head) {
                    const faCdnLink = document.createElement('link');
                    faCdnLink.rel = 'stylesheet';
                    faCdnLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css';
                    head.appendChild(faCdnLink);
                }
                return counter;
            })();
        """)
        css_files = []
        for location, data in location_to_asset.items():
            asset = data["asset"]
            if asset.endswith(".css"):
                css_files.append(f"{os.path.dirname(html_path)}/{asset}")
        for css_file in css_files:
            with open(css_file, "r") as file:
                content = file.read()
            content = re.sub(r'@font-face\s*{[^}]*}', '', content, flags=re.DOTALL)
            with open(css_file, 'w') as file:
                file.write(content)
