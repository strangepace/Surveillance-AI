#!/usr/bin/env python3
"""
Enhanced Surveillance AI - Multi-Prompt Analysis
Handles complex queries by breaking them into sub-queries and combining results
"""

import os
import json
import re
from typing import List, Dict, Any, Tuple
from datetime import datetime
import cv2
import numpy as np
from google.cloud import videointelligence_v1
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

class ComplexQueryAnalyzer:
    def __init__(self):
        self.video_client = videointelligence_v1.VideoIntelligenceServiceClient()
        self.setup_gemini()
        
    def setup_gemini(self):
      Gemini for vision analysis"""
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY))
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
    def parse_complex_query(self, query: str) -> Dict[str, List[str]]:
      arse complex query into sub-components
        Example: male wearing blue jacket with brown bag exiting entrance to enter red car"
         components = {
        person:],
          clothing:       objects:       actions:],
          vehicles:       locations:       colors:      gender': []
        }
        
        # Extract colors
        color_pattern = r\b(red|blue|green|yellow|brown|black|white|orange|purple|pink)\b       colors = re.findall(color_pattern, query.lower())
        components[colors= colors
        
        # Extract gender
        if 'male' in query.lower():
            components[gender].append('male')
        eliffemale' in query.lower():
            components[gender'].append('female')
            
        # Extract clothing
        clothing_pattern = rb(jacket|shirt|pants|dress|hat|shoes|boots|coat)\b        clothing = re.findall(clothing_pattern, query.lower())
        components['clothing'] = clothing
        
        # Extract objects
        object_pattern = r'\b(bag|backpack|purse|phone|keys|wallet|umbrella|book)\b'
        objects = re.findall(object_pattern, query.lower())
        components['objects'] = objects
        
        # Extract vehicles
        vehicle_pattern = rb(car|truck|bus|motorcycle|bike|bicycle)\b        vehicles = re.findall(vehicle_pattern, query.lower())
        components['vehicles'] = vehicles
        
        # Extract actions
        action_pattern = r'\b(walking|running|entering|exiting|sitting|standing|carrying|holding)\b'
        actions = re.findall(action_pattern, query.lower())
        components['actions'] = actions
        
        # Extract locations
        location_pattern = rb(entrance|exit|door|building|room|street|parking|lot)\b'
        locations = re.findall(location_pattern, query.lower())
        components['locations'] = locations
        
        # Always include person detection
        if any([components['gender], components['clothing'], components['actions']]):
            components[person'].append('person')
            
        return components
    
    def detect_people_google(self, video_path: str) -> List[Dict]:
      etect people using Google Video Intelligence"
        print("🔍 Detecting people with Google Video Intelligence...")
        
        with open(video_path, "rb") as file:
            input_content = file.read()
        
        features =           videointelligence_v1Feature.PERSON_DETECTION,
            videointelligence_v1.Feature.LABEL_DETECTION,
        ]
        
        config = videointelligence_v1.PersonDetectionConfig(
            include_bounding_boxes=True,
            include_pose_landmarks=True,
        )
        
        context = videointelligence_v1.VideoContext(
            person_detection_config=config
        )
        
        operation = self.video_client.annotate_video(
            request={
         features": features,
              input_content: input_content,
              video_context": context,
            }
        )
        
        result = operation.result(timeout=600)
        
        people_detections = []
        for annotation in result.annotation_results:
            for track in annotation.person_detection_annotations:
                for detected_person in track.tracks:
                    for segment in detected_person.segments:
                        people_detections.append({
                       start_time': segment.start_time_offset.total_seconds(),
                     end_time': segment.end_time_offset.total_seconds(),
                       confidence': segment.confidence
                        })
        
        return people_detections
    
    def detect_objects_google(self, video_path: str) -> List[Dict]:
       tect objects using Google Video Intelligence"
        print("🔍 Detecting objects with Google Video Intelligence...")
        
        with open(video_path, "rb") as file:
            input_content = file.read()
        
        features = [videointelligence_v1.Feature.LABEL_DETECTION]
        
        operation = self.video_client.annotate_video(
            request={
         features": features,
              input_content: input_content,
            }
        )
        
        result = operation.result(timeout=600)
        
        object_detections = []
        for annotation in result.annotation_results:
            for label in annotation.segment_label_annotations:
                object_detections.append({
                label': label.entity.description,
               confidence: label.segments[0].confidence,
               start_time: label.segments[0].segment.start_time_offset.total_seconds(),
                   end_time: label.segments[0].segment.end_time_offset.total_seconds()
                })
        
        return object_detections
    
    def extract_frame_at_time(self, video_path: str, timestamp: float) -> np.ndarray:
        Extract a frame at specific timestamp""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(timestamp * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None
    
    def analyze_frame_with_vision(self, frame: np.ndarray, sub_query: str) -> Dict:
  yze a single frame using Gemini Vision"""
        try:
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(frame)
            
            # Create prompt for the sub-query
            prompt = f"""
            Analyze this image for: {sub_query}
            
            Return a JSON response with:
            {{
                detected": true/false,
                confidence": 0.0-1.0
          details: escription of what was found,
                location": "where in the image"
            }}
            
            Be specific and accurate. Only return the JSON, no other text.
                 
            response = self.gemini_model.generate_content([prompt, pil_image])
            
            # Parse JSON response
            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                return [object Object]detected": False, confidence: 0, "details":JSON parse error"}
                
        except Exception as e:
            return [object Object]detected": False, confidence: 0, details: f"Error: {str(e)}"}
    
    def detect_color_in_frame(self, frame: np.ndarray, target_color: str) -> Dict:
        ect specific color in frame using image processing"    # Color ranges for different colors (HSV)
        color_ranges = [object Object]           red: (0, 100, 1010,255255
            blue: ([100,100,100130,255255            green': ([40, 100, 1080,255255         yellow': ([20, 100, 1030,255255]),
            brown: (101002020,255200            black': ([0, 00180,25530           white': ([0, 020, [180,30, 255])
        }
        
        if target_color not in color_ranges:
            return [object Object]detected": False,confidence": 0.0}
        
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        
        # Create mask for target color
        lower, upper = color_ranges[target_color]
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        
        # Calculate percentage of pixels with target color
        total_pixels = mask.shape[0] * mask.shape[1      color_pixels = cv2.countNonZero(mask)
        color_percentage = color_pixels / total_pixels
        
        # Threshold for detection (adjust as needed)
        threshold = 00.055of frame should be target color
        
        return [object Object]        detected": color_percentage > threshold,
           confidence": min(color_percentage / threshold,10      details": f{color_percentage:0.2f frame is {target_color}",
           color_percentage": color_percentage
        }
    
    def analyze_complex_query(self, video_path: str, query: str) -> Dict[str, Any]:
      unction to analyze complex queries using multi-prompt strategy"        print(f"🎯 Analyzing complex query: '{query}'")
        
        # Parse the complex query
        components = self.parse_complex_query(query)
        print(f"📋 Parsed components: {components}")
        
        # Initialize results
        results = {
          queryquery,
       components': components,
            matching_frames:        analysis_summary': {}
        }
        
        # Step 1: Get basic detections from Google Video Intelligence
        people_detections = self.detect_people_google(video_path)
        object_detections = self.detect_objects_google(video_path)
        
        print(f"👥 Found {len(people_detections)} person detections)
        print(f"📦 Found {len(object_detections)} object detections")
        
        # Step2xtract frames with people for detailed analysis
        candidate_timestamps = set()
        for detection in people_detections:
            # Sample multiple frames from each person detection
            start_time = detection['start_time]          end_time = detection['end_time']
            
            # Sample frames at regular intervals
            for t in np.arange(start_time, end_time, 0.5 Every 0.5 seconds
                candidate_timestamps.add(t)
        
        print(f"🖼️  Analyzing {len(candidate_timestamps)} candidate frames")
        
        # Step 3: Analyze each candidate frame
        for timestamp in candidate_timestamps:
            frame = self.extract_frame_at_time(video_path, timestamp)
            if frame is None:
                continue
            
            frame_results =[object Object]
          timestamp': timestamp,
             matches},
       overall_confidence': 0
            }
            
            # Analyze each component
            for component_type, sub_queries in components.items():
                if not sub_queries:
                    continue
                    
                for sub_query in sub_queries:
                    if component_type == 'colors':
                        # Use color detection
                        result = self.detect_color_in_frame(frame, sub_query)
                    else:
                        # Use vision model
                        result = self.analyze_frame_with_vision(frame, sub_query)
                    
                    frame_results['matches'][f"{component_type}_{sub_query}"] = result
            
            # Calculate overall confidence (all components must match)
            all_match = True
            total_confidence = 0.0
            match_count = 0
            
            for match_result in frame_results['matches'].values():
                if match_result['detected']:
                    total_confidence += match_result['confidence']
                    match_count +=1              else:
                    all_match = False
            
            if match_count > 0             frame_results['overall_confidence'] = total_confidence / match_count
            
            # Only include frames that match all criteria
            if all_match and frame_results['overall_confidence'] > 0.5           results['matching_frames'].append(frame_results)
        
        # Step 4: Generate summary
        results['analysis_summary] = {
        total_frames_analyzed: len(candidate_timestamps),
            matching_frames_found': len(results[matching_frames]),   components_searched': components,
        confidence_threshold': 0.5
        }
        
        return results

def main():
   execution function for Colab"""
    print("🚀 Enhanced Surveillance AI - Multi-Prompt Analysis)
    print(= * 60)
    
    # Mount Google Drive
    from google.colab import drive
    drive.mount(/content/drive')
    
    # Setup paths
    uploads_path = /content/drive/MyDrive/surveillance-ai/uploads    results_path = /content/drive/MyDrive/surveillance-ai/results"
    
    # Create directories if they don't exist
    os.makedirs(uploads_path, exist_ok=True)
    os.makedirs(results_path, exist_ok=True)
    
    # Load credentials
    credentials_path = /content/drive/MyDrive/surveillance-ai/credentials.json"
    if os.path.exists(credentials_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        print("✅ Credentials loaded")
    else:
        print(❌ Credentials not found at:", credentials_path)
        return
    
    # Load environment variables
    env_path = /content/drive/MyDrive/surveillance-ai/.env"
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print("✅ Environment variables loaded")
    else:
        print("❌ .env file not found at:", env_path)
        return
    
    # List available videos
    video_files = [f for f in os.listdir(uploads_path) if f.endswith((.mp4', .avi,.mov'))]
    
    if not video_files:
        print("❌ No video files found in uploads folder")
        return
    
    print(f"📹 Available videos: {video_files}")
    
    # Select video (for now, use the first one)
    selected_video = video_files[0]
    video_path = os.path.join(uploads_path, selected_video)
    print(f🎬 Selected video: {selected_video}")
    
    # Initialize analyzer
    analyzer = ComplexQueryAnalyzer()
    
    # Example complex queries to test
    test_queries = [
        male wearing blue jacket with brown bag exiting entrance to enter red car,person wearing red shirt walking,female carrying black bag,person entering building
    ]    
    # Analyze each query
    all_results = {}
    
    for query in test_queries:
        print(f"\n🔍 Analyzing query: '{query}'")
        print("-" * 50)
        
        try:
            result = analyzer.analyze_complex_query(video_path, query)
            all_results[query] = result
            
            print(f"✅ Found {len(result[matching_frames'])} matching frames")
            
            # Save individual results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_filename = f"{selected_video}_{query.replace(' ', _}_{timestamp}.json"
            result_path_full = os.path.join(results_path, result_filename)
            
            with open(result_path_full, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"💾 Results saved to: {result_path_full}")
            
        except Exception as e:
            print(f❌ Error analyzing query{query}': {str(e)})   # Save combined results
    combined_filename = f{selected_video}_complex_analysis_{datetime.now().strftime(%Y%m%d_%H%M%S')}.json"
    combined_path = os.path.join(results_path, combined_filename)
    
    with open(combined_path, was f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n🎉 Analysis complete! Combined results saved to: {combined_path}")
    print(📊Summary:")
    for query, result in all_results.items():
        print(f"  - '{query}': {len(result[matching_frames])} matches)if __name__ == "__main__":
    main() 