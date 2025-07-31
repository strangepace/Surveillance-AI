#!/usr/bin/env python3
"""
Validate the prompt interpreter fix with specific test cases.
Tests the LangChain + OpenAI integration for extracting meaningful labels.
"""
import asyncio
import os
from dotenv import load_dotenv
from prompt_interpreter import interpret_multiple_prompts

# Load environment variables
load_dotenv()

async def test_prompt_interpreter_validation():
    """Test the prompt interpreter with specific validation cases."""
    print("🧪 Prompt Interpreter Validation Test")
    print("=" * 60)
    
    # Test cases from user requirements
    test_cases = [
        {
            "input": "elderly man in red hoodie with a black bag",
            "expected": ["elderly man", "red hoodie", "black bag"],
            "description": "User's specific example"
        },
        {
            "input": "person, red shirt, car",
            "expected": ["person", "red shirt", "car"],
            "description": "Simple comma-separated labels"
        },
        {
            "input": "cars and vehicles on the road",
            "expected": ["car", "vehicle", "road"],
            "description": "Natural language to labels"
        },
        {
            "input": "soldiers with weapons",
            "expected": ["soldier", "weapon"],
            "description": "Military/security context"
        },
        {
            "input": "fire and smoke in building",
            "expected": ["fire", "smoke", "building"],
            "description": "Safety/emergency context"
        }
    ]
    
    print(f"🔑 OpenAI API Key available: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    print(f"📝 Testing {len(test_cases)} validation cases...")
    print()
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 Test {i}: {test_case['description']}")
        print(f"   Input: '{test_case['input']}'")
        print(f"   Expected: {test_case['expected']}")
        
        try:
            # Test the prompt interpreter
            result = await interpret_multiple_prompts([test_case['input']])
            
            if result and len(result) > 0:
                labels = result[0].get("labels", [])
                print(f"   Actual: {labels}")
                
                # Validate results
                success = True
                for expected_label in test_case['expected']:
                    if not any(expected_label.lower() in label.lower() for label in labels):
                        print(f"   ⚠️  Missing: '{expected_label}'")
                        success = False
                
                if success:
                    print(f"   ✅ PASS: All expected labels found")
                else:
                    print(f"   ❌ FAIL: Some expected labels missing")
                
                results.append({
                    'test_case': test_case,
                    'success': success,
                    'actual_labels': labels
                })
            else:
                print(f"   ❌ FAIL: No result returned")
                results.append({
                    'test_case': test_case,
                    'success': False,
                    'actual_labels': []
                })
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({
                'test_case': test_case,
                'success': False,
                'error': str(e)
            })
        
        print()
    
    # Summary
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 SUCCESS: All prompt interpretation tests passed!")
        print("✅ The LangChain + OpenAI integration is working correctly.")
        print("✅ Meaningful labels are being extracted instead of individual characters.")
    else:
        print("⚠️  PARTIAL SUCCESS: Some tests failed.")
        print("🔧 The prompt interpreter may need further tuning.")
    
    # Show detailed results
    print("\n📋 DETAILED RESULTS:")
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{i}. {status}: {result['test_case']['description']}")
        if not result['success'] and 'error' in result:
            print(f"   Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_prompt_interpreter_validation())