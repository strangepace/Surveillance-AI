# backend_v3/demo_prompt_interpreter.py
"""
Demo script for prompt_interpreter.py module.
Shows how to interpret natural language prompts into structured detection categories.
"""
import json
from .prompt_interpreter import interpret_prompt, interpret_multiple_prompts, PromptInterpreter


def main():
    """Demo the prompt interpreter functionality."""
    print("🎯 Prompt Interpreter Demo")
    print("=" * 40)
    
    # Test cases with expected outputs
    test_cases = [
        {
            "prompt": "elderly man with red shirt",
            "description": "Basic people and color detection"
        },
        {
            "prompt": "man with gun in blue car",
            "description": "People, weapons, colors, and vehicles"
        },
        {
            "prompt": "burning vehicle with smoke",
            "description": "Fire detection and vehicles"
        },
        {
            "prompt": "person running and fighting",
            "description": "People and unusual activities"
        },
        {
            "prompt": "woman with knife climbing fence",
            "description": "Complex multi-category detection"
        },
        {
            "prompt": "elderly man in red shirt with a gun",
            "description": "Example from requirements"
        }
    ]
    
    print("🔍 Testing individual prompts:")
    print("-" * 30)
    
    for i, test_case in enumerate(test_cases):
        prompt = test_case["prompt"]
        description = test_case["description"]
        
        print(f"\n{i+1}. {description}")
        print(f"   Prompt: '{prompt}'")
        
        try:
            result = interpret_prompt(prompt)
            
            # Count non-empty categories
            non_empty = {k: v for k, v in result.items() if v}
            category_count = len(non_empty)
            
            print(f"   Result: {category_count} categories detected")
            
            # Show detailed results
            for category, items in result.items():
                if items:
                    print(f"      {category}: {items}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test batch processing
    print(f"\n🔍 Testing batch processing:")
    print("-" * 30)
    
    prompts = [
        "elderly man with red shirt",
        "woman in blue car", 
        "burning building",
        "person with gun"
    ]
    
    try:
        results = interpret_multiple_prompts(prompts)
        
        print(f"Processed {len(prompts)} prompts:")
        for i, (prompt, result) in enumerate(zip(prompts, results)):
            non_empty = {k: v for k, v in result.items() if v}
            print(f"   {i+1}. '{prompt}' -> {len(non_empty)} categories")
            
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
    
    # Test synonym expansion
    print(f"\n🔍 Testing synonym expansion:")
    print("-" * 30)
    
    interpreter = PromptInterpreter()
    
    test_terms = ["car", "gun", "fire", "man"]
    expanded = interpreter.expand_synonyms(test_terms)
    
    print(f"Original terms: {test_terms}")
    print(f"Expanded terms: {expanded}")
    
    # Test edge cases
    print(f"\n🔍 Testing edge cases:")
    print("-" * 30)
    
    edge_cases = [
        ("", "Empty string"),
        ("   ", "Whitespace only"),
        ("very long prompt with many words describing elderly man with red shirt and blue pants driving a black car with a gun while running and fighting", "Very long prompt")
    ]
    
    for prompt, description in edge_cases:
        try:
            result = interpret_prompt(prompt)
            non_empty = {k: v for k, v in result.items() if v}
            print(f"   '{description}': {len(non_empty)} categories")
        except Exception as e:
            print(f"   '{description}': Error - {e}")
    
    print(f"\n🎉 Demo completed!")
    print("The prompt interpreter successfully converts natural language queries into structured detection categories.")


if __name__ == "__main__":
    main() 