from ollama import chat, ChatResponse


class QABasePipeline:
    def generate_response(self, query: str):
        prompt = f"""
            Provide health recommendations based on the patient's information: {query}.
            In case this information is not related to the health or personal data, just respond: 'You haven't provided medical symptoms and data. Try again.'
        """

        response: ChatResponse = chat(model='llama3.2:3b', messages=[
            {
                "role": "system", 
                "content": """
                    You are an expert in producing Wiki-articles based on given content.    
                """
            },
            {
                "role": "user",
                "content": prompt
            },
        ])

        return response.message.content