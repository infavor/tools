
from os import remove
import matplotlib.pyplot as plt
import statistics as stt


import logging
import sys



from PIL import Image
import numpy as np


root = logging.getLogger()
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
handler.setFormatter(formatter)
root.addHandler(handler)

## translate pixel values into real value
VERTICAL_OP = 1
HORIZONTAL_OP = 1000 


def getpixels(path):
    im = Image.open(path)
    pixels = list(im.getdata())
    width, height = im.size
    pixels = [pixels[i * width:(i + 1) * width] for i in range(height)]
    return width,height,pixels



class ScanLine:
    
    def __init__(self) -> None:
        self.lines = {}    
        pass

    def add(self, c, r ):
        if c in self.lines.keys():
            self.lines[c].add(r)
        else:
            self.lines[c] = {r}


    def finish_scan(self):
        self.lines = {k : v for k,v in sorted(self.lines.items(),  key=lambda a:a[0] )}
        remove_keys = []
        for k in self.lines.keys():
            self.lines[k] =  sorted( self.lines[k] )
            if len(self.lines[k]) < 6:
                remove_keys.append(k)
        for k in remove_keys:
            self.lines.pop(k)


def scanimage(w ,h, px):

    scl = ScanLine()
    for r in range(h):
        for c in range(w):
            if px[r][c][3] > 0: ## default 4 channels
                scl.add(c,r)
    scl.finish_scan()
    return scl





def segment(seg, scl):


    cset = sorted(scl.lines.keys())
    # root.info(cset)
    ## assume that pixels are consecutive
    left = -1
    right = -1
    last = -1
    cur = 0
    for c in cset:
        if last == -1:
            last = c
            left = c
            right = c
            continue
        
        if c == last + 1:
            right = max(right , c)
        else:
            if cur == seg:
                return (left, right)
            else:
                cur +=1
                left = c
                right = c
        
        last = c

    # root.info(left)
    # root.info(right)
    if cur == seg:
        return (left , right)

    return (-1, -1) ## no segment is found


def getop(scl, left, right):

    lls = []


    for i in range(left, right+1):
        # root.info( (  scl.lines[i] )   )    
        lls.append(max(scl.lines[i] )  - min(scl.lines[i])   )
    
    # root.info(lls)
    res =  np.mean( ( np.array(lls) ) )
    # root.info(res)
    return  HORIZONTAL_OP * 1.0 / res



def bin_search(list , key):

    l = 0
    r = len(list)
    while l < r:
        mid = l + (r - l) // 2
        if list[mid] < key: 
            l = mid + 1 
        else:
            r = mid
    if l >= len(list) or list[l] != key:
        return -1
    return l

"""
 this class is designed for real data to plot whole curve.
 For each single input image ,it translates pixels values into real values based on #OP,
 so that a coordinate system to treat different ranges of values ​​in the same way.
"""
class DataView:
    
    def __init__(self, op, w , h, scl : ScanLine) -> None:
        self.scl = scl
        self.width = w
        self.height = h
        self.x = []
        self.real_x = []
        self.real_y = []

        self.op = op
    
    def assign_xy(self):
        req_seg = 1
        while 1:
            target_seg = segment(req_seg, self.scl)

            tlen = target_seg[1] - target_seg[0]
            if tlen < 10:
                req_seg +=1
            else:
                break
        root.info("-----")
        root.info(target_seg[0])
        root.info(target_seg[1])

        xlist =  list( self.scl.lines.keys() )
        idx_l = bin_search(  xlist ,  target_seg[0] )
        idx_r = bin_search(  xlist ,  target_seg[1] )

        self.x = xlist[idx_l : idx_r + 1] 


        remove_c = []

        for c in range( target_seg[0], target_seg[1] +1  ):
            drop = 0
            ys =np.array(self.scl.lines[c])
            ys_avg = self.height / 2 
            ys_high = ys[ys > ys_avg ]
            if ys_high.size == 0:
                root.warn("zero len %d col" %(c))
                root.info(ys_high)
                drop = 1
            ys_low = ys[ys < ys_avg ]
            if ys_low.size == 0:
                root.warn("zero len %d col" %(c))
                root.info(ys_low)
                drop = 1
            if drop:

                remove_c.append(c)
                continue

            self.real_y.append(
                np.mean(ys_high ) - np.mean(ys_low)
            )

        x_clone = { k for k in self.x  }
        for k in remove_c:
            x_clone.remove(k)

          

        self.x = sorted(x_clone)


        x0 = self.x[0]
        # print(self.x)
        self.real_x =  [ self.op * (i - x0 ) for i in self.x  ]
        root.info("x y : (%d , %d)"  %(  len(self.real_x), len(self.real_y) ) )
            




def getdata(path):
    w,h,px = getpixels(path)
    scl = scanimage(w,h, px) 
    left, right = segment(0, scl)
    # root.info(left)
    # root.info(right)
    op = getop(scl,left, right)
    # root.info(op)

    dv = DataView(op, w, h, scl)

    dv.assign_xy()
    return dv

if __name__ == "__main__":



    dv1 = getdata("./2/1000-left.jpg")
    dv2 = getdata("./2/1000-right.jpg")
    


    # left, right = segment(1, scl)
    # root.info(left)
    # root.info(right)

    ##i
    plt.plot(dv1.real_x, dv1.real_y)
    plt.plot(dv2.real_x, dv2.real_y)
    plt.show()



