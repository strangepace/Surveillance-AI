# We are implementing your suggestion to use the ChatOpenAI class.

from langchain_openai import ChatOpenAI # Updated import for newer LangChain version
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os
import logging
from typing import Dict, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)

# 2. Use the ChatOpenAI class with the "gpt-3.5-turbo" model
openai = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

# Initialize Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT_TEMPLATE = """
Answer the following question based on the events detected in a surveillance video.

Question: "{prompt}"

Detected Events & Objects (Keywords):
{keywords}

Based on the detected events, provide a concise, natural language answer to the question.
If the detected events do not contain enough information to answer the question, state that clearly.

Answer:
"""

async def interpret_prompt(prompt: str, video_analysis_results: Dict[str, Any], model: str) -> str:
    """
    Interpret the video analysis results in the context of the user's prompt.
    Returns a natural language string as the final answer.
    """
    try:
        labels = [d['label'] for d in video_analysis_results.get('labels', [])]
        objects = [d['label'] for d in video_analysis_results.get('objects', [])]
        keyword_list = sorted(list(set(labels + objects)))
        keywords_str = ", ".join(keyword_list)

        if not keywords_str:
            keywords_str = "No objects or events were detected in the video."

        final_prompt = PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=["prompt", "keywords"]
        )
        
        if model == "chatgpt":
            # We can go back to using LLMChain now that we have the correct class/model pair
            chain = LLMChain(llm=openai, prompt=final_prompt)
            result = await chain.arun(prompt=prompt, keywords=keywords_str)
            
        elif model == "gemini":
            gemini_model = genai.GenerativeModel('gemini-pro')
            filled_prompt = final_prompt.format(prompt=prompt, keywords=keywords_str)
            response = await gemini_model.generate_content_async(filled_prompt)
            result = response.text
            
        else:
            raise ValueError(f"Unsupported model: {model}")
        
        return result.strip()
            
    except Exception as e:
        logger.error(f"Error interpreting prompt: {e}")
        raise Exception(f"Failed to interpret prompt: {e}")