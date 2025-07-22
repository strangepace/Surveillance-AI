import cv2
import numpy as np
import os

def create_test_video():
    """Create a simple test video with a moving object"""
    # Video settings
    width = 640
    height = 480
    fps = 30
    duration = 5  # seconds
    
    # Create output directory if it doesn't exist
    os.makedirs("content", exist_ok=True)
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('content/sample_video.mp4', fourcc, fps, (width, height))
    
    # Create frames
    for i in range(fps * duration):
        # Create a black frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add a moving rectangle (simulating a person)
        x = int(width * (i / (fps * duration)))
        y = height // 2
        cv2.rectangle(frame, (x-20, y-40), (x+20, y+40), (0, 0, 255), -1)
        
        # Add some text
        cv2.putText(frame, "Test Video", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Write the frame
        out.write(frame)
    
    # Release everything
    out.release()
    print("Test video created at: content/sample_video.mp4")

if __name__ == "__main__":
    create_test_video() 