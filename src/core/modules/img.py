import time, json, email
from itertools import islice
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
        src_to_data = {src: src_to_data[src] for src in islice(src_to_data.keys(), 2)}
        self.logger.debug(f"Extracted {len(src_to_data)} images")

        self.logger.debug(f"Classifying images via LLM...")
        self.__classify_images(src_to_data)
        self.logger.debug(f"Images classified: {len(src_to_data)}")
        
        for src, data in src_to_data.items():
            if data["has_text"] == "true":
                self.logger.debug(f"Extracting text via LLM...")
                data["text"] = self.__extract_text(data["path"])
        
        for src, data in src_to_data.items():
            if data["is_chart"] == "true":
                self.logger.debug(f"Extracting description via LLM...")
                data["description"] = self.__extract_description(data["path"])

        self.logger.debug(f"Adding text to mhtml...")
        counter = self.__add_text(path, src_to_data)
        self.logger.debug(f"Added text: {counter}")

        self.logger.debug(f"Replacing alt...")
        counter = self.__replace_alt(path, src_to_data)
        self.logger.debug(f"Alts replaced: {counter}")

        self.logger.debug(f"Adding modals...")
        counter = self.__add_modals(path, src_to_data)
        self.logger.debug(f"Modals added: {counter}")

        self.logger.debug(f"Images remediation completed in {time.time() - start_time:.2f} seconds.")
        self.logger.info(f"Remediated {len(src_to_data)} images.")
        self.report["img"] = len(src_to_data)
    
    def __extract_images(self, path):
        src_to_data = self.mhtml_manipulator.exec(path, """
            (function() {
                const rootElement = document.getElementById('co_document_0');
                const images = Array.from(rootElement.querySelectorAll('img'));
                return images.reduce((result, img) => {
                    result[img.src] = {
                        alt: img.alt || null,
                        id: img.id || null
                    };
                    return result;
                }, {});
            })();
        """)
        with open(path, "r", encoding="utf-8") as file:
            msg = email.message_from_file(file)
        counter = 0;
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type.startswith("image/"):
                content_location = part.get("Content-Location")
                if content_location in src_to_data:
                    image_bytes = part.get_payload(decode=True)
                    if image_bytes:
                        extension = content_type.split("/")[-1]
                        counter += 1
                        local_path = f"{path}_image_{counter}.{extension}"
                        with open(local_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        src_to_data[content_location]["path"] = local_path
        unresolved_srcs = [src for src, data in src_to_data.items() if "path" not in data]
        for src in unresolved_srcs:
            del src_to_data[src]
        return src_to_data
    
    def __classify_images(self, src_to_data):
        paths = [data["path"] for src, data in src_to_data.items()]
        response = self.llm.ask(images=paths, prompt=f"""
            For every image attached, provide the following structured response:
            ```json
            [
                {{
                    "has_text": "true/false - Does this image has plaint text description under it?",
                    "is_chart": "true/false Is this image a chart?",
                    "alt": "short description of the image"
                }},
                {{
                    ...
                }}
            ]
            ```
        """, max_tokens=15000, temperature=0, context="",)
        self.logger.debug(f"LLM response:\n{response}")
        response = response[len("```json"):-len("```")].strip()
        response = json.loads(response)
        i = 0
        for src, data in src_to_data.items():
            llm_response = response[i]
            data["has_text"] = llm_response["has_text"]
            data["is_chart"] = llm_response["is_chart"]
            data["alt"] = llm_response["alt"]
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
        self.logger.debug(f"LLM response:\n{response}")
        response = response[len("```json"):-len("```")].strip()
        return json.loads(response)["text"]
    
    def __extract_description(self, path):
        response = self.llm.ask(images=[path], prompt=f"""
            Give me detailed description of the attached chart:
            For each image analyzed, provide the following structured response:
            ```json
            {{
                "description": "..."
            }}
            ```
        """, max_tokens=15000, temperature=0, context="",)
        self.logger.debug(f"LLM response:\n{response}")
        response = response[len("```json"):-len("```")].strip()
        return json.loads(response)["description"]

    def __add_text(self, path, src_to_data):
        return self.mhtml_manipulator.exec(path, f"""
            (function() {{
                const style = document.createElement('style');
                style.textContent = `
                    .a11ypoc-image-text {{
                        margin-bottom: 1em;
                    }}
                `;
                document.head.appendChild(style);

                let counter = 0;
                const rootElement = document.getElementById('co_document_0');
                for (const [src, data] of Object.entries({json.dumps(src_to_data)})) {{
                    if (data.has_text === 'true') {{
                        let element = document.getElementById(data.id);
                        while (element.parentElement.tagName.toLowerCase() !== 'div') {{
                            element = element.parentElement;
                        }}
                        const paragraph = document.createElement('p');
                        paragraph.textContent = data.text;
                        paragraph.classList.add('a11ypoc-image-text');
                        element.insertAdjacentElement('afterend', paragraph);
                        counter++;
                    }}
                }}
                return counter;
            }})();
        """)
    
    def __replace_alt(self, path, src_to_data):
        return self.mhtml_manipulator.exec(path, f"""
            (function() {{
                let counter = 0;
                const rootElement = document.getElementById('co_document_0');
                for (const [src, data] of Object.entries({json.dumps(src_to_data)})) {{
                    let element = document.getElementById(data.id);
                    element.alt = data.alt;
                    counter++;
                }}
                return counter;
            }})();
        """)

    def __add_modals(self, path, src_to_data):
        return self.mhtml_manipulator.exec(path, f"""
            (function() {{
                const script = document.createElement('script');
                script.textContent = `
                    function logInfo(imageId) {{
                        console.log('Button clicked for image with ID: ' + imageId);
                    }}
                `;
                document.head.appendChild(script);
                const style = document.createElement('style');
                style.textContent = `
                    .a11ypoc-image-description {{
                        margin-bottom: 1em;
                    }}
                    .a11ypoc-image-description-button {{
                        margin-top: 0.5em;
                        padding: 0.5em 1em;
                        background-color: #007BFF;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    }}
                    .a11ypoc-image-description-button:hover {{
                        background-color: #0056b3;
                    }}
                `;
                document.head.appendChild(style);

                let counter = 0;
                const rootElement = document.getElementById('co_document_0');
                for (const [src, data] of Object.entries({json.dumps(src_to_data)})) {{
                    if (data.is_chart === 'true') {{
                        let element = document.getElementById(data.id);
                        while (element.parentElement.tagName.toLowerCase() !== 'div') {{
                            element = element.parentElement;
                        }}
                        const modalHTML = `
                            <p class="a11ypoc-image-description"><strong>${{data.description}}<strong></p>
                            <button class="a11ypoc-image-description-button" onclick="logInfo('${{data.id}}')">Show Description</button>
                        `;
                        element.insertAdjacentHTML('afterend', modalHTML);
                        counter++;
                    }}
                }}
                return counter;
            }})();
        """)
