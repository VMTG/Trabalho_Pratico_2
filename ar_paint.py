#!/usr/bin/env python3
#shebang line to inform the OS that the content is in python

#!/usr/bin/env python3

#------------------------------------------------------------------------
#                            Import functions
#------------------------------------------------------------------------
import time
import json
import argparse
import sys
import cv2
import numpy as np
from math import sqrt
from datetime import datetime
from random import randint,shuffle


#------------------------------------------------------------------------
#                           Global Variables
#------------------------------------------------------------------------
# Color of the pencil, starting as Black
draw_color = (0,0,0)
# Thickness of the pencil, starting as 5
pencil_thickness = 5
# Threshold for the shake prevension mode, starting as 50
shake_threshold = 50
# 
centroid_area = 0 


#------------------------------------------------------------------------
#                               Classes
#------------------------------------------------------------------------
class Mouse:  
    """
    Class "Mouse": This class is used in the case the user desires to use 
        the mouse as the pencil. It updates the pencil coordenates
    """
    def __init__(self):
        self.coords = (None,None)
        self.pressed = False

    def update_mouse(self,event,x,y,flags,param):
        self.coords = (x,y)

        if event == cv2.EVENT_LBUTTONDOWN:
            self.pressed = True
        elif event == cv2.EVENT_LBUTTONUP:
            self.pressed = False

class Figure:
    """
    Class "Figure": This class is used to help regist the different types 
        of geometric figures

    """
    def __init__(self,type,origin,final,colour,thickness):
        self.type = type
        self.coord_origin = origin
        self.coord_final = final
        self.color = colour
        self.thickness = thickness

#------------------------------------------------------------------------
#                              Functions
#------------------------------------------------------------------------

def init_arguments():
    """
    Function "init_arguments": Function that processes the input arguments 
        necessary to determine what type of mode is going to be used

    Returns:
        path:   Path of the Json file created by color_segmenter that 
            contains the limits of the desired section
        usp:    Boolean to know if Shake Prevension mode is being used
        ucc:    Boolean to know if the live feed from the Camera is being 
            used as canvas
        um:     Boolean to know if the mouse is being used as pencil
        ugc:    Boolean to know if canvas is divided is zones to be painted

    """
    # Input Arguments
    parser = argparse.ArgumentParser(description='Ar Paint ')
    parser.add_argument('-j','--json',type = str, required= False , help='Full path to json file', default='limits.json')
    parser.add_argument('-usp','--use_shake_prevention', action='store_true', help='Use shake prevention mode, change shake prevention threshold using , and .')
    parser.add_argument('-ucc','--use_cam_canvas', action='store_true', help='Use camera as canvas')
    parser.add_argument('-um','--use_mouse', action='store_true', help='Use mouse as the pencil')
    parser.add_argument('-ugc','--use_grid_canvas', action='store_true', help='Use grid as canvas')
    args = vars(parser.parse_args())
   

    path = 'limits.json' if not args['json'] else args['json']  # Path for the json file
    usp = args['use_shake_prevention']  # Shake prevention mode
    ucc = args['use_cam_canvas']        # Use live feed from the cam to be used as the canvas
    um = args['use_mouse']              # Use mouse as the pencil
    ugc = args['use_grid_canvas']       # Use a zone grid as the canvas 
    return path, usp, ucc, um, ugc

def readFile(path):
    """
    Function "readFile": Function that read the file Json to regists the 
    limits created by color_segmenter

    Args:
        path (string): Full Path of the Json file that contains the limits 

    Returns:
        limits: Array containing the RGB limits
    """
    try:
        with open(path, 'r') as openfile:
            json_object = json.load(openfile)
            limits = json_object['limits']
    # if the file doesn't exist, send out an error message and quit
    except FileNotFoundError:
        sys.exit('The .json file with the color data doesn\'t exist.')

    return limits

def get_Centroid(mask) :
    """
    Function "get_Centroid": Used find all the objects in the frame after
        the mask with the limits was applied, afterwards it finds the 
        biggest object, to calculate the coordinates of the centroid 

    Args:
        mask (Image): image of the frame after it was appplied the mask

    Returns:
        (cX,cY): Coordenates of the Centroid
        image_result: Result of the frame after the selection of the 
            biggest object (painted by green and red cruz in the centroid)
    """
    # find all contours (objects)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # if objects are detected, let's find the biggest one, make it green and calculate the centroid
    if cnts:

        # find the biggest object
        cnt = max(cnts, key=cv2.contourArea)

        # make it green (but still show other objects in white)
        biggest_obj = np.zeros(mask.shape, np.uint8)
        cv2.drawContours(biggest_obj, [cnt], -1, 255, cv2.FILLED)
        biggest_obj = cv2.bitwise_and(mask, biggest_obj) # mask-like image with only the biggest object
        all_other_objs = cv2.bitwise_xor(mask, biggest_obj) # all other objects except the biggest one
        
        b = all_other_objs
        g = mask
        r = all_other_objs

        image_result = cv2.merge((b, g, r))

        # calculate centroid coordinates
        M = cv2.moments(cnt)
        cX = int(M["m10"] / M["m00"]) if (M["m00"]!=0) else None
        cY = int(M["m01"] / M["m00"]) if (M["m00"]!=0) else None

        # draw small red cross to indicate the centroid point
        if cX: 
            cv2.line(image_result, (cX-8, cY-8), (cX+8, cY+8), (0, 0, 255), 5)
            cv2.line(image_result, (cX+8, cY-8), (cX-8, cY+8), (0, 0, 255), 5)

    # if it didn't detect any objects, just show the mask as it is
    else:
        image_result = cv2.merge((mask, mask, mask))
        cX = None
        cY = None
        
    return (cX,cY), image_result

def key_Press(key_input,canvas,draw_moves):
    """
    Function "key_Press": Function that changes color, thickness, 
        shake threshold and saves the canvas as .png and .jpg files.
        Also quits the program in case 'q' is pressed

    Args:
        key_input (string): Input by the user from the keyboard
        canvas (Image): Image that is being painted
        draw_moves (Figure): Arrays of Figure that inclues all 
            the moves to be drawned after every frame

    Returns:
        True/False: If it's to end or not to end the program
    """
    global draw_color, pencil_thickness, shake_threshold
    height,width,_ = np.shape(canvas)
    max_threshold = max(height,width)
        # quit program
    if key_input=='q':
        print('Leaving the program...')
        return False
        # change color to Red
    elif key_input=='r':
        print("Changed Color to Red")
        draw_color = (0,0,255)
        # change color to Green
    elif key_input=='g':
        print("Changed Color to Green")
        draw_color = (0,255,0)
        # change color to Blue
    elif key_input=='b':
        print("Changed Color to Blue")
        draw_color = (255,0,0)
        # decrease pencil size
    elif key_input=='-':
        if pencil_thickness > 0:
            pencil_thickness -= 5
            print("Decrease pencil size")
        # increase pencil size
    elif key_input=='+':
        if pencil_thickness < 50:
            pencil_thickness += 5
            print("Increase pencil size")
        # save canvas 
    elif key_input=='w' and draw_moves != []:
        print("Save obtained drawing")
        # Regists the current time
        date = datetime.now()
        formatted_date = date.strftime("%a_%b_%d_%H:%M:%S")
        # Creates the 2 files (.png and .jpg)
        name_canvas = 'drawing_' + formatted_date + '.png'
        name_canvas_colored = 'drawing_' + formatted_date + '_colored.jpg'
        canvas = redraw_Painting(canvas,draw_moves)
        # Saves both as "drawing_DATE"
        cv2.imwrite(name_canvas, canvas)            #.png
        cv2.imwrite(name_canvas_colored, canvas)    #.jpg
        # increase shake threshold
    elif key_input==',':
        if shake_threshold > 0:
            shake_threshold -= 50 
            print("Decrease shake threshold")
            print("Shake prevension Threshold: ",shake_threshold/max_threshold*100,"%")
        # decrease shake threshold
    elif key_input=='.':
        if shake_threshold < (max_threshold-50):
            shake_threshold += 50
            print("Increase shake threshold")
            print("Shake prevension Threshold: ",shake_threshold/max_threshold*100,"%")
    return True

def redraw_Painting(frame, figures):
    """
    Function "redraw_Painting"

    Args:
        frame (Image): Image frame to be drawn all the figures
        figures (Figure): Arrays of Figure that contain the information 
            to draw 

    Returns:
        frame: image after it was redrawn all the figures
    """
    for step in figures:
        if step.type == "square":
            # Draw the Square given the coordinates from one the corner to the diagonal one
            cv2.rectangle(frame,step.coord_origin,step.coord_final,step.color,step.thickness)
        
        elif step.type == "circle":
            # Calculation of the Radious given the difference coordinates  
            difx = step.coord_final[0] - step.coord_origin[0]
            dify = step.coord_final[1] - step.coord_origin[1]
            radious = round(sqrt(difx**2 + dify**2))
            # Draw the Circle given the coordinates of the center and radious  
            cv2.circle(frame,step.coord_origin,radious,step.color,step.thickness) 

        elif step.type == "ellipse":
            # Calculation of the center and axes given the difference coordinates  
            meanx = (step.coord_final[0] - step.coord_origin[0])/2
            meany = (step.coord_final[1] - step.coord_origin[1])/2
            center = (round(meanx + step.coord_origin[0]), round(meany + step.coord_origin[1]))
            axes = (round(abs(meanx)), round(abs(meany)))
            # Draw the Ellipse given the 2 coordinates of the outside oof the ellipse
            cv2.ellipse(frame,center,axes,0,0,360,step.color,step.thickness)
        
        elif step.type == "line":
            # Draw the Line based on previous and current position of the pencil
            cv2.line(frame, step.coord_origin,step.coord_final, step.color,step.thickness)
        
        elif step.type == "dot":    
            # Draw the Dot based on the current position of the pencil    
            cv2.circle(frame, step.coord_final, 1, step.color,step.thickness) 
    return frame

def form_Grid(frame):
    """
    Function "form_Grid": Obtains the coordinates and colors 
        of each division. Used for the Zone painting mode input by user 

    Args:
        frame (Image): Image that is going to be divided into sections

    Returns:
        contours: coordinates of each section
    """
    height,width,_ = frame.shape
    grid = np.zeros([height,width],dtype=np.uint8)

    # coloring zones are a grid
    grid[height-1,:] = 255
    grid[:,width-1] = 255

    for y in range(0,height,int(height/3)):
        grid[y,:] = 255
    for x in range(0,width,int(width/4)):
        grid[:,x] = 255

    grid = cv2.bitwise_not(grid)

    # contours of each zone
    contours, _ = cv2.findContours(grid, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # color for each number
    numbers_to_colors = [(0,0,255), (0,255,0), (255,0,0)]
    #randomize the order of the color corresponding to each number
    shuffle(numbers_to_colors)

    return contours, numbers_to_colors
            
def colors_Legend(num_colors, accuracy = None):
    """
    Function "colors_Legend": creates the window to display the Legend 
    for colors to paint in each zone

    Args:
        num_colors (string): Array contain the colors for each section
        accuracy (int, optional): Percentage value of correct 
            painted zones. Defaults to None.

    Returns:
        legend: Image containg the legend for each color 
    """
    # Empty window
    legend = np.zeros([300,350,3],dtype=np.uint8)
    # Creates the legend for each color
    for i in range(3):
        colour = 'Red  (r)' if num_colors[i]==(0,0,255) else ('Green  (g)' if num_colors[i]==(0,255,0) else 'Blue  (b)')
        cv2.putText(legend, str(i+1) + ' - ' + colour, (50, 50+50*i), cv2.FONT_HERSHEY_SIMPLEX, 0.9, num_colors[i], 2)
    # Creates the text for the accuracy 
    if accuracy!=None:
        if accuracy == "NaN":
            cv2.putText(legend, 'Accuracy: ' + str(accuracy) , (50, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)
        else:
            cv2.putText(legend, 'Accuracy: ' + str(accuracy) + '%', (50, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)
    
    return legend

def draw_Grid(frame, contours, numbers):
    """
    Function "draw_Grid": Draws the grid for each zone in the empty white image

    Args:
        frame (Image): Image to be drawn on the grid
        contours (int): Coordinates of all the sections
        numbers (_type_): Array of the number for each Zone

    """
    # grid and numbers will be white
    color = (0,0,0)
    # draws the numbers in each zone
    for i in range(len(contours)):
        c = contours[i]

        x,y,width,height = cv2.boundingRect(c)
        cx = int(x + width/2)
        cy = int(y + height/2)

        # write the numbers in zone
        cv2.putText(frame, str(numbers[i]), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    # draw the contours and return the result
    return cv2.drawContours(frame, contours, -1, color, 3)

def calc_accuracy(frame, contours, zone_numbers, num_colors):
    """
    Function "calc_accuracy": Calculates the percentage of correct 
        pixeis drawn in each zones

    Args:
        frame (Image): Image that is going to be calculated 
            the accuracy
        contours (int): Coordinates of each zone
        zone_numbers (int): Numbers of each zone
        num_colors (int): Color for each zone

    Returns:
        accuracy: returns the result of the percentage calculated
    """

    height,width,_ = frame.shape
    # Max value of pixels in the window
    total_pixels = height*width
    # Value of correct pixels drawn in the entire window
    right_pixels = 0 
    # Regists the correct pixels painted for each zone
    for i in range(len(contours)):

        c = contours[i]                             # the zone
        zone_number = zone_numbers[i]               # the zone number
        color = num_colors[zone_number-1]           # the zone color

        # corners of this zone (zones are always rectangles)
        minX = c[0][0][0]
        maxX = c[2][0][0]
        minY = c[0][0][1]
        maxY = c[1][0][1]

        _,_,depth = frame.shape

        # evaluate each pixel
        for pixel_row in frame[minY:maxY, minX:maxX, 0:depth]:
            for pixel in pixel_row:
                pixel = (pixel[0], pixel[1], pixel[2])
                right_pixels += 1 if pixel==color else 0

    # Calculate the accuracy give correct and max pixels
    return int((right_pixels/total_pixels)*100)

#------------------------------------------------------------------------
#                                Main
#------------------------------------------------------------------------

def main():
    """
        Function "main": Cointais all the actions realizes given 
                the input and objective of the work.
            Starts by reading the arguments and reads the file Json.
            Setup the camera, and all the windows necessary 
                for each mode.
            Continious Operations inclued reading the keyboard input
                to determine what is drawn and what colors are used.
                Including to quit, save and clean the canvas

    """
    global draw_color, pencil_thickness
    # Imput arguments to determine what modes are used
    path, usp, use_cam, use_mouse, use_grid = init_arguments()
    # Read the Json File to determine the color limits of the object
    ranges = readFile(path) 

    # Setting up the video capture
    capture = cv2.VideoCapture(0)
    _, frame = capture.read()

    # Setting up blank Canvas for painting
    height,width,_ = np.shape(frame)
    paint_window = np.zeros((height,width,4))
    paint_window.fill(255)
    cv2.imshow("Paint Window",paint_window)
    cv2.moveWindow("Paint Window", 640, 735)

    # RGB Ranges for the object
    range_lows = (ranges['B']['min'], ranges['G']['min'], ranges['R']['min'])
    range_highs = (ranges['B']['max'], ranges['G']['max'], ranges['R']['max'])
    
    # Array contaning all the drawing intances 
    draw_moves = []
    # Flag to determine if the user is drawing or not to paint
    flag_draw = False
    # Flag to know if the user started painting
    started_draw = False
    
    # For the mode to paint in the divided Zones  
    if use_grid:
        print('Using a numbered grid as a canvas') 
        # Creates the Zones with the respective numbers corresponding colors
        zones, numbers_to_colors = form_Grid(paint_window)
        num_zones = len(zones)
        color_numbers = []
        for _ in range(num_zones):
            color_numbers.append(randint(1,3))
        # Color for each Zone Legend window
        stats = colors_Legend(numbers_to_colors)
        color_window = 'Color map'
        # Window for the Legend
        cv2.namedWindow(color_window, cv2.WINDOW_NORMAL)
        cv2.moveWindow(color_window, 100, 600)
        cv2.imshow(color_window, stats)
        
    # For the mode to use normal blank canvas
    if not use_cam and not use_grid:
        print('Using a white canvas as a canvas') 
    
    # For the mode to use shake prevention mode
    if usp:
        print('Using shake prevention mode') 

    # For the mode to use the cam as canvas
    if use_cam:
        print('Using camera frames as a canvas') 

    # For the mode to use the mouse as pencil
    if use_mouse:
        print('Using the mouse to paint')
        mouse = Mouse()
        cv2.setMouseCallback("Paint Window", mouse.update_mouse)
    elif not use_mouse:
        print('Using an displayed object to paint') 
    #---------------------------------------------------------------------
    #                       Continuous Operations
    #---------------------------------------------------------------------
    while True:
        # Setup camera 
        _,frame = capture.read()
        # Flips frame
        flipped_frame = cv2.flip(frame, 1)
        # Cleans the painting window
        paint_window.fill(255)

        # For the Use camera as canvas mode
        if use_cam: 
            operating_frame = flipped_frame
        # For the Zone divided canvas mode
        elif use_grid:
            grid_window = draw_Grid(paint_window, zones, color_numbers)
            operating_frame = grid_window
        else:
        # For the clean Canvas mode
            operating_frame = paint_window

        # Mask for the object using the live camera
        frame_mask = cv2.inRange(flipped_frame, range_lows, range_highs)
        # Frame of camera with Mask applied
        frame_wMask = cv2.bitwise_and(flipped_frame,flipped_frame, mask = frame_mask)
        
        # For the object centroid as pencil
        if not use_mouse:    
            (cx,cy),frame_test = get_Centroid(frame_mask)
            cv2.imshow("Centroid window", frame_test)
            cv2.moveWindow("Centroid window", 1360, 10)
            cv2.imshow("Original window",frame_wMask)
        # For the mode to use mouse as pencil
        else:
            # Obtain the coordinates of the mouse 
            cx = mouse.coords[0]
            cy = mouse.coords[1]
            # Draw a red cross in the mouse position
            if cx:
                cv2.line(operating_frame, (cx-5, cy-5), (cx+5, cy+5), (0, 0, 255), 5)
                cv2.line(operating_frame, (cx+5, cy-5), (cx-5, cy+5), (0, 0, 255), 5)
        # Waits 1 ms for a key input
        k = cv2.waitKey(1) & 0xFF
        # Converts the input into a string 
        key_chr = str(chr(k))
        # Operates on the pencil given the key pressed 
        if not key_Press(key_chr,operating_frame,draw_moves): break
        # Start/Continue/Stop of the Drawing if "d" is pressed
        if key_chr == "d":
            flag_draw = not flag_draw
            started_draw = True
        if flag_draw:
            if (cx,cy) != (None,None):
                # To draw Squares
                if key_chr == "s":
                    draw_moves[len(draw_moves)-1] = (Figure("square",(cox,coy),(cx,cy),draw_color,pencil_thickness))
                    cx_last,cy_last = cx,cy
                # To draw Circles
                elif key_chr == "o":
                    draw_moves[len(draw_moves)-1] = (Figure("circle",(cox,coy),(cx,cy),draw_color,pencil_thickness))
                    cx_last,cy_last = cx,cy
                # To draw Ellipses
                elif key_chr == "e":
                    draw_moves[len(draw_moves)-1] = (Figure("ellipse",(cox,coy),(cx,cy),draw_color,pencil_thickness))
                    cx_last,cy_last = cx,cy
                # To clean the canvas
                elif key_chr == 'c':
                    print('Clear canvas')
                    draw_moves = []
                    cx_last,cy_last = cx,cy
                # Else draw lines or dots following the pencil
                else:
                    try:
                        # For Shake Prevension Mode
                        if usp:
                            # Calculates the distance between 2 points
                            diffX = abs(cx_last - cx)
                            diffY = abs(cy_last - cy)
                            # If the distance is bigger than the threshold put a dot in location
                            if diffX>shake_threshold or diffY>shake_threshold: # this line performs shake detection
                                draw_moves.append(Figure("dot",(0,0),(cx_last,cy_last),draw_color,pencil_thickness))
                            # Else draw Lines between two points
                            else:
                                draw_moves.append(Figure("line",(cx_last,cy_last),(cx,cy),draw_color,pencil_thickness))
                        # Draw lines between two points in normal mode
                        else:
                            draw_moves.append(Figure("line",(cx_last,cy_last),(cx,cy),draw_color,pencil_thickness))
                    except:
                        cx_last,cy_last = cx,cy
                # Updates last position of the pencil
                if key_chr != "s" and key_chr != "o" and key_chr != "e" and key_chr != "c":   
                    cox,coy = cx,cy
                    cx_last,cy_last = cx,cy
        else:
            # Initiates the calculations for Accuracy after stopping the drawing 
            if key_chr == 'f' and use_grid:
                print("Finished painting, calculated the accuracy")
                # Accuracy given the painting and drawing
                accuracy_frame = redraw_Painting(operating_frame,draw_moves)
                # If user tries to calculate Accuracy after started to draw
                if started_draw:
                    # Returns the correct value in %
                    accuracy = calc_accuracy(accuracy_frame, zones, color_numbers,numbers_to_colors)
                # If user tries to calculate Accuracy before it started to draw
                else:
                    # Return Not a Number
                    accuracy = "NaN"
                # Updates the accuracy legend
                stats = colors_Legend(numbers_to_colors, accuracy)
                cv2.imshow(color_window, stats)
            # To clean the canvas
            if key_chr == 'c':
                print('Clear canvas')
                draw_moves = []
            cx_last,cy_last = cx,cy
        # re-draws all the actions to reproduce the sum of previous and current drawings in the current frame 
        operating_frame = redraw_Painting(operating_frame,draw_moves)
        # updates the Window with the current drawing
        cv2.imshow("Paint Window",operating_frame)
    # Closes all the windows and cam capture
    capture.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    # print("")
    main()