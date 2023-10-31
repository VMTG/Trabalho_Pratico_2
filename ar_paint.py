#!/usr/bin/env python3
#shebang line to inform the OS that the content is in python

#!/usr/bin/env python3

import json
import argparse
import sys
import cv2
import numpy as np
from math import sqrt
from datetime import datetime

draw_color = (255,255,255)
pencil_thickness = 5
shake_threshold = 50
centroid_area = 0 

def initialization():
    # Input Arguments
    parser = argparse.ArgumentParser(description='Ar Paint ')
    parser.add_argument('-j','--json',type = str, required= False , help='Full path to json file', default='limits.json')
    parser.add_argument('-usp','--use_shake_prevention', action='store_true', help='Use shake prevention mode, change shake prevention threshold using , and .')
    parser.add_argument('-ucc','--use_cam_canvas', action='store_true', help='Use camera as canvas')
    parser.add_argument('-um','--use_mouse', action='store_true', help='Use mouse as the pencil')
    args = vars(parser.parse_args())
   

    path = 'limits.json' if not args['json'] else args['json'] # Path for the json file
    usp = args['use_shake_prevention'] # Shake prevention mode
    ucc = args['use_cam_canvas'] # Use live feed from the cam to be used as the canvas
    um = args['use_mouse'] # Use mouse as the pencil
    return path, usp, ucc, um

def readFile(path):
    try:
        with open(path, 'r') as openfile:
            json_object = json.load(openfile)
            limits = json_object['limits']
    # if the file doesn't exist, send out an error message and quit
    except FileNotFoundError:
        sys.exit('The .json file with the color data doesn\'t exist.')

    return limits

def get_centroid(mask) :
    global centroid_area,shake_threshold
    # find all contours (objects)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    skip = False
    # if we detect objects, let's find the biggest one, make it green and calculate the centroid
    if cnts:

        # find the biggest object
        cnt = max(cnts, key=cv2.contourArea)

        cnt_Area = cv2.contourArea(cnt)
        # diff_Area = abs(centroid_area-cnt_Area)
        # if diff_Area > (cnt_Area/2):
        #     skip = True
        #     centroid_area = cnt_Area-(diff_Area*0.25)

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
        if cX: # it's enough to check either cX or cY, if one is None then both are None
            cv2.line(image_result, (cX-8, cY-8), (cX+8, cY+8), (0, 0, 255), 5)
            cv2.line(image_result, (cX+8, cY-8), (cX-8, cY+8), (0, 0, 255), 5)

    # if we don't detect any objects, we just show the mask as it is
    else:
        image_result = cv2.merge((mask, mask, mask))
        cX = None
        cY = None
        
    return (cX,cY), image_result , skip

def key_press(key_input,canvas):
    global draw_color, pencil_thickness, shake_threshold
    height,width,_ = np.shape(canvas)
    max_threshold = max(height,width)
        # quit program
    if key_input=='q':
        return False
        # change color to Red
    elif key_input=='r':
        draw_color = (0,0,255)
        # change color to Green
    elif key_input=='g':
        draw_color = (0,255,0)
        # change color to Blue
    elif key_input=='b':
        draw_color = (255,0,0)
        # decrease pencil size
    elif key_input=='-':
        if pencil_thickness > 0:
            pencil_thickness -= 5
        # increase pencil size
    elif key_input=='+':
        if pencil_thickness < 50:
            pencil_thickness += 5
        # save canvas 
    elif key_input=='w':
        date = datetime.now()
        formatted_date = date.strftime("%a_%b_%d_%H:%M:%S")
        name_canvas = 'drawing_' + formatted_date + '.png'
        name_canvas_colored = 'drawing_' + formatted_date + '_colored.jpg'
        cv2.imwrite(name_canvas, canvas)
        cv2.imwrite(name_canvas_colored, canvas)
    elif key_input==',':
        if shake_threshold > 0:
            shake_threshold -= 50 
            print("Shake prevension Threshold: ",shake_threshold/max_threshold*100,"%")
    elif key_input=='.':
        if shake_threshold < (max_threshold-50):
            shake_threshold += 50
            print("Shake prevension Threshold: ",shake_threshold/max_threshold*100,"%")
    return True

class Figure:

    def __init__(self,type,origin,final,colour,thickness):
        self.type = type
        self.coord_origin = origin
        self.coord_final = final
        self.color = colour
        self.thickness = thickness

def redraw_painting(frame, figures):
    for step in figures:
        if step.type == "square":
            cv2.rectangle(frame,step.coord_origin,step.coord_final,step.color,step.thickness)
        
        elif step.type == "circle":
            difx = step.coord_final[0] - step.coord_origin[0]
            dify = step.coord_final[1] - step.coord_origin[1]
            radious = round(sqrt(difx**2 + dify**2))
            cv2.circle(frame,step.coord_origin,radious,step.color,step.thickness) 

        elif step.type == "ellipse":
            meanx = (step.coord_final[0] - step.coord_origin[0])/2
            meany = (step.coord_final[1] - step.coord_origin[1])/2
            center = (round(meanx + step.coord_origin[0]), round(meany + step.coord_origin[1]))
            axes = (round(abs(meanx)), round(abs(meany)))
            cv2.ellipse(frame,center,axes,0,0,360,step.color,step.thickness)
        
        elif step.type == "line":
            cv2.line(frame, step.coord_origin,step.coord_final, step.color,step.thickness)
        
        elif step.type == "dot":        
            cv2.circle(frame, step.coord_final, 1, step.color,step.thickness) 

class Mouse:
    
    def __init__(self):
        self.coords = (None,None)
        self.pressed = False

    def update_mouse(self,event,x,y,flags,param):
        self.coords = (x,y)

        if event == cv2.EVENT_LBUTTONDOWN:
            self.pressed = True
        elif event == cv2.EVENT_LBUTTONUP:
            self.pressed = False
               
def main():
    global draw_color, pencil_thickness
    # setting up the video capture
    path, usp, use_cam, use_mouse = initialization()
    ranges = readFile(path) 

    capture = cv2.VideoCapture(0)
    _, frame = capture.read()
    cv2.imshow("Original window",frame)

    height,width,_ = np.shape(frame)
    paint_window = np.zeros((height,width,4))
    paint_window.fill(255)
    cv2.imshow("Paint Window",paint_window)
    
    range_lows = (ranges['B']['min'], ranges['G']['min'], ranges['R']['min'])
    range_highs = (ranges['B']['max'], ranges['G']['max'], ranges['R']['max'])
    
    draw_moves = []
    flag_draw = False

    if use_mouse:
        mouse = Mouse()
        cv2.setMouseCallback("Paint Window", mouse.update_mouse)

    ## Operação em contínuo ##
    while True:
        _,frame = capture.read()
        flipped_frame = cv2.flip(frame, 1)
        paint_window.fill(255)
        if use_cam: 
            operating_frame = flipped_frame
        else:
            operating_frame = paint_window
        
        frame_mask = cv2.inRange(flipped_frame, range_lows, range_highs)

        frame_wMask = cv2.bitwise_and(flipped_frame,flipped_frame, mask = frame_mask)
        cv2.imshow("Original window",frame_wMask)

        if not use_mouse:    
            (cx,cy),frame_test,skip = get_centroid(frame_mask)
            cv2.imshow("Centroid window", frame_test)
            if skip: continue
        else:
            cx = mouse.coords[0]
            cy = mouse.coords[1]
            
            if cx:
                cv2.line(operating_frame, (cx-5, cy-5), (cx+5, cy+5), (0, 0, 255), 5)
                cv2.line(operating_frame, (cx+5, cy-5), (cx-5, cy+5), (0, 0, 255), 5)
    

        k = cv2.waitKey(1) & 0xFF

        key_chr = str(chr(k))
        if not key_press(key_chr,operating_frame): break

        if key_chr == "d":
            flag_draw = True

        if flag_draw :

            if (cx,cy) != (None,None):
                if key_chr == "s":
                    draw_moves[len(draw_moves)-1] = (Figure("square",(cox,coy),(cx,cy),draw_color,pencil_thickness))
                    cx_last,cy_last = cx,cy
                elif key_chr == "o":
                    draw_moves[len(draw_moves)-1] = (Figure("circle",(cox,coy),(cx,cy),draw_color,pencil_thickness))
                    cx_last,cy_last = cx,cy
                elif key_chr == "e":
                    draw_moves[len(draw_moves)-1] = (Figure("ellipse",(cox,coy),(cx,cy),draw_color,pencil_thickness))
                    cx_last,cy_last = cx,cy
                elif key_chr == 'c':
                    draw_moves = []
                    cx_last,cy_last = cx,cy
                else:
                    try:
                        if usp:
                            diffX = abs(cx_last - cx)
                            diffY = abs(cy_last - cy)
                            if diffX>shake_threshold or diffY>shake_threshold: # this line performs shake detection
                                draw_moves.append(Figure("dot",(0,0),(cx_last,cy_last),draw_color,pencil_thickness))
                            else:
                                draw_moves.append(Figure("line",(cx_last,cy_last),(cx,cy),draw_color,pencil_thickness))
                        else:
                            draw_moves.append(Figure("line",(cx_last,cy_last),(cx,cy),draw_color,pencil_thickness))
                    except:
                        cx_last,cy_last = cx,cy
                if k == 0xFF:
                    cox,coy = cx,cy
                    cx_last,cy_last = cx,cy
    
            redraw_painting(operating_frame,draw_moves)
            

        cv2.imshow("Paint Window",operating_frame)

    capture.release()
    cv2.destroyAllWindows()



if __name__ == '__main__':
    main()