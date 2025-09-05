# backend_v3/clip_loader.py
"""
CLIP model loader for backend_v3. Loads model, tokenizer, and preprocess transform
based on config (supports open_clip backend, ViT-B-32 by default).
"""
import os
import torch
import open_clip
from config_loader import load_clip_config


def get_clip_model(config_path=None, device=None):
    """
    Load CLIP model, tokenizer, and preprocess transform based on config.
    Args:
        config_path (str): Path to YAML config file.
        device (str): 'cuda' or 'cpu'. If None, auto-detect.
    Returns:
        model: CLIP model
        tokenizer: CLIP tokenizer
        preprocess: CLIP image transform
        device: The device being used
    Raises:
        RuntimeError: If model fails to load.
    """
    config = load_clip_config(config_path)
    model_name = config.get('name', 'ViT-B-32')
    backend = config.get('backend', 'open_clip')
    
    # Device management with config override
    device_config = config.get('device', {})
    auto_detect = device_config.get('auto_detect', True)
    force_cpu = device_config.get('force_cpu', False)
    log_device = device_config.get('log_device', True)
    
    # Determine device
    if device is not None:
        # Explicit device override
        selected_device = device
    elif force_cpu:
        # Force CPU even if GPU available
        selected_device = 'cpu'
    elif auto_detect and torch.cuda.is_available():
        # Auto-detect GPU
        selected_device = 'cuda'
    else:
        # Fallback to CPU
        selected_device = 'cpu'
    
    # Log device selection
    if log_device:
        if selected_device == 'cuda':
            gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Unknown'
            print(f"🚀 Using device: {selected_device} ({gpu_name})")
        else:
            print(f"🖥️  Using device: {selected_device}")
    
    try:
        if backend == 'open_clip':
            # OpenCLIP 2.32.0 returns 3 values: model, preprocess, preprocess_val
            model, preprocess, _ = open_clip.create_model_and_transforms(model_name, pretrained='laion2b_s34b_b79k')
            tokenizer = open_clip.get_tokenizer(model_name)
        else:
            raise NotImplementedError(f"Backend '{backend}' is not supported yet. Use 'open_clip'.")
        model = model.to(selected_device)
        model.eval()
        return model, tokenizer, preprocess, selected_device
    except Exception as e:
        raise RuntimeError(f"Failed to load CLIP model ({model_name}, backend={backend}): {e}") 