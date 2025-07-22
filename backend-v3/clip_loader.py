# backend_v3/clip_loader.py
"""
CLIP model loader for backend_v3. Loads model, tokenizer, and preprocess transform
based on config (supports open_clip backend, ViT-B-32 by default).
"""
import os
import torch
import open_clip
from .config_loader import load_clip_config


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
    Raises:
        RuntimeError: If model fails to load.
    """
    config = load_clip_config(config_path)
    model_name = config.get('name', 'ViT-B-32')
    backend = config.get('backend', 'open_clip')
    device = device or ('cuda' if torch.cuda.is_available() else 'cpu')

    try:
        if backend == 'open_clip':
            model, _, preprocess = open_clip.create_model_and_transforms(model_name, pretrained='laion2b_s34b_b79k')
            tokenizer = open_clip.get_tokenizer(model_name)
        else:
            raise NotImplementedError(f"Backend '{backend}' is not supported yet. Use 'open_clip'.")
        model = model.to(device)
        model.eval()
        return model, tokenizer, preprocess
    except Exception as e:
        raise RuntimeError(f"Failed to load CLIP model ({model_name}, backend={backend}): {e}") 