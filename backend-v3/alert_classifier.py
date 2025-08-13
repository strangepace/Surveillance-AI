#!/usr/bin/env python3
"""
Alert classification system for backend-v3.
Categorizes detections into security, safety, crowd, traffic, and suspicious alerts.
"""
import re
from typing import Dict, List, Any, Optional

class AlertClassifier:
    """Classifies video detections into alert categories."""
    
    def __init__(self):
        """Initialize the alert classifier with category definitions."""
        self.categories = {
            "security": {
                "keywords": ["weapon", "gun", "knife", "dangerous", "suspicious", "threat", "attack", "fight", "violence"],
                "priority": "high",
                "description": "Security threats and dangerous objects"
            },
            "safety": {
                "keywords": ["fire", "smoke", "accident", "fall", "injury", "emergency", "hazard", "danger"],
                "priority": "high", 
                "description": "Safety hazards and emergencies"
            },
            "crowd": {
                "keywords": ["crowd", "group", "gathering", "mob", "protest", "rally", "assembly"],
                "priority": "medium",
                "description": "Crowd events and gatherings"
            },
            "traffic": {
                "keywords": ["car", "vehicle", "truck", "bus", "motorcycle", "traffic", "accident", "parking"],
                "priority": "medium",
                "description": "Traffic and vehicle related events"
            },
            "suspicious": {
                "keywords": ["loitering", "trespassing", "unauthorized", "suspicious", "strange", "unusual"],
                "priority": "medium",
                "description": "Suspicious behavior and activities"
            }
        }
    
    def classify_detection(self, detection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a single detection into alert categories.
        
        Args:
            detection (Dict[str, Any]): Detection result with labels and confidence
            
        Returns:
            Dict[str, Any]: Detection with added classification info
        """
        labels = detection.get("labels", [])
        confidence = detection.get("confidence", 0)
        
        # Convert labels to string for keyword matching
        label_text = " ".join(labels).lower()
        
        # Find matching categories
        matched_categories = []
        for category, config in self.categories.items():
            for keyword in config["keywords"]:
                if keyword.lower() in label_text:
                    matched_categories.append({
                        "category": category,
                        "priority": config["priority"],
                        "description": config["description"],
                        "matched_keyword": keyword
                    })
                    break  # Only match first keyword per category
        
        # Add classification to detection
        detection["alert_classification"] = {
            "categories": matched_categories,
            "primary_category": matched_categories[0]["category"] if matched_categories else "general",
            "priority": matched_categories[0]["priority"] if matched_categories else "low"
        }
        
        return detection
    
    def classify_batch(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify a batch of detections.
        
        Args:
            detections (List[Dict[str, Any]]): List of detection results
            
        Returns:
            List[Dict[str, Any]]: List of detections with classification info
        """
        classified_detections = []
        
        for detection in detections:
            classified = self.classify_detection(detection)
            classified_detections.append(classified)
        
        return classified_detections
    
    def get_alert_summary(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of alerts by category.
        
        Args:
            detections (List[Dict[str, Any]]): List of classified detections
            
        Returns:
            Dict[str, Any]: Summary of alerts by category and priority
        """
        summary = {
            "total_detections": len(detections),
            "categories": {},
            "priorities": {"high": 0, "medium": 0, "low": 0},
            "timeline": []
        }
        
        for detection in detections:
            classification = detection.get("alert_classification", {})
            categories = classification.get("categories", [])
            priority = classification.get("priority", "low")
            
            # Count by category
            for cat_info in categories:
                category = cat_info["category"]
                if category not in summary["categories"]:
                    summary["categories"][category] = 0
                summary["categories"][category] += 1
            
            # Count by priority
            summary["priorities"][priority] += 1
            
            # Add to timeline
            summary["timeline"].append({
                "timestamp": detection.get("timestamp", "unknown"),
                "categories": [cat["category"] for cat in categories],
                "priority": priority,
                "confidence": detection.get("confidence", 0)
            })
        
        return summary

def classify_detections(detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to classify a list of detections.
    
    Args:
        detections (List[Dict[str, Any]]): List of detection results
        
    Returns:
        List[Dict[str, Any]]: List of detections with alert classification
    """
    classifier = AlertClassifier()
    return classifier.classify_batch(detections)

def get_alert_summary(detections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience function to get alert summary.
    
    Args:
        detections (List[Dict[str, Any]]): List of detection results
        
    Returns:
        Dict[str, Any]: Alert summary
    """
    classifier = AlertClassifier()
    return classifier.get_alert_summary(detections)