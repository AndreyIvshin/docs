import time, json, email
from core.module import Module

DISPLAY_MAP = {}

class ImgFolder(Module):
    def __init__(self, mhtml_manipulator, logger_factory):
        super().__init__(mhtml_manipulator, logger_factory)

    def fix_mhtml(self, path):
        self.logger.debug(f"Starting images foldening...")
        start_time = time.time()
        map = self.mhtml_manipulator.exec(path, """
            (function() {
                const displayMap = {};
                const contentWrapper = document.getElementById("co_document_0");
                if (contentWrapper) {
                    const images = contentWrapper.querySelectorAll("img");
                    images.forEach(image => {
                        displayMap[image.id] = image.style.display || "";
                        image.style.display = "none";
                        image.classList.add("folded-by-a11ypoc");
                    });
                }
                return JSON.stringify(displayMap);
            })();
        """)
        DISPLAY_MAP = json.loads(map)
        self.logger.debug(f"Images foldering completed in {time.time() - start_time:.2f} seconds.")
        self.logger.info(f"Folded {len(DISPLAY_MAP.items())} images.")

class ImgUnfolder(Module):
    def __init__(self, mhtml_manipulator, logger_factory):
        super().__init__(mhtml_manipulator, logger_factory)

    def fix_mhtml(self, path):
        self.logger.debug(f"Starting images unfoldening...")
        start_time = time.time()
        counter = self.mhtml_manipulator.exec(path, f"""
            (function() {{
                let counter = 0;
                const contentWrapper = document.getElementById("co_document_0");
                if (contentWrapper) {{
                    const images = contentWrapper.querySelectorAll("img.folded-by-a11ypoc");
                    const displayMap = {json.dumps(DISPLAY_MAP)};
                    images.forEach(image => {{
                        image.style.display = displayMap[image.id];
                        delete displayMap[image.id];
                        image.classList.remove("folded-by-a11ypoc");
                        counter++;
                    }});
                }}
                return counter;
            }})();
        """)
        self.logger.debug(f"Images unfoldening completed in {time.time() - start_time:.2f} seconds.")
        self.logger.info(f"Unfolded {counter} images.")

class ImagesRemediator(Module):
    def __init__(self, mhtml_manipulator, logger_factory, llm, report):
        super().__init__(mhtml_manipulator, logger_factory)
        self.report = report
        self.llm = llm

    def fix_mhtml(self, path):
        self.logger.debug(f"Starting images remediation...")
        start_time = time.time()

        self.logger.debug(f"Extracted images...")
        src_to_data = self.__extract_images(path)
        self.logger.debug(f"Extracted {len(src_to_data)} images")

        self.logger.debug(f"Classifying images via LLM...")
        self.__classify_images(src_to_data)
        self.logger.debug(f"Images classified: {len(src_to_data)}")
        
        for i, (src, data) in enumerate(src_to_data.items()):
            if src_to_data[i]["has_text"]:
                self.logger.debug(f"Extracting text via LLM...")
                text = self.__extract_text(data["path"])
                self.logger.debug(f"Text extracted: {text}")

        self.logger.debug(f"Images remediation completed in {time.time() - start_time:.2f} seconds.")
        self.logger.info(f"Remediated {len(src_to_data)} images.")
        self.report["img"] = len(src_to_data)
    
    def __extract_images(self, path):
        images = self.mhtml_manipulator.exec(path, """
            (function() {
                const rootElement = document.getElementById('co_document_0');
                const images = Array.from(rootElement.querySelectorAll('img'));
                return images.map(img => img.src);
            })();
        """)
        with open(path, "r", encoding="utf-8") as file:
            msg = email.message_from_file(file)
        images_paths = {}
        counter = 0;
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type.startswith("image/"):
                content_location = part.get("Content-Location")
                if content_location in images:
                    image_data = part.get_payload(decode=True)
                    if image_data:
                        extension = content_type.split("/")[-1]
                        counter += 1
                        local_path = f"{path}_image_{counter}.{extension}"
                        with open(local_path, "wb") as img_file:
                            img_file.write(image_data)
                        images_paths[content_location] = {"path": local_path}
        return images_paths
    
    def __classify_images(self, src_to_data):
        paths = [data["path"] for src, data in src_to_data.items()]
        response = self.llm.ask(images=paths, prompt=f"""
            Analyze all images attached and classify them by the following criterias:
                - does this image contains text in the bottom?
                - does this image a chart?
            For each image analyzed, provide the following structured response:
            ```json
            [
                {{
                    "src": "...",
                    "has_text": true/false,
                    "is_chart": true/false
                }},
                {{
                    ...
                }}
            ]
            ```
        """, max_tokens=15000, temperature=0, context="",)
        if response.startswith("```json") and response.endswith("```"):
            response = response[len("```json"):-len("```")].strip()
        response = json.loads(response)
        i = 0
        for src, data in src_to_data.items():
            llm_response = response[i]
            data["has_text"] = llm_response["has_text"]
            data["is_chart"] = llm_response["is_chart"]
            i += 1
    
    def __extract_text(self, path):
        response = self.llm.ask(images=[path], prompt=f"""
            Extract the text at the bottom of the image:
            For each image analyzed, provide the following structured response:
            ```json
            {{
                "text": "..."
            }}
            ```
        """, max_tokens=15000, temperature=0, context="",)
        if response.startswith("```json") and response.endswith("```"):
            response = response[len("```json"):-len("```")].strip()
        return response

