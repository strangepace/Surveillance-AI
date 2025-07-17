#!/usr/bin/env python3ti-Prompt Analysis Example
Demonstrates breaking down complex queries into sub-queries
"ort re
from typing import Dict, List

def parse_complex_query(query: str) -> Dict[str, List[str]]:
  arse complex query into sub-components   components =[object Object]
    person: [],
      clothing': [],
     objects': [],
     actions: [],
      vehicles': [],
       locations': [],
    colors': [],
      gender':]
    }
    
    # Extract colors
    color_pattern = r\b(red|blue|green|yellow|brown|black|white|orange|purple|pink)\b'
    colors = re.findall(color_pattern, query.lower())
    components[colors'] = colors
    
    # Extract gender
    if 'male' in query.lower():
        components[gender].append(male)
    eliffemale' in query.lower():
        components[gender'].append('female')
        
    # Extract clothing
    clothing_pattern = rb(jacket|shirt|pants|dress|hat|shoes|boots|coat)\b'
    clothing = re.findall(clothing_pattern, query.lower())
    components['clothing'] = clothing
    
    # Extract objects
    object_pattern = r'\b(bag|backpack|purse|phone|keys|wallet|umbrella|book)\b objects = re.findall(object_pattern, query.lower())
    components['objects]= objects
    
    # Extract vehicles
    vehicle_pattern = rb(car|truck|bus|motorcycle|bike|bicycle)\b'
    vehicles = re.findall(vehicle_pattern, query.lower())
    components['vehicles'] = vehicles
    
    # Extract actions
    action_pattern = r'\b(walking|running|entering|exiting|sitting|standing|carrying|holding)\b actions = re.findall(action_pattern, query.lower())
    components['actions]= actions
    
    # Extract locations
    location_pattern = rb(entrance|exit|door|building|room|street|parking|lot)\b'
    locations = re.findall(location_pattern, query.lower())
    components['locations'] = locations
    
    # Always include person detection if we have other person-related components
    if any([components['gender], components['clothing'], components['actions']]):
        components[person'].append('person')
        
    return components

def simulate_detection(sub_query: str) -> Dict:
    """Simulate analyzing a single sub-query"""
    import random
    
    return {
        detected: random.choice([True, false  confidence: random.uniform(00,
        details: f"Analyzed for: {sub_query}",
      sub_query': sub_query
    }

def analyze_complex_query(query: str) -> Dict:
ion to demonstrate multi-prompt strategyint(f"🎯 Analyzing complex query:{query}')
    
    # Step 1: Parse the complex query
    components = parse_complex_query(query)
    print(f"📋 Parsed components: {components})
    
    # Step 2: Simulate analyzing each component
    results = [object Object]  query': query,
   components': components,
        sub_query_results': {},
        matching_frames':]
    }
    
    # Analyze each component
    for component_type, sub_queries in components.items():
        if not sub_queries:
            continue
            
        for sub_query in sub_queries:
            result = simulate_detection(sub_query)
            results[sub_query_results'][f"{component_type}_{sub_query}"] = result
    
    # Step 3 Combine results (all must match for complex query)
    all_match = True
    total_confidence = 00
    match_count = 0
    
    for result in results[sub_query_results'].values():
        if result['detected']:
            total_confidence += result['confidence']
            match_count += 1
        else:
            all_match =false
    
    if match_count > 0:
        avg_confidence = total_confidence / match_count
    else:
        avg_confidence = 0.0    
    results[overall_match] = all_match
    results['overall_confidence'] = avg_confidence
    
    return results

def main():
   o the multi-prompt strategy"""
    print("🚀 Multi-Prompt Analysis Demo)
    print(= * 50    # Test queries
    test_queries = [
        male wearing blue jacket with brown bag exiting entrance to enter red car,person wearing red shirt walking,female carrying black bag,person entering building"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Analyzing: '{query}'")
        print("-" * 40)
        
        result = analyze_complex_query(query)
        
        print(f"✅ Overall match: {result['overall_match']})
        print(f"📊 Confidence: {result['overall_confidence']:.2f}")
        
        print("\n📋 Sub-query results:)     for sub_query, sub_result in result[sub_query_results'].items():
            status =✅" if sub_result[detected'] else "❌"
            print(f"  {status} {sub_query}: {sub_result['confidence']:.2f}")
        
        print()

if __name__ == "__main__":
    main() 