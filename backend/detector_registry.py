"""
Detector Registry - Centralized detector management system.

Provides a registry pattern for detectors, making it easy to:
- Add/remove detectors via configuration
- Instantiate detectors dynamically
- Control which detectors are enabled
"""

import logging
from typing import Dict, Type, Any, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger("detector_registry")


class BaseDetector(ABC):
    """Base class for all detectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize detector with configuration.
        
        Args:
            config (Dict[str, Any]): Detector-specific configuration
        """
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def detect(self, video_path: str) -> List[Dict[str, Any]]:
        """
        Detect objects/events in video.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            List[Dict[str, Any]]: List of detection results
        """
        pass
    
    def is_enabled(self) -> bool:
        """
        Check if detector is enabled in config.
        
        Returns:
            bool: True if enabled, False otherwise
        """
        # Support both new (detection.detectors) and legacy (detectors) config structure
        if "detection" in self.config and "detectors" in self.config["detection"]:
            detector_config = self.config["detection"]["detectors"]
        else:
            detector_config = self.config.get("detectors", {})
        
        detector_name = self.name.lower().replace("detector", "")
        return detector_config.get(detector_name, {}).get("enabled", True)


# Import existing detector classes
from detectors import (
    PeopleDetector,
    ColorDetector,
    FireDetector,
    WeaponsDetector,
    VehiclesDetector,
    UnusualActivityDetector
)


# Detector Registry
DETECTOR_REGISTRY: Dict[str, Type[BaseDetector]] = {
    "people": PeopleDetector,
    "color": ColorDetector,
    "fire": FireDetector,
    "weapons": WeaponsDetector,
    "vehicles": VehiclesDetector,
    "unusual_activity": UnusualActivityDetector,
}


class DetectorRegistry:
    """Manages detector registration and instantiation."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize detector registry with configuration.
        
        Args:
            config (Dict[str, Any]): Application configuration
        """
        self.config = config
        self.registry = DETECTOR_REGISTRY.copy()
        logger.info(f"Detector registry initialized with {len(self.registry)} detectors")
    
    def register(self, name: str, detector_class: Type[BaseDetector]):
        """
        Register a new detector.
        
        Args:
            name (str): Detector name (key)
            detector_class (Type[BaseDetector]): Detector class
        """
        self.registry[name] = detector_class
        logger.info(f"Registered detector: {name} -> {detector_class.__name__}")
    
    def get_enabled_detectors(self) -> List[str]:
        """
        Get list of enabled detector names from config.
        
        Returns:
            List[str]: List of enabled detector names
        """
        # Support both new (detection.detectors) and legacy (detectors) config structure
        if "detection" in self.config and "detectors" in self.config["detection"]:
            detector_config = self.config["detection"]["detectors"]
        else:
            detector_config = self.config.get("detectors", {})
        
        enabled = []
        
        for name in self.registry.keys():
            detector_name_config = detector_config.get(name, {})
            if detector_name_config.get("enabled", True):
                enabled.append(name)
        
        logger.info(f"Enabled detectors: {enabled}")
        return enabled
    
    def create_detector(self, name: str) -> Optional[BaseDetector]:
        """
        Create an instance of a detector by name.
        
        Args:
            name (str): Detector name
            
        Returns:
            Optional[BaseDetector]: Detector instance or None if not found
        """
        if name not in self.registry:
            logger.warning(f"Detector '{name}' not found in registry")
            return None
        
        detector_class = self.registry[name]
        # Support both new (detection.detectors) and legacy (detectors) config structure
        if "detection" in self.config and "detectors" in self.config["detection"]:
            detector_config = self.config["detection"]["detectors"].get(name, {})
        else:
            detector_config = self.config.get("detectors", {}).get(name, {})
        
        try:
            detector = detector_class(self.config)
            logger.info(f"Created detector instance: {name}")
            return detector
        except Exception as e:
            logger.error(f"Failed to create detector '{name}': {e}", exc_info=True)
            return None
    
    def create_all_enabled(self) -> Dict[str, BaseDetector]:
        """
        Create instances of all enabled detectors.
        
        Returns:
            Dict[str, BaseDetector]: Dictionary of detector name -> instance
        """
        enabled_names = self.get_enabled_detectors()
        detectors = {}
        
        for name in enabled_names:
            detector = self.create_detector(name)
            if detector:
                detectors[name] = detector
        
        logger.info(f"Created {len(detectors)} enabled detector instances")
        return detectors


def get_detector_registry(config: Dict[str, Any]) -> DetectorRegistry:
    """
    Factory function to create a detector registry.
    
    Args:
        config (Dict[str, Any]): Application configuration
        
    Returns:
        DetectorRegistry: Initialized registry instance
    """
    return DetectorRegistry(config)

