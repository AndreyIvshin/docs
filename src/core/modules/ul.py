from core.module import Module
import time, json

class UlRemediator(Module):
    def __init__(self, mhtml_manipulator, logger_factory, screenshot_maker, llm, report):
        super().__init__(mhtml_manipulator, logger_factory)
        self.screenshot_maker = screenshot_maker
        self.llm = llm
        self.report = report

    def fix_mhtml(self, path):
        self.logger.debug(f"Starting UL remediation...")
        start_time = time.time()
        counter = 0
        
        self.logger.debug(f"Making screenshots...")
        images = self.screenshot_maker.convert(path, width=1280, chunk_height=4000)
        
        self.logger.debug(f"Extracting HTML...")
        html = self.mhtml_manipulator.exec(path, """
            (function() {
                const targetElement = document.getElementById("co_document_0");
                return targetElement ? targetElement.outerHTML : null;
            })();
        """)
        
        if html:
            self.logger.debug(f"Calling LLM...")
            response = self.__call_llm(images, html)
            
            self.logger.debug(f"LLM response: \n{response}")
            if response != "None":
                uls = []
                response = json.loads(response)
                self.logger.debug(f"Restoring contents...")
                self.__restore_content(path, response)
                
                for ul in response:
                    ul["replacement"] = self.__generate_ul(ul["data"])
                    uls.append(ul)
                response = json.dumps(uls)
                self.logger.debug(f"LLM response enriched: \n{response}")

                self.logger.debug(f"Modifying DOM...")
                counter = self.__modify_dom(path, response)
        else:
            self.logger.error(f"No co_document_0! Skipping...")

        self.logger.debug(f"UL remediation completed in {time.time() - start_time:.2f} seconds.")
        self.logger.info(f"Remediated {counter} ULs.")
        self.report["ul"] = counter
    
    def __call_llm(self, images, html):
        response = self.llm.ask(images=images,prompt=f"""
            I need you to analyze a document and identify all unordered lists based on their visual appearance. This includes:
            - Bullet points (e.g., •, -, or similar symbols) that are visually grouped together.
            - Bullet points that are grouped under headings or categories, even if the headings are not explicitly part of the list.
            - Lists that are visually structured as unordered lists, even if they are not marked up as <ul> or <li> in the HTML.
            Do not rely on the HTML markup to determine whether something is an unordered list, as the markup may not be accurate. Instead, focus on how the content looks visually.
            For each unordered list you find, provide the following structured response:
            [
                {{
                    "selector": "first clear id selector to use for replacement, like this #some_id",
                    "other_selectors": ["other id selectors to be deleted if initial selector doesn't contain all elements inside of it"],
                    "data": {{
                        "elements": [
                            {{
                                "id": "clear id selector of the list element, that contins text, like this #some_id"
                            }},
                            ...
                        ]
                    }}
                }},
                ...
            ]

            **Important Notes:**
            - Do not include any additional keys or wrappers.
            - If no clear visual grouping exists, do not include the list in the response.
            - Respond with prettified JSON only. Do not use markdown, code blocks, or any other formatting.

            HTML:
            {html}
        """, max_tokens=15000, temperature=0, context="",)
        if response.startswith("```json") and response.endswith("```"):
            response = response[len("```json"):-len("```")].strip()
        return response
    
    def __restore_content(self, path, response):
        ids = []
        for item in response:
            ul_ids = [element["id"] for element in item["data"]["elements"]]
            ids.extend(ul_ids)

        contents = json.loads(self.mhtml_manipulator.exec(path, f"""
            (function() {{
                let ids = {json.dumps(ids)};
                let contents = {{}};
                for (let id of ids) {{
                    const cleanId = id.startsWith("#") ? id.slice(1) : id;
                    const element = document.getElementById(cleanId);
                    contents[id] = element ? element.innerHTML : null;
                }}
                return JSON.stringify(contents);
            }})();
        """))

        for item in response:
            for element in item["data"]["elements"]:
                id = element["id"]
                element["content"] = contents[id]

    def __generate_ul(self, ul):
        elements = ul["elements"]
        html = f"""<style>
            .a11y-ul {{
                margin: 20px 0;
                padding: 0 20px;
                list-style: none;
            }}
            .a11y-li {{
                margin-bottom: 10px;
            }}
        </style>
        <ul class="a11y-ul">
        """
        for element in elements:
            html += f"""
                <li class="a11y-li">
                    {element["content"]}
                </li>
            """
        html += """
        </ul>
        """
        return html

    def __modify_dom(self, path, json):
        return self.mhtml_manipulator.exec(path, f"""
            (function() {{
                let counter = 0;
                const replacements = {json};
                function replaceElements(replacements) {{
                    replacements.forEach(replacement => {{
                        const element = document.querySelector(replacement.selector);
                        if (element) {{
                            const tempContainer = document.createElement("div");
                            tempContainer.innerHTML = replacement.replacement;
                            const parent = element.parentNode;
                            while (tempContainer.firstChild) {{
                                parent.insertBefore(tempContainer.firstChild, element);
                            }}
                            parent.removeChild(element);
                            counter++;
                        }}
                    }});
                }}
                function removeOtherSelectors(replacements) {{
                    replacements.forEach(replacement => {{
                        if (replacement.other_selectors) {{
                            replacement.other_selectors.forEach(selector => {{
                                const elements = document.querySelectorAll(selector);
                                elements.forEach(element => {{
                                    element.parentNode.removeChild(element);
                                }});
                            }});
                        }}
                    }});
                }}
                replaceElements(replacements);
                removeOtherSelectors(replacements);
                return counter;
            }})();
        """)
