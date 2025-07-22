# backend_v3/prompt_interpreter.py
"""
LangChain-powered prompt interpreter for backend-v3.
Converts natural language prompts into structured detection categories.
"""
import os
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class DetectionCategories:
    """Structured detection categories for surveillance prompts."""
    people: List[str] = field(default_factory=list)
    colors: List[str] = field(default_factory=list)
    fire: List[str] = field(default_factory=list)
    weapons: List[str] = field(default_factory=list)
    vehicles: List[str] = field(default_factory=list)
    unusual_activity: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, List[str]]:
        """Convert to dictionary format."""
        return {
            "people": self.people,
            "colors": self.colors,
            "fire": self.fire,
            "weapons": self.weapons,
            "vehicles": self.vehicles,
            "unusual_activity": self.unusual_activity
        }


class PromptInterpreter:
    """LangChain-powered prompt interpreter for surveillance queries."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the prompt interpreter.
        
        Args:
            api_key (str): OpenAI API key (defaults to environment variable)
            model (str): LLM model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.llm = None
        self.prompt_template = None
        self.output_parser = None
        self.synonym_dict = self._load_synonyms()
        
        if not self.api_key:
            print("⚠️  No OpenAI API key found. Using fallback keyword matching.")
            self.use_fallback = True
        else:
            self.use_fallback = False
            self._setup_langchain()
    
    def _load_synonyms(self) -> Dict[str, List[str]]:
        """Load synonym dictionary for better matching."""
        return {
            # People synonyms
            "person": ["person", "human", "individual", "someone"],
            "man": ["man", "male", "guy", "gentleman"],
            "woman": ["woman", "female", "lady", "girl"],
            "elderly": ["elderly", "old", "senior", "aged"],
            "child": ["child", "kid", "boy", "girl", "youngster"],
            
            # Vehicle synonyms
            "car": ["car", "vehicle", "automobile", "sedan"],
            "truck": ["truck", "pickup", "lorry"],
            "motorcycle": ["motorcycle", "bike", "motorbike"],
            "bicycle": ["bicycle", "bike", "cycle"],
            
            # Weapon synonyms
            "gun": ["gun", "firearm", "weapon", "pistol", "rifle"],
            "knife": ["knife", "blade", "weapon"],
            
            # Fire synonyms
            "fire": ["fire", "flame", "burning", "blaze"],
            "smoke": ["smoke", "smoking"],
            
            # Color synonyms
            "red": ["red", "crimson", "scarlet"],
            "blue": ["blue", "navy", "azure"],
            "green": ["green", "emerald", "forest"],
            "yellow": ["yellow", "golden", "amber"],
            "black": ["black", "dark"],
            "white": ["white", "pale"],
            "brown": ["brown", "tan", "beige"],
            "gray": ["gray", "grey", "silver"],
            
            # Activity synonyms
            "running": ["running", "sprinting", "jogging"],
            "walking": ["walking", "strolling"],
            "fighting": ["fighting", "brawling", "struggling"],
            "climbing": ["climbing", "scaling"],
            "jumping": ["jumping", "leaping"],
            "falling": ["falling", "dropping"]
        }
    
    def _setup_langchain(self):
        """Setup LangChain with OpenAI."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import JsonOutputParser
            
            self.llm = ChatOpenAI(
                model=self.model,
                temperature=0,  # Deterministic responses
                api_key=self.api_key
            )
            
            # Create the prompt template
            self.prompt_template = ChatPromptTemplate.from_messages([
                ("system", self._get_system_prompt()),
                ("user", "Extract detection categories from this prompt: {prompt}")
            ])
            
            # Setup JSON output parser
            self.output_parser = JsonOutputParser()
            
            print("✅ LangChain setup complete")
            
        except ImportError as e:
            print(f"⚠️  LangChain not available: {e}")
            self.use_fallback = True
        except Exception as e:
            print(f"⚠️  LangChain setup failed: {e}")
            self.use_fallback = True
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for LLM."""
        return """You are a surveillance AI assistant that extracts structured detection categories from natural language prompts.

Your task is to analyze the user's prompt and extract relevant information into these categories:

1. people: Any descriptions of people (e.g., "elderly man", "woman", "child")
2. colors: Any color descriptions (e.g., "red shirt", "blue car")
3. fire: Any fire-related terms (e.g., "burning", "flames", "smoke")
4. weapons: Any weapon descriptions (e.g., "gun", "knife", "weapon")
5. vehicles: Any vehicle descriptions (e.g., "car", "truck", "motorcycle")
6. unusual_activity: Any unusual or suspicious activities (e.g., "fighting", "climbing", "running")

Rules:
- Extract specific terms, not generic ones
- Include relevant adjectives with nouns (e.g., "red shirt" not just "shirt")
- If a category has no relevant terms, use an empty list
- Be precise and avoid duplicates
- Consider synonyms and related terms

Return ONLY a valid JSON object with these exact keys: people, colors, fire, weapons, vehicles, unusual_activity

Example:
Input: "elderly man in red shirt with a gun"
Output: {
  "people": ["elderly man"],
  "colors": ["red shirt"],
  "fire": [],
  "weapons": ["gun"],
  "vehicles": [],
  "unusual_activity": []
}"""
    
    def interpret_prompt(self, prompt: str) -> Dict[str, List[str]]:
        """
        Interpret a natural language prompt into structured detection categories.
        
        Args:
            prompt (str): Natural language prompt
            
        Returns:
            Dict[str, List[str]]: Structured detection categories
        """
        if not prompt or not prompt.strip():
            return DetectionCategories().to_dict()
        
        prompt = prompt.strip().lower()
        
        if self.use_fallback:
            return self._fallback_interpretation(prompt)
        else:
            return self._llm_interpretation(prompt)
    
    def _llm_interpretation(self, prompt: str) -> Dict[str, List[str]]:
        """Use LangChain LLM for interpretation."""
        try:
            if not self.llm or not self.prompt_template or not self.output_parser:
                print("⚠️  LangChain components not properly initialized")
                return self._fallback_interpretation(prompt)
            
            # Create the chain
            chain = self.prompt_template | self.llm | self.output_parser
            
            # Run the chain
            result = chain.invoke({"prompt": prompt})
            
            # Validate and clean the result
            return self._validate_and_clean_result(result)
            
        except Exception as e:
            print(f"⚠️  LLM interpretation failed: {e}")
            return self._fallback_interpretation(prompt)
    
    def _fallback_interpretation(self, prompt: str) -> Dict[str, List[str]]:
        """Fallback keyword-based interpretation."""
        categories = DetectionCategories()
        
        # Simple keyword matching
        words = prompt.split()
        
        # People detection
        people_keywords = ["man", "woman", "person", "child", "elderly", "old", "young"]
        for word in words:
            if any(keyword in word for keyword in people_keywords):
                # Get surrounding context
                idx = words.index(word)
                context = " ".join(words[max(0, idx-2):idx+3])
                categories.people.append(context)
        
        # Color detection
        color_keywords = ["red", "blue", "green", "yellow", "black", "white", "brown", "gray", "grey"]
        for word in words:
            if word in color_keywords:
                # Get color + object context
                idx = words.index(word)
                if idx + 1 < len(words):
                    color_obj = f"{word} {words[idx+1]}"
                    categories.colors.append(color_obj)
        
        # Weapon detection
        weapon_keywords = ["gun", "knife", "weapon", "firearm"]
        for word in words:
            if word in weapon_keywords:
                categories.weapons.append(word)
        
        # Vehicle detection
        vehicle_keywords = ["car", "truck", "motorcycle", "bike", "vehicle"]
        for word in words:
            if word in vehicle_keywords:
                categories.vehicles.append(word)
        
        # Fire detection
        fire_keywords = ["fire", "burning", "flame", "smoke"]
        for word in words:
            if word in fire_keywords:
                categories.fire.append(word)
        
        # Activity detection
        activity_keywords = ["running", "fighting", "climbing", "jumping", "falling"]
        for word in words:
            if word in activity_keywords:
                categories.unusual_activity.append(word)
        
        return categories.to_dict()
    
    def _validate_and_clean_result(self, result: Dict) -> Dict[str, List[str]]:
        """Validate and clean LLM result."""
        expected_keys = ["people", "colors", "fire", "weapons", "vehicles", "unusual_activity"]
        
        # Ensure all expected keys exist
        for key in expected_keys:
            if key not in result:
                result[key] = []
            elif not isinstance(result[key], list):
                result[key] = []
        
        # Remove any extra keys
        cleaned_result = {key: result[key] for key in expected_keys if key in result}
        
        # Ensure all values are strings
        for key in cleaned_result:
            cleaned_result[key] = [str(item).strip() for item in cleaned_result[key] if item]
        
        return cleaned_result
    
    def expand_synonyms(self, terms: List[str]) -> List[str]:
        """Expand terms using synonym dictionary."""
        expanded = []
        for term in terms:
            expanded.append(term)
            # Check for synonyms
            for synonym_key, synonyms in self.synonym_dict.items():
                if synonym_key in term.lower():
                    for synonym in synonyms:
                        if synonym not in expanded:
                            expanded.append(synonym)
        return list(set(expanded))  # Remove duplicates
    
    def interpret_multiple(self, prompts: List[str]) -> List[Dict[str, List[str]]]:
        """
        Interpret multiple prompts at once.
        
        Args:
            prompts (List[str]): List of natural language prompts
            
        Returns:
            List[Dict[str, List[str]]]: List of structured detection categories
        """
        results = []
        for prompt in prompts:
            result = self.interpret_prompt(prompt)
            results.append(result)
        return results


# Convenience function for easy usage
def interpret_prompt(prompt: str, api_key: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Convenience function to interpret a single prompt.
    
    Args:
        prompt (str): Natural language prompt
        api_key (str): OpenAI API key (optional)
        
    Returns:
        Dict[str, List[str]]: Structured detection categories
    """
    interpreter = PromptInterpreter(api_key=api_key)
    return interpreter.interpret_prompt(prompt)


def interpret_multiple_prompts(prompts: List[str], api_key: Optional[str] = None) -> List[Dict[str, List[str]]]:
    """
    Convenience function to interpret multiple prompts.
    
    Args:
        prompts (List[str]): List of natural language prompts
        api_key (str): OpenAI API key (optional)
        
    Returns:
        List[Dict[str, List[str]]]: List of structured detection categories
    """
    interpreter = PromptInterpreter(api_key=api_key)
    return interpreter.interpret_multiple(prompts) 