# backend_v3/test_clip_loader.py
"""
Test script for CLIP model loader in backend_v3.
Loads the model, runs dummy text and image encoding, and asserts outputs.
"""
import torch
from PIL import Image
import numpy as np
from clip_loader import get_clip_model

def test_clip_loader():
    """
    Test loading CLIP model and running dummy encodings.
    """
    print("Loading CLIP model...")
    model, tokenizer, preprocess = get_clip_model()
    print("Model loaded.")

    # Dummy image (random noise)
    dummy_img = Image.fromarray(np.uint8(np.random.rand(224, 224, 3) * 255))
    image_input = preprocess(dummy_img).unsqueeze(0)

    # Dummy text
    texts = ["man in red shirt", "white van"]
    text_input = tokenizer(texts)

    with torch.no_grad():
        image_features = model.encode_image(image_input)
        text_features = model.encode_text(text_input)

    assert image_features is not None and image_features.shape[0] == 1, "Image features not computed."
    assert text_features is not None and text_features.shape[0] == len(texts), "Text features not computed."
    print("CLIP model test passed. Image and text features computed.")

if __name__ == "__main__":
    test_clip_loader() 