# backend_v3/prompt_interpreter.py
"""
LangChain-powered prompt interpreter for backend-v3.
Converts natural language prompts into structured detection categories.
"""

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os
import logging
from typing import Dict, Any, List
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Use the ChatOpenAI class with the "gpt-3.5-turbo" model
openai = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)

# Initialize Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# New prompt template for extracting meaningful labels
LABEL_EXTRACTION_TEMPLATE = """
You are an AI surveillance analyst. Extract meaningful detection labels from the given natural language prompt.

User Prompt: "{prompt}"

Extract all meaningful objects, people, actions, and attributes that should be detected in video footage.
Return ONLY a comma-separated list of individual labels, with no explanations or additional text.

Examples:
- "elderly man in red hoodie with black bag" → "elderly man,red hoodie,black bag"
- "cars and vehicles on the road" → "car,vehicle,road"
- "soldiers with weapons" → "soldier,weapon"
- "fire and smoke in building" → "fire,smoke,building"

Extracted labels:
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
            # Use LLMChain with the correct class/model pair
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

async def interpret_multiple_prompts(prompts: List[str]) -> List[Dict[str, str]]:
    """
    Interpret multiple prompts using LangChain + OpenAI to extract meaningful labels.
    Returns a list of categorized prompts with extracted labels.
    """
    try:
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("⚠️ OpenAI API key not found, using fallback keyword extraction")
            return _fallback_keyword_extraction(prompts)
        
        # Create label extraction prompt
        label_prompt = PromptTemplate(
            template=LABEL_EXTRACTION_TEMPLATE,
            input_variables=["prompt"]
        )
        
        # Create LLM chain
        chain = LLMChain(llm=openai, prompt=label_prompt)
        
        categories = []
        for prompt in prompts:
            try:
                # Extract labels using LangChain
                result = await chain.arun(prompt=prompt)
                
                # Parse the comma-separated labels
                labels = [label.strip() for label in result.split(',') if label.strip()]
                
                # Determine category based on extracted labels
                category = _determine_category(labels)
                
                categories.append({
                    "prompt": prompt,
                    "category": category,
                    "labels": labels
                })
                
                logger.info(f"✅ Extracted labels from '{prompt}': {labels}")
                
            except Exception as e:
                logger.error(f"❌ Error processing prompt '{prompt}': {e}")
                # Fallback to simple categorization
                category = _simple_categorization(prompt)
                categories.append({
                    "prompt": prompt,
                    "category": category,
                    "labels": [prompt]  # Use original prompt as fallback
                })
        
        return categories
        
    except Exception as e:
        logger.error(f"Error interpreting multiple prompts: {e}")
        return _fallback_keyword_extraction(prompts)

def _fallback_keyword_extraction(prompts: List[str]) -> List[Dict[str, str]]:
    """
    Fallback method when LangChain is not available.
    """
    categories = []
    for prompt in prompts:
        # Simple categorization logic
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['person', 'people', 'man', 'woman', 'child', 'elderly']):
            category = "person"
        elif any(word in prompt_lower for word in ['car', 'vehicle', 'truck', 'bus', 'motorcycle']):
            category = "vehicle"
        elif any(word in prompt_lower for word in ['weapon', 'gun', 'knife', 'dangerous']):
            category = "security"
        elif any(word in prompt_lower for word in ['fire', 'smoke', 'accident', 'fall']):
            category = "safety"
        elif any(word in prompt_lower for word in ['crowd', 'group', 'gathering']):
            category = "crowd"
        else:
            category = "general"
        
        categories.append({
            "prompt": prompt,
            "category": category,
            "labels": [prompt]  # Use original prompt as fallback
        })
    
    return categories

def _determine_category(labels: List[str]) -> str:
    """
    Determine category based on extracted labels.
    """
    label_text = " ".join(labels).lower()
    
    if any(word in label_text for word in ['person', 'people', 'man', 'woman', 'child', 'elderly', 'human']):
        return "person"
    elif any(word in label_text for word in ['car', 'vehicle', 'truck', 'bus', 'motorcycle', 'automobile']):
        return "vehicle"
    elif any(word in label_text for word in ['weapon', 'gun', 'knife', 'dangerous', 'threat']):
        return "security"
    elif any(word in label_text for word in ['fire', 'smoke', 'accident', 'fall', 'hazard']):
        return "safety"
    elif any(word in label_text for word in ['crowd', 'group', 'gathering', 'assembly']):
        return "crowd"
    else:
        return "general"

def _simple_categorization(prompt: str) -> str:
    """
    Simple categorization for fallback.
    """
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ['person', 'people', 'man', 'woman', 'child', 'elderly']):
        return "person"
    elif any(word in prompt_lower for word in ['car', 'vehicle', 'truck', 'bus', 'motorcycle']):
        return "vehicle"
    elif any(word in prompt_lower for word in ['weapon', 'gun', 'knife', 'dangerous']):
        return "security"
    elif any(word in prompt_lower for word in ['fire', 'smoke', 'accident', 'fall']):
        return "safety"
    elif any(word in prompt_lower for word in ['crowd', 'group', 'gathering']):
        return "crowd"
    else:
        return "general"

# Keep the original PROMPT_TEMPLATE for backward compatibility
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