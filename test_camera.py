import cv2

# Open the webcam (0 is the default camera)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam. Please check your camera.")
    exit()

print("Webcam is working! Press 'q' to quit.")

while True:
    # Read a frame from the camera
    ret, frame = cap.read()
    
    # Show the frame in a window
    cv2.imshow('Camera Test', frame)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()