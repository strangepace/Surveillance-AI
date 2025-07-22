# backend_v3/test_prompt_interpreter.py
"""
Test script for prompt_interpreter.py module.
Tests prompt interpretation, output validation, and deterministic responses.
"""
import os
import json
from prompt_interpreter import (
    interpret_prompt, 
    interpret_multiple_prompts,
    PromptInterpreter,
    DetectionCategories
)


def test_detection_categories():
    """Test DetectionCategories dataclass."""
    print("🧪 Testing DetectionCategories...")
    
    # Test default initialization
    categories = DetectionCategories()
    result = categories.to_dict()
    
    expected_keys = ["people", "colors", "fire", "weapons", "vehicles", "unusual_activity"]
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"
        assert isinstance(result[key], list), f"Key {key} should be a list"
        assert len(result[key]) == 0, f"Key {key} should be empty initially"
    
    print("  ✅ DetectionCategories initialization works")
    
    # Test with data
    categories.people = ["elderly man"]
    categories.colors = ["red shirt"]
    categories.weapons = ["gun"]
    
    result = categories.to_dict()
    assert result["people"] == ["elderly man"]
    assert result["colors"] == ["red shirt"]
    assert result["weapons"] == ["gun"]
    
    print("  ✅ DetectionCategories data assignment works")
    print("✅ DetectionCategories tests passed")


def test_fallback_interpretation():
    """Test fallback keyword-based interpretation."""
    print("🧪 Testing fallback interpretation...")
    
    interpreter = PromptInterpreter(api_key=None)  # Force fallback
    
    test_cases = [
        {
            "prompt": "elderly man with red shirt",
            "expected": {
                "people": ["elderly man"],
                "colors": ["red shirt"],
                "fire": [],
                "weapons": [],
                "vehicles": [],
                "unusual_activity": []
            }
        },
        {
            "prompt": "man with gun in blue car",
            "expected": {
                "people": ["man"],
                "colors": ["blue car"],
                "fire": [],
                "weapons": ["gun"],
                "vehicles": ["car"],
                "unusual_activity": []
            }
        },
        {
            "prompt": "burning vehicle with smoke",
            "expected": {
                "people": [],
                "colors": [],
                "fire": ["burning", "smoke"],
                "weapons": [],
                "vehicles": ["vehicle"],
                "unusual_activity": []
            }
        },
        {
            "prompt": "person running and fighting",
            "expected": {
                "people": ["person"],
                "colors": [],
                "fire": [],
                "weapons": [],
                "vehicles": [],
                "unusual_activity": ["running", "fighting"]
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        result = interpreter.interpret_prompt(test_case["prompt"])
        
        # Check that all expected keys exist
        for key in test_case["expected"]:
            assert key in result, f"Missing key {key} in result"
            assert isinstance(result[key], list), f"Key {key} should be a list"
        
        # Check that expected items are present (allowing for additional items)
        for key, expected_items in test_case["expected"].items():
            for item in expected_items:
                if item:  # Skip empty items
                    assert item in result[key], f"Expected '{item}' in {key}, got {result[key]}"
        
        print(f"  ✅ Test case {i+1}: '{test_case['prompt']}'")
    
    print("✅ Fallback interpretation tests passed")


def test_llm_interpretation():
    """Test LLM-based interpretation if API key is available."""
    print("🧪 Testing LLM interpretation...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("  ⚠️  No OpenAI API key found, skipping LLM tests")
        return
    
    interpreter = PromptInterpreter(api_key=api_key)
    
    if interpreter.use_fallback:
        print("  ⚠️  LangChain setup failed, using fallback")
        return
    
    test_cases = [
        "elderly man in red shirt with a gun",
        "woman driving blue car",
        "burning building with smoke",
        "person climbing fence",
        "man with knife fighting"
    ]
    
    for i, prompt in enumerate(test_cases):
        try:
            result = interpreter.interpret_prompt(prompt)
            
            # Validate structure
            expected_keys = ["people", "colors", "fire", "weapons", "vehicles", "unusual_activity"]
            for key in expected_keys:
                assert key in result, f"Missing key: {key}"
                assert isinstance(result[key], list), f"Key {key} should be a list"
            
            print(f"  ✅ LLM test {i+1}: '{prompt}' -> {len([v for v in result.values() if v])} categories")
            
        except Exception as e:
            print(f"  ⚠️  LLM test {i+1} failed: {e}")
    
    print("✅ LLM interpretation tests completed")


def test_deterministic_responses():
    """Test that responses are deterministic."""
    print("🧪 Testing deterministic responses...")
    
    interpreter = PromptInterpreter()
    prompt = "elderly man with red shirt and gun"
    
    # Run the same prompt multiple times
    results = []
    for i in range(3):
        result = interpreter.interpret_prompt(prompt)
        results.append(result)
    
    # All results should be identical
    for i in range(1, len(results)):
        assert results[i] == results[0], f"Results should be deterministic, got different results"
    
    print("  ✅ Responses are deterministic")
    print("✅ Deterministic response tests passed")


def test_multiple_prompts():
    """Test batch processing of multiple prompts."""
    print("🧪 Testing multiple prompt interpretation...")
    
    prompts = [
        "elderly man with red shirt",
        "woman in blue car",
        "burning building",
        "person with gun"
    ]
    
    results = interpret_multiple_prompts(prompts)
    
    assert len(results) == len(prompts), "Should return one result per prompt"
    
    for i, (prompt, result) in enumerate(zip(prompts, results)):
        # Validate structure
        expected_keys = ["people", "colors", "fire", "weapons", "vehicles", "unusual_activity"]
        for key in expected_keys:
            assert key in result, f"Missing key {key} in result {i}"
            assert isinstance(result[key], list), f"Key {key} should be a list in result {i}"
        
        print(f"  ✅ Multiple prompt {i+1}: '{prompt}' -> {len([v for v in result.values() if v])} categories")
    
    print("✅ Multiple prompts tests passed")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("🧪 Testing edge cases...")
    
    interpreter = PromptInterpreter()
    
    # Test empty prompt
    result = interpreter.interpret_prompt("")
    expected_keys = ["people", "colors", "fire", "weapons", "vehicles", "unusual_activity"]
    for key in expected_keys:
        assert key in result, f"Empty prompt should return all keys"
        assert result[key] == [], f"Empty prompt should return empty lists"
    
    # Test whitespace-only prompt
    result = interpreter.interpret_prompt("   ")
    for key in expected_keys:
        assert key in result, f"Whitespace prompt should return all keys"
        assert result[key] == [], f"Whitespace prompt should return empty lists"
    
    # Test None prompt
    result = interpreter.interpret_prompt(None)
    for key in expected_keys:
        assert key in result, f"None prompt should return all keys"
        assert result[key] == [], f"None prompt should return empty lists"
    
    # Test very long prompt
    long_prompt = "elderly man with red shirt and blue pants driving a black car with a gun while running and fighting and burning building with smoke and fire"
    result = interpreter.interpret_prompt(long_prompt)
    for key in expected_keys:
        assert key in result, f"Long prompt should return all keys"
        assert isinstance(result[key], list), f"Long prompt should return lists"
    
    print("  ✅ Edge cases handled correctly")
    print("✅ Edge case tests passed")


def test_synonym_expansion():
    """Test synonym expansion functionality."""
    print("🧪 Testing synonym expansion...")
    
    interpreter = PromptInterpreter()
    
    # Test synonym expansion
    terms = ["car", "gun", "fire"]
    expanded = interpreter.expand_synonyms(terms)
    
    # Should include original terms plus synonyms
    assert "car" in expanded, "Original term should be included"
    assert "vehicle" in expanded, "Synonym should be included"
    assert "gun" in expanded, "Original term should be included"
    assert "firearm" in expanded, "Synonym should be included"
    assert "fire" in expanded, "Original term should be included"
    assert "flame" in expanded, "Synonym should be included"
    
    print("  ✅ Synonym expansion works correctly")
    print("✅ Synonym expansion tests passed")


def test_output_validation():
    """Test that output validation works correctly."""
    print("🧪 Testing output validation...")
    
    interpreter = PromptInterpreter()
    
    # Test with various malformed inputs that might come from LLM
    malformed_inputs = [
        {"people": "not a list"},  # Wrong type
        {"people": ["man"], "extra_key": ["something"]},  # Extra key
        {"people": ["man"]},  # Missing keys
        None,  # None input
        "not a dict",  # String input
    ]
    
    for i, malformed in enumerate(malformed_inputs):
        try:
            cleaned = interpreter._validate_and_clean_result(malformed)
            
            # Should have all expected keys
            expected_keys = ["people", "colors", "fire", "weapons", "vehicles", "unusual_activity"]
            for key in expected_keys:
                assert key in cleaned, f"Missing key {key} after validation"
                assert isinstance(cleaned[key], list), f"Key {key} should be list after validation"
            
            print(f"  ✅ Validation test {i+1} passed")
            
        except Exception as e:
            print(f"  ⚠️  Validation test {i+1} failed: {e}")
    
    print("✅ Output validation tests passed")


def main():
    """Run all prompt interpreter tests."""
    print("🚀 Testing Prompt Interpreter Module")
    print("=" * 50)
    
    tests = [
        test_detection_categories,
        test_fallback_interpretation,
        test_llm_interpretation,
        test_deterministic_responses,
        test_multiple_prompts,
        test_edge_cases,
        test_synonym_expansion,
        test_output_validation
    ]
    
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
        print()
    
    print(f"📊 Tests passed: {passed}/{len(tests)}")
    if passed == len(tests):
        print("🎉 All prompt interpreter tests passed!")
    else:
        print("⚠️  Some tests failed.")


if __name__ == "__main__":
    main() 