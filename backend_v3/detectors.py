# backend_v3/detectors.py

from typing import List, Dict, Any
import torch
import numpy as np
from PIL import Image
import cv2
from .clip_loader import get_clip_model

class PeopleDetector:
    def __init__(self, config):
        self.config = config
        # Load CLIP model for people detection
        self.model, self.tokenizer, self.preprocess = get_clip_model()
        self.device = next(self.model.parameters()).device

    def detect(self, video_path: str) -> List[Dict[str, Any]]:
        """Detect people, age, gender, and clothing in the video using CLIP."""
        results = []
        # TODO: Extract frames from video and run CLIP detection
        # For now, return placeholder
        return results

    def score_prompts(self, image, prompts):
        """Score image against text prompts using CLIP."""
        with torch.no_grad():
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            text_input = self.tokenizer(prompts).to(self.device)
            
            image_features = self.model.encode_image(image_input)
            text_features = self.model.encode_text(text_input)
            
            # Normalize features
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Compute similarity
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            return similarity

class ColorDetector:
    def __init__(self, config):
        self.config = config
        # Load CLIP model for color detection
        self.model, self.tokenizer, self.preprocess = get_clip_model()
        self.device = next(self.model.parameters()).device

    def detect(self, video_path: str) -> List[Dict[str, Any]]:
        """Detect key colors in clothing and objects using CLIP."""
        results = []
        # TODO: Extract frames and run color detection
        return results

    def detect_colors_in_frame(self, frame):
        """Detect colors in a single frame using CLIP."""
        color_prompts = [
            "red shirt", "blue jacket", "white car", "black bag",
            "green clothing", "yellow object", "brown item"
        ]
        
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        scores = self.score_prompts(pil_image, color_prompts)
        return scores

    def score_prompts(self, image, prompts):
        """Score image against color prompts using CLIP."""
        with torch.no_grad():
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            text_input = self.tokenizer(prompts).to(self.device)
            
            image_features = self.model.encode_image(image_input)
            text_features = self.model.encode_text(text_input)
            
            # Normalize and compute similarity
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            return similarity

class FireDetector:
    def __init__(self, config):
        self.config = config
        # Load CLIP model for fire detection
        self.model, self.tokenizer, self.preprocess = get_clip_model()
        self.device = next(self.model.parameters()).device

    def detect(self, video_path: str) -> List[Dict[str, Any]]:
        """Detect fire, flames, and smoke in the video using CLIP."""
        results = []
        # TODO: Extract frames and run fire detection
        return results

    def detect_fire_in_frame(self, frame):
        """Detect fire in a single frame using CLIP."""
        fire_prompts = [
            "fire", "flame", "burning", "smoke", "fire alarm"
        ]
        
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        scores = self.score_prompts(pil_image, fire_prompts)
        return scores

    def score_prompts(self, image, prompts):
        """Score image against fire prompts using CLIP."""
        with torch.no_grad():
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            text_input = self.tokenizer(prompts).to(self.device)
            
            image_features = self.model.encode_image(image_input)
            text_features = self.model.encode_text(text_input)
            
            # Normalize and compute similarity
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            return similarity

# Placeholders for future detectors
class WeaponsDetector:
    def __init__(self, config):
        self.config = config
    def detect(self, video_path: str) -> List[Dict[str, Any]]:
        return []

class VehiclesDetector:
    def __init__(self, config):
        self.config = config
    def detect(self, video_path: str) -> List[Dict[str, Any]]:
        return []

class UnusualActivityDetector:
    def __init__(self, config):
        self.config = config
    def detect(self, video_path: str) -> List[Dict[str, Any]]:
        return [] 