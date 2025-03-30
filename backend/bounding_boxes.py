import cv2
import math

class BoundingBox():
    def __init__(self, x=0, y=0, width=0, height=0, thickness=3, color=(0, 0, 0),scaling=(1, 1), label=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.thickness = thickness
        self.color = color
        self.scaling = scaling
        self.update_bounds()
    
    def set_bounds_tl_br(self, tl, br):
        self.x = (tl[0] + br[0]) / 2
        self.y = (tl[1] + br[1]) / 2
        self.width = br[0] - tl[0]
        self.height = br[1] - tl[1]
        self.bounds = self.update_bounds()
        return self

    def set_bounds(self, coords : list):
        return self.set_bounds_tl_br(coords[0], coords[2])

    def resize(self, width, height):
        self.width = width
        self.height = height
        self.update_bounds()
        return self
    
    def set_pos(self, x, y):
        self.x = x
        self.y = y
        self.update_bounds()
        return self
    
    def set_label(self, label : str):
        self.label = label
        return self
    
    def update_bounds(self):
        self.bounds = [
            int((self.x - self.width / 2) * self.scaling[0]),  #xmin
            int((self.y - self.height / 2) * self.scaling[1]), #ymin
            int((self.x + self.width / 2) * self.scaling[0]),  #xmax
            int((self.y + self.height / 2) * self.scaling[1])  #ymax
        ]
        return self.bounds
    
    def get_bounds(self):
        return self.bounds
    
    def check_intersection(self, b):
        box : BoundingBox = b
        if self.x > box.bounds[0] and self.x < box.bounds[2] and self.y > box.bounds[1] and self.y < box.bounds[3]:
            return True
        return False
    
    def check_overlap(self, b, x_threshold, y_threshold):
        x_overlap = min(self.bounds[2], b.bounds[2]) - max(self.bounds[0], b.bounds[0])
        y_overlap = min(self.bounds[3], b.bounds[3]) - max(self.bounds[1], b.bounds[1])
        return x_overlap > -x_threshold and y_overlap > -y_threshold
    
    def render(self, frame, label=True, box=True, font_size=5):
        font_scale = font_size / 10
        font_thickness = int(math.ceil(10 / 10))
        if label: cv2.putText(frame, text=self.label, org=(self.bounds[0], int(self.bounds[1] - font_size / 2)), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=font_scale, color=self.color, thickness=font_thickness, lineType=cv2.LINE_AA)
        if box: cv2.rectangle(frame, pt1=(self.bounds[0], self.bounds[1]), pt2=(self.bounds[2], self.bounds[3]), color=self.color, thickness=int(self.thickness))

    def __str__(self):
        return f"x: {self.x}, y: {self.y}, Bounds: {self.bounds}, Label: {self.label}"

def sort_boxes(elements : list[BoundingBox], y_threshold : float) -> list[list[BoundingBox]]:
    if len(elements) == 0: return []

    #Sort Rows
    elements.sort(key=lambda a: a.y)
    sorted = []
    row = []
    current_row = elements[0].y

    #Group Rows
    for i in elements:
        if i.y - current_row < y_threshold:
            row.append(i)
        else:
            current_row = i.y
            sorted.append(row)
            row = [i]
    sorted.append(row)
    
    #Sort Rows
    for i in sorted:
        i.sort(key=lambda a: a.x)

    return sorted

def group_boxes(elements : list[list[BoundingBox]], x_threshold, y_threshold) -> list[list[BoundingBox]]:
    ##Note element list should already be sorted in top down left right order
    if len(elements) == 0: return []

    searched : list[list[bool]] = []
    grouped_rows : list[list[BoundingBox]] = []
    grouped_boxes : list[list[BoundingBox]] = []

    #Merge Rows
    for r in elements:
        row : list[BoundingBox] = []
        b = r[0]
        for b1 in r:
            if b == b1: continue
            if b.check_overlap(b1, x_threshold, y_threshold):
                b = merge_boxes(b, b1)
            else:
                row.append(b)
                b = b1
        row.append(b)
        searched.append([False] * len(row))
        grouped_rows.append(row)
    
    '''
        Note: Chose not to include columns as usecase is usally just reading text line by line
    '''
    # #Merge Columns
    # for r in range(len(grouped_rows)):
    #     row = []
    #     for c in range(len(grouped_rows[r])):
    #         if searched[r][c]: continue
    #         b = grouped_rows[r][c]
    #         searched[r][c] = True
    #         for r1 in range(r + 1, len(grouped_rows)):
    #             for c1 in range(len(grouped_rows[r1])):
    #                 b1 = grouped_rows[r1][c1]
    #                 if b.check_overlap(b1, x_threshold, y_threshold):
    #                     searched[r1][c1] = True
    #                     b = merge_boxes(b, b1)
    #         row.append(b)
    #     grouped_boxes.append(row)

    return grouped_rows

def merge_boxes(b1 : BoundingBox, b2 : BoundingBox) -> BoundingBox:
    if b1 == None: return b2
    if b2 == None: return b1
    bounds = [
        min(b1.bounds[0], b2.bounds[0]), #xmin
        min(b1.bounds[1], b2.bounds[1]), #ymin
        max(b1.bounds[2], b2.bounds[2]), #xmax
        max(b1.bounds[3], b2.bounds[3]), #ymax
    ]
    labels = b1.label + ' ' + b2.label #Combine Labels
    return BoundingBox(label=labels).set_bounds_tl_br((bounds[0], bounds[1]), (bounds[2], bounds[3])) #Return new BoundingBox