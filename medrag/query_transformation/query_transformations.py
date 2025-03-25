from ollama import chat, ChatResponse

def rewrite_query(original_query: str):
    query_rewrite_template = f"""You are an AI assistant tasked with reformulating user queries to improve retrieval in a RAG system. 
    Given the original query, rewrite it to be more specific, detailed, and likely to retrieve relevant information. Do not add extra details, just return the rewritten query.

    Original query: {original_query}

    Rewritten query:"""

    response: ChatResponse = chat(model='llama3.2:3b', messages=[
        {
            'role': 'user',
            'content': query_rewrite_template,
        },
    ])

    return response.message.content

def generate_step_back_query(original_query):
    step_back_template = f"""You are an AI assistant tasked with generating broader, more general queries to improve context retrieval in a RAG system.
    Given the original query, generate a step-back query that is more general and can help retrieve relevant background information. Do not add extra details, just return the step-back query.

    Original query: {original_query}

    Step-back query:"""

    response: ChatResponse = chat(model='llama3.2:3b', messages=[
        {
            'role': 'user',
            'content': step_back_template,
        },
    ])

    return response.message.content

def decompose_query(original_query: str):
    subquery_decomposition_template = f"""You are an AI assistant tasked with breaking down complex queries into simpler sub-queries for a RAG system.
    Given the original query, decompose it into 2-4 simpler sub-queries that, when answered together, would provide a comprehensive response to the original query. Do not add extra details, just return the sub-queries.

    Original query: {original_query}

    example: What are the impacts of climate change on the environment?

    Sub-queries:
    1. What are the impacts of climate change on biodiversity?
    2. How does climate change affect the oceans?
    3. What are the effects of climate change on agriculture?
    4. What are the impacts of climate change on human health?"""

    response: ChatResponse = chat(model='llama3.2:3b', messages=[
        {
            'role': 'user',
            'content': subquery_decomposition_template,
        },
    ])

    return response.message.content
