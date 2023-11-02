#!/usr/bin/env python3
#shebang line to inform the OS that the content is in python

#!/usr/bin/env python3

import cv2
import json

# Create a function for the trackbar callback to update the color limits
def update_limits(x):
    pass

def main():

    # setting up the video capture
    cap = cv2.VideoCapture(0)
    _, frame = cap.read()
    
    # dimensions for both windows
    scale_x = 1.2
    scale_y = 1.2
    window_width = int(frame.shape[1] * scale_x)
    window_height = int(frame.shape[0] * scale_y)
    
    #Create OpenCV windows to show the original image and segmentation mask
    window_name = 'Original Image'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, window_width, window_height)
    cv2.moveWindow(window_name, 100, 200)
    mask_window = 'Color Mask'
    cv2.namedWindow(mask_window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(mask_window, window_width, window_height)
    cv2.moveWindow(mask_window, 1000, 200)

    # Create trackbars for color limits
    cv2.createTrackbar('Bmin', 'Color Mask', 0, 255, update_limits)
    cv2.createTrackbar('Bmax', 'Color Mask', 255, 255, update_limits)
    cv2.createTrackbar('Gmin', 'Color Mask', 0, 255, update_limits)
    cv2.createTrackbar('Gmax', 'Color Mask', 255, 255, update_limits)
    cv2.createTrackbar('Rmin', 'Color Mask', 0, 255, update_limits)
    cv2.createTrackbar('Rmax', 'Color Mask', 255, 255, update_limits)


    while True:
        ret, frame = cap.read()
        if not ret:
          break

        # Converte a imagem para o espaço de cores HSV 
        #hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Get current trackbar values
        min_b = cv2.getTrackbarPos('Bmin', 'Color Mask')
        max_b = cv2.getTrackbarPos('Bmax', 'Color Mask')

        min_g = cv2.getTrackbarPos('Gmin', 'Color Mask')
        max_g = cv2.getTrackbarPos('Gmax', 'Color Mask')

        min_r = cv2.getTrackbarPos('Rmin', 'Color Mask')
        max_r = cv2.getTrackbarPos('Rmax', 'Color Mask')
    
    
        # Sets color limits based on trackbar values
        lower_bound = (min_b, min_g, min_r)
        upper_bound = (max_b, max_g, max_r)

         # Creates a mask for color detection
        mask = cv2.inRange(frame, lower_bound, upper_bound)
 
        # Updates OpenCV windows
        cv2.imshow('Original Image', cv2.flip(frame,1))
        cv2.imshow('Color Mask', cv2.flip(mask,1))

        key = cv2.waitKey(1)
        if key == ord('w'):
            # Save limits in a JSON file
            limits = {'limits': {'B': {'max': max_b,'min': min_b}, 'G': { 'max': max_g, 'min': min_g}, 'R': {'max': max_r,'min': min_r}}}
        

            with open('limits.json', 'w') as file:
             json.dump(limits,file)
            
            print('Saved.....') 

        elif key == ord('q'):
            print('Interrupted.....')
            break

if __name__ == '__main__':
    main()