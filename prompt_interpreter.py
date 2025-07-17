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
openai = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

# Initialize Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT_TEMPLATE = """
You are an AI surveillance analyst. Analyze the following video content based on the user's question.

Question: "{prompt}"

Video Analysis Results:
- Video Duration: {duration_seconds} seconds
- Total Labels Detected: {total_labels}
- Total Objects Detected: {total_objects}
- Total Shots: {total_shots}

Detected Labels (with timestamps):
{labels_summary}

Detected Objects (with timestamps):
{objects_summary}

Shot Changes:
{shots_summary}

Based on the detected events and objects, provide a comprehensive answer to the question. Include:
1. A direct answer to the question
2. Relevant timestamps where key events occur
3. Confidence levels of the detections
4. Any important patterns or sequences observed

If the detected events do not contain enough information to answer the question, state that clearly and explain what additional information would be needed.

Answer:
"""

async def interpret_prompt(prompt: str, video_analysis_results: Dict[str, Any], model: str) -> str:
    """
    Interpret the video analysis results in the context of the user's prompt.
    Returns a natural language string as the final answer.
    """
    try:
        # Extract metadata
        metadata = video_analysis_results.get("metadata", {})
        video_metadata = metadata.get("video_metadata", {})
        duration_seconds = video_metadata.get("duration_seconds", 0)
        
        # Extract summary
        summary = video_analysis_results.get("summary", {})
        total_labels = summary.get("total_labels", 0)
        total_objects = summary.get("total_objects", 0)
        total_shots = summary.get("total_shots", 0)
        
        # Process labels
        labels = video_analysis_results.get("labels", [])
        labels_summary = []
        for label in labels:
            start_time = label.get("start_time", 0)
            end_time = label.get("end_time", 0)
            confidence = label.get("confidence", 0)
            label_name = label.get("label", "Unknown")
            labels_summary.append(f"- {label_name} (confidence: {confidence:.2f}) at {start_time:.1f}s-{end_time:.1f}s")
        
        labels_str = "\n".join(labels_summary) if labels_summary else "No labels detected"
        
        # Process objects
        objects = video_analysis_results.get("objects", [])
        objects_summary = []
        for obj in objects:
            start_time = obj.get("start_time", 0)
            end_time = obj.get("end_time", 0)
            confidence = obj.get("confidence", 0)
            object_name = obj.get("label", "Unknown")
            objects_summary.append(f"- {object_name} (confidence: {confidence:.2f}) at {start_time:.1f}s-{end_time:.1f}s")
        
        objects_str = "\n".join(objects_summary) if objects_summary else "No objects detected"
        
        # Process shots
        shots = video_analysis_results.get("shots", [])
        shots_summary = []
        for shot in shots:
            start_time = shot.get("start_time", 0)
            end_time = shot.get("end_time", 0)
            duration = shot.get("duration", 0)
            shots_summary.append(f"- Shot at {start_time:.1f}s-{end_time:.1f}s (duration: {duration:.1f}s)")
        
        shots_str = "\n".join(shots_summary) if shots_summary else "No shot changes detected"
        
        # Create the enhanced prompt
        final_prompt = PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=["prompt", "duration_seconds", "total_labels", "total_objects", "total_shots", "labels_summary", "objects_summary", "shots_summary"]
        )
        
        if model == "chatgpt":
            # We can go back to using LLMChain now that we have the correct class/model pair
            chain = LLMChain(llm=openai, prompt=final_prompt)
            result = await chain.arun(
                prompt=prompt,
                duration_seconds=duration_seconds,
                total_labels=total_labels,
                total_objects=total_objects,
                total_shots=total_shots,
                labels_summary=labels_str,
                objects_summary=objects_str,
                shots_summary=shots_str
            )
            
        elif model == "gemini":
            # Use the correct Gemini API
            gemini_model = genai.GenerativeModel('gemini-pro')
            filled_prompt = final_prompt.format(
                prompt=prompt,
                duration_seconds=duration_seconds,
                total_labels=total_labels,
                total_objects=total_objects,
                total_shots=total_shots,
                labels_summary=labels_str,
                objects_summary=objects_str,
                shots_summary=shots_str
            )
            response = gemini_model.generate_content(filled_prompt)
            result = response.text
            
        else:
            raise ValueError(f"Unsupported model: {model}")
        
        return result.strip()
            
    except Exception as e:
        logger.error(f"Error interpreting prompt: {e}")
        raise Exception(f"Failed to interpret prompt: {e}")