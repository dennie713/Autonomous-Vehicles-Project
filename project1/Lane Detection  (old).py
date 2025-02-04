
# import library
import matplotlib.pyplot as plt
import cv2
import os, glob
import numpy as np
from moviepy.editor import VideoFileClip

# definition
def show_images(images, cmap = None):
    cols = 2
    rows = (len(images)+1)//cols
    
    plt.figure(figsize=(10,11))
    for i, image in enumerate(images):
        plt.subplot(rows,cols,i+1)
        cmap = 'gray' if len(image.shape) == 2 else cmap
        plt.imshow(image, cmap = cmap)
        plt.xticks([])
        plt.yticks([])
    plt.tight_layout(pad = 0, h_pad = 0, w_pad = 0)
    plt.show()
    
def select_rgb_white_yellow(image):
    # white color mask
    lower = np.uint8([200, 200, 200])
    upper = np.uint8([255, 255, 255])
    white_mask = cv2.inRange(image, lower, upper)
    # yellow color mask
    lower = np.uint8([190, 190,   0])
    upper = np.uint8([255, 255, 255])
    yellow_mask = cv2.inRange(image, lower, upper)
    # combine the mask
    mask = cv2.bitwise_or(white_mask, yellow_mask)
    return cv2.bitwise_and(image, image, mask = mask)

    
def select_white_yellow(image):
    converted = convert_hls(image)
    # white color mask
    lower = np.uint8([  0, 180,   0])
    upper = np.uint8([255, 255, 255])
    white_mask = cv2.inRange(converted, lower, upper)
    # yellow color mask
    lower = np.uint8([ 10,   0, 100])
    upper = np.uint8([ 40, 255, 255])
    yellow_mask = cv2.inRange(converted, lower, upper)
    # combine the mask
    mask = cv2.bitwise_or(white_mask, yellow_mask)
    return cv2.bitwise_and(image, image, mask = mask)

def convert_hsv(image):
    return cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

def convert_hls(image):
    return cv2.cvtColor(image, cv2.COLOR_RGB2HLS)

def convert_gray_scale(image):
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

def apply_smoothing(image, kernel_size = 15):
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

def detect_edges(image, low_threshold = 50, high_threshold = 150):
    return cv2.Canny(image, low_threshold, high_threshold)

def filter_region(image, vertices):
    mask = np.zeros_like(image)
    if len(mask.shape) == 2:
        cv2.fillPoly(mask, vertices, 255)
    else:
        cv2.fillPoly(mask, vertices, (255,)*mask.shape[2]) # in case, the input image has a channel dimension         
    return cv2.bitwise_and(image, mask)
    
def select_region(image):
    rows, cols = image.shape[:2]
    bottom_left  = [cols*0.1, rows*0.9]
    top_left     = [cols*0.35, rows*0.7]
    bottom_right = [cols*0.9, rows*0.9]
    top_right    = [cols*0.65, rows*0.7] 
    # the vertices are an array of polygons (i.e array of arrays) and the data type must be integer
    vertices = np.array([[bottom_left, top_left, top_right, bottom_right]], dtype = np.int32)
    return filter_region(image, vertices)

def hough_lines(image):
    return cv2.HoughLinesP(image, rho=1, theta=np.pi/180, threshold=20, minLineLength=20, maxLineGap=300)

def draw_lines(image, lines, color = [255, 0, 0], thickness = 2, make_copy = True):
    if make_copy:
        image = np.copy(image)  # don't want to modify the original
    for line in lines:
        for x1, y1, x2, y2 in line:
            cv2.line(image, (x1, y1), (x2, y2), color, thickness)
    return image

def average_slope_intercept(lines):
    left_lines    = [] # (slope, intercept)
    left_weights  = [] # (length,)
    right_lines   = [] # (slope, intercept)
    right_weights = [] # (length,)
    
    for line in lines:
        for x1, y1, x2, y2 in line:
            if x2==x1:
                continue # ignore a vertical line
            slope = (y2-y1)/(x2-x1)
            intercept = y1 - slope*x1
            length = np.sqrt((y2-y1)**2+(x2-x1)**2)
            if slope < 0 : # y is reversed in image
                if slope > -100:
                    left_lines.append((slope, intercept))
                    left_weights.append((length))
            elif slope > 0:
                if slope < 100:
                    right_lines.append((slope, intercept))
                    right_weights.append((length))
    
    # add more weight to longer lines    
    left_lane  = np.dot(left_weights,  left_lines) /np.sum(left_weights)  if len(left_weights) >0 else None
    right_lane = np.dot(right_weights, right_lines)/np.sum(right_weights) if len(right_weights)>0 else None
    
    return left_lane, right_lane # (slope, intercept), (slope, intercept)

def make_line_points(y1, y2, line):
    if line is None:
        return None
    
    slope, intercept = line
    
    # make sure everything is integer as cv2.line requires it
    x1 = int((y1 - intercept)/slope)
    x2 = int((y2 - intercept)/slope)
    y1 = int(y1)
    y2 = int(y2)
    
    return ((x1, y1), (x2, y2))

def lane_lines(image, lines):
    left_lane, right_lane = average_slope_intercept(lines)
    
    y1 = image.shape[0] # bottom of the image
    y2 = y1*0.6         # slightly lower than the middle

    left_line  = make_line_points(y1, y2, left_lane)
    right_line = make_line_points(y1, y2, right_lane)
    
    return left_line, right_line

    
def draw_lane_lines(image, lines, color=[255, 0, 0], thickness=20):
    # make a separate image to draw lines and combine with the orignal later
    line_image = np.zeros_like(image)
    for line in lines:
        if line is not None:
            cv2.line(line_image, *line,  color, thickness)
    # image1 * α + image2 * β + λ
    # image1 and image2 must be the same shape.
    return cv2.addWeighted(image, 1.0, line_image, 0.95, 0.0)
             

# load image
test_images = [plt.imread(path) for path in glob.glob('test.jpg')]

show_images(test_images)

# color selection
show_images(list(map(select_rgb_white_yellow, test_images)))

# change color into different color space
show_images(list(map(convert_hsv, test_images)))
show_images(list(map(convert_hls, test_images)))

# doing color selection in hls color space
white_yellow_images = list(map(select_white_yellow, test_images))
show_images(white_yellow_images)

# convert into gray scale
gray_images = list(map(convert_gray_scale, white_yellow_images))
show_images(gray_images)

# doing Gaussian Blur
blurred_images = list(map(lambda image: apply_smoothing(image), gray_images))
show_images(blurred_images)

# Canny Edge detection
edge_images = list(map(detect_edges, blurred_images))
show_images(edge_images)

# ROI Subtraction
roi_images = list(map(select_region, edge_images))
show_images(roi_images)

# Hough Transformation
list_of_lines = list(map(hough_lines, roi_images))

line_images = []
for image, lines in zip(test_images, list_of_lines):
    line_images.append(draw_lines(image, lines))
    
show_images(line_images)

lane_images = []
for image, lines in zip(test_images, list_of_lines):
    lane_images.append(draw_lane_lines(image, lane_lines(image, lines)))

show_images(lane_images)

#%%
from collections import deque
QUEUE_LENGTH=50
class LaneDetector:
    def __init__(self):
        self.left_lines = deque(maxlen=QUEUE_LENGTH)
        self.right_lines = deque(maxlen=QUEUE_LENGTH)
    def process(self, image):
        white_yellow = select_white_yellow(image)
        gray = convert_gray_scale(white_yellow)
        smooth_gray = apply_smoothing(gray)
        edges = detect_edges(smooth_gray)
        regions = select_region(edges)
        lines = hough_lines(regions)
        left_line, right_line = lane_lines(image, lines)
        def mean_line(line, lines):
            if line is not None:
                lines.append(line)
            if len(lines)>0:
                line = np.mean(lines, axis=0, dtype=np.int32)
                line = tuple(map(tuple, line))
                # make sure it's tuples not numpy array for cv2.line to work
            return line

        left_line = mean_line(left_line, self.left_lines)
        right_line = mean_line(right_line, self.right_lines)

        return draw_lane_lines(image, (left_line, right_line))
def process_video(video_input, video_output):
     detector = LaneDetector()

     clip = VideoFileClip(os.path.join('test_videos', video_input))
     processed = clip.fl_image(detector.process)
     processed.write_videofile(os.path.join('output_videos', video_output), audio=False)
    

process_video('challenge.mp4', 'challenge.mp4')    
process_video('solidYellowLeft.mp4', 'solidYellowLeft.mp4')
process_video('solidWhiteRight.mp4', 'solidWhiteRight.mp4')