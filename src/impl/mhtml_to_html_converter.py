import email, os, json

class HtmlConverter:
    def __init__(self, mhtml_manipulator, html_manipulator):
        self.mhtml_manipulator = mhtml_manipulator
        self.html_manipulator = html_manipulator
    
    def exec(self, mhtml_path):
        self.__generate_ids(mhtml_path)
        html_path = self.__create_html(mhtml_path)
        location_to_asset = self.__laod_assets(mhtml_path)
        for l, a in location_to_asset.items():
            print(f"{a}: {l}")

    def __generate_ids(self, path):
        return self.mhtml_manipulator.exec(path, """
            (function() {
                counter = 0;
                const allElements = document.querySelectorAll('*');
                allElements.forEach(element => {
                    if (!element.id) {
                        element.id = `a11ypoc_marker_id_${counter++}`;
                    }
                });
                return counter;
            })();
        """)

    def __create_html(self, mhtml_path):
        html = self.mhtml_manipulator.exec(mhtml_path, """
            (function() {
                return document.documentElement.outerHTML;
            })();
        """)
        dirname = os.path.dirname(mhtml_path)
        filename = os.path.basename(mhtml_path)[:-6] + ".html"
        html_path = f"{dirname}/{filename}"
        with open(html_path, "w", encoding="utf-8") as file:
            file.write(html)
        if not os.path.exists(f"{dirname}/assets"):
            os.makedirs(f"{dirname}/assets")
        return html_path

    def __get_images_data(self, path):
        return self.html_manipulator.exec(path, """
            (function() {
                const images = Array.from(document.querySelectorAll('img'));
                return images.reduce((result, img) => {
                    result[img.src] = {
                        id: img.id,
                        src: img.src || "none",
                    };
                    return result;
                }, {});
            })();
        """)
    
    def __resolve_images(self, mhtml_path, src_to_data):
        resolved_src_to_data = {}
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
            if content_type.startswith("image/"):
                content_location = part.get("Content-Location")
                if content_location in src_to_data:
                    image_bytes = part.get_payload(decode=True)
                    if image_bytes:
                        extension = content_type.split("/")[-1]
                        counter += 1
                        asset_path = f"assets/image-{counter}.{extension}"
                        local_path = f"{os.path.dirname(mhtml_path)}/{asset_path}"
                        with open(local_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        resolved_src_to_data[content_location] = {}
                        resolved_src_to_data[content_location]["asset"] = asset_path
        print(types)
        return resolved_src_to_data

    def __replace_images(self, html_path, src_to_data):
        # Serialize the Python dictionary to a JSON string
        src_to_data_json = json.dumps(src_to_data)

        # Pass the JSON string into the JavaScript code
        return self.html_manipulator.exec(html_path, f"""
            (function() {{
                let counter = 0;
                const srcToData = {src_to_data_json};
                const images = document.querySelectorAll('img');
                
                images.forEach(image => {{
                    if (srcToData[image.src] && srcToData[image.src]['asset']) {{
                        image.src = srcToData[image.src]['asset'];
                        counter++;
                    }}
                }});
                
                return counter;
            }})();
        """)

    # New method: Get CSS href links
    def __get_css_data(self, path):
        return self.html_manipulator.exec(path, """
            (function() {
                const links = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
                return links.reduce((result, link) => {
                    result[link.href] = {
                        href: link.href || "none",
                    };
                    return result;
                }, {});
            })();
        """)

    # New method: Resolve CSS content
    def __resolve_css(self, mhtml_path, href_to_data):
        resolved_href_to_data = {}
        counter = 0
        with open(mhtml_path, "r", encoding="utf-8") as mhtml:
            msg = email.message_from_file(mhtml)
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/css":
                content_location = part.get("Content-Location")
                if content_location in href_to_data:
                    css_bytes = part.get_payload(decode=True)
                    if css_bytes:
                        counter += 1
                        asset_path = f"assets/style-{counter}.css"
                        local_path = f"{os.path.dirname(mhtml_path)}/{asset_path}"
                        with open(local_path, "wb") as css_file:
                            css_file.write(css_bytes)
                        resolved_href_to_data[content_location] = {}
                        resolved_href_to_data[content_location]["asset"] = asset_path
        return resolved_href_to_data

    # New method: Replace CSS href links
    def __replace_css_links(self, html_path, href_to_data):
        # Serialize the Python dictionary to a JSON string
        href_to_data_json = json.dumps(href_to_data)

        # Pass the JSON string into the JavaScript code
        return self.html_manipulator.exec(html_path, f"""
            (function() {{
                let counter = 0;
                const hrefToData = {href_to_data_json};
                const links = document.querySelectorAll('link[rel="stylesheet"]');
                
                links.forEach(link => {{
                    if (hrefToData[link.href] && hrefToData[link.href]['asset']) {{
                        link.href = hrefToData[link.href]['asset'];
                        counter++;
                    }}
                }});
                
                return counter;
            }})();
        """)

    def __laod_assets(self, mhtml_path):
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
        print(types)
        return location_to_asset
    
    