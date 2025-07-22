# backend_v3/config_loader.py
"""
Utility to load YAML config files for backend_v3.
"""
import yaml
import os

def load_clip_config(config_path=None):
    """
    Load CLIP model config from YAML file.
    Args:
        config_path (str): Path to the YAML config file.
    Returns:
        dict: CLIP model config dictionary.
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the YAML is invalid.
    """
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'clip_config.yaml')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"CLIP config file not found: {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config.get('clip_model', {}) 