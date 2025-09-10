import requests, base64

class OpenAIClient:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url

    def ask(self, prompt, images, max_tokens, temperature, context):
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={"messages": [
                    {"role": "system", "content": context},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        *self.__base64_image_parts(images)
                    ]}
                ], "max_tokens": max_tokens, "temperature": temperature }
            )
            response.raise_for_status()
            result = response.json()
            assistant_response = result["choices"][0]["message"]["content"].strip()
            return assistant_response
        except requests.exceptions.HTTPError as http_err:
            error_message = response.text if response.content else str(http_err)
            raise Exception(f"HTTP Error: {http_err}; Details: {error_message}")
        except requests.exceptions.RequestException as req_err:
            raise Exception(f"Request Error: {req_err}")
        except KeyError:
            raise Exception("Error: Unexpected response structure.")
        except ValueError as val_err:
            raise Exception(f"Value Error: {val_err}")
    
    def __base64_image_parts(self, images):
        image_parts = []
        for _, image_path in enumerate(images, start=1):
            base64_image = None
            try:
                with open(image_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            except Exception as e:
                raise ValueError(f"Failed to encode image {image_path}: {e}")
            image_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
            })
        return image_parts
