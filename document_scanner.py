import cv2
import numpy as np
import mouse_click_event


# store details of rectangle corner-points at every stage of evaluation
class rect_details:
    def __init__(self,idx,interp_M):
        self.indices=idx
        self.points=np.asarray([interp_M[idx[0],idx[1]],interp_M[idx[1],idx[2]],interp_M[idx[2],idx[3]],interp_M[idx[3],idx[0]]],dtype=np.float32)
        self.area=cv2.contourArea(self.points)


# checks for intersecting point between the two lines
def l_inter(line1,line2):
    r1,t1 = line1
    r2,t2 = line2
    A= np.array([[np.cos(t1),np.sin(t1)],[np.cos(t2),np.sin(t2)]])
    B= np.array([[r1],[r2]])
    if abs(t1-t2)>np.pi/4:
        try:
            return [np.linalg.solve(A, B)]
        except:
            return False
    return False


# checks for all outer intersecting points in the set of lines
def points_inter(L,M,interp_M):
    intersections = []
    for i, line1 in enumerate(L[:-1]):
        for j, line2 in enumerate(L[i+1:],i+1):
            res=l_inter(line1, line2)
            if res:
                if res[0][0,0]>0 and res[0][1,0]>5:
                    intersections.append(res)
                    M[i][j]=M[j][i]=1
                    interp_M[i,j]=interp_M[j,i]=res[0].reshape((1,2))[0]
                else:
                    interp_M[i,j]=interp_M[j,i]=np.NaN
            else:
                interp_M[i,j]=interp_M[j,i]=np.NaN
    return intersections,M,interp_M


# draw all possible edges in the image
def draw_lines(image,L):
    for l in L:
        [rho,theta]=l[0]
        a=np.cos(theta)
        b=np.sin(theta)
        x0=a*rho
        y0=b*rho
        x1=int(x0 + 1000*(-b))
        y1=int(y0 + 1000*a)
        x2=int(x0 - 1000*(-b))
        y2=int(y0 - 1000*a)
        res=cv2.line(image,(x1,y1),(x2,y2),(0,0,255),2)
    return image


# Evaluate all possible edges using Hough Lines and sort to only unique ones from bunch of lines
def find_threshold(image,edge,thres):
    img=image.copy()
    lines=cv2.HoughLines(edge,rho=1,theta=np.pi/180,threshold=thres)
    img=draw_lines(img,lines)
    cv2.imshow("check",img)
    key=cv2.waitKey(0) & 0xFF
    if key==ord('c'):
        return False
    #else enter key 'r'
    c=0
    lu=[]
    for l in lines:
        c=c+1
        for lt in lines[c:]:
            t=0
            if lt[0][0]!=l[0][0]:
                k=abs(lt[0]-l[0])<[50.,0.5]
                if k[0] and k[1]:
                    t=-1
                    break
        if t==0:
            lu.append(l)
    img=image.copy()
    img=draw_lines(img,lu)
    cv2.imshow("check",img)
    key=cv2.waitKey(0) & 0xFF
    if key==ord('c'):
        return False
    else:
        #enter key 'r'
        return lu


# Set the order of rectangle corner points as - top-left, top-right, bottom right, bottom left
def order_points(points):
    rect=np.zeros((4,2),dtype="float32")
    x=points[np.argsort(points,0)[:,0]]
    x1=x[:2,:]
    x2=x[2:,:]
    rect[3]=x1[np.argsort(x1,0)[:,1]][1,:]
    rect[2]=x2[np.argsort(x2,0)[:,1]][1,:]
    rect[1]=x2[np.argsort(x2,0)[:,1]][0,:]
    rect[0]=x1[np.argsort(x1,0)[:,1]][0,:]
    return rect


# Let users correct the predicted corner points of rectangle in real time (interactive way) using mouse_click_event function
# Converts the perspective view of chosen rectangle to top-down (bird's eye) view
def four_point_transform(image,points):
    rect=order_points(points)
    corners=[tuple(i) for i in rect]
    corners=mouse_click_event.adjust_coor_quad(image,corners)
    rect=[list(i) for i in corners]
    rect=np.array(rect,dtype="float32")
    (tl,tr,br,bl)=rect
    width1=np.sqrt(((br[0]-bl[0])**2)+((br[1]-bl[1])**2))
    width2=np.sqrt(((tr[0]-tl[0])**2)+((tr[1]-tl[1])**2))
    width=max(int(width1),int(width2))
    height1=np.sqrt(((tr[0]-br[0])**2)+((tr[1]-br[1])**2))
    height2=np.sqrt(((tl[0]-bl[0])**2)+((tl[1]-bl[1])**2))
    height=max(int(height1),int(height2))
    dest=np.array([[0,0],[width-1,0],[width-1,height-1],[0,height-1]],dtype="float32")
    M=cv2.getPerspectiveTransform(rect,dest)
    warped=cv2.warpPerspective(image,M,(width,height))
    return warped


# 1st, simple method to apply doc-scanner
def scanner(image):
    img=image.copy()
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    gray=cv2.GaussianBlur(gray,(5,5),0,0)
    edged=cv2.Canny(gray,75,200)
    #threshold=cv2.adaptiveThreshold(gray,255.0,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,19,9)
    contours,hierarchy=cv2.findContours(edged.copy(),cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    contour=sorted(contours,key=cv2.contourArea,reverse=True)[:5]
    for c in contour:
        peri=cv2.arcLength(c,True)
        approx=cv2.approxPolyDP(c,0.1*peri,True)
        if len(approx)==4:
            screen=approx
            break
    res=cv2.drawContours(img,[screen],-1,(0,0,255),2)
    #ratio=image.shape[0]/500.0
    warped=four_point_transform(image,screen.reshape(4,2))
    #cv2.imshow("output in colour",warped)
    gray=cv2.cvtColor(warped,cv2.COLOR_BGR2GRAY)
    gray=cv2.GaussianBlur(gray,(5,5),0,0)
    threshold=cv2.adaptiveThreshold(gray,255.0,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,19,9)
    #cv2.imshow("output in black & white",threshold)
    return warped,threshold


# 2nd, simple method to apply doc-scanner
def camscanner(image):
    img=image.copy()
    h,w=image.shape[:2]
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    _,binary=cv2.threshold(gray,127,255,cv2.THRESH_BINARY_INV)
    contours,hierarchy=cv2.findContours(binary.copy(),cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    contour=sorted(contours,key=cv2.contourArea,reverse=True)
    for i in range(len(contour)):
        if cv2.contourArea(contour[i])<(h*w*0.9):
            contour=contour[i:]
            break
    contour=contour[:5]
    for c in contour:
        peri=cv2.arcLength(c,True)
        approx=cv2.approxPolyDP(c,0.1*peri,True)
	if len(approx)==4:
            screen=approx
            break
    try:
	warped=four_point_transform(image,screen.reshape(4,2))
    except:
	print("Could not find edges!")
    #cv2.imshow("output in colour",warped)
    gray=cv2.cvtColor(warped,cv2.COLOR_BGR2GRAY)
    _,binary=cv2.threshold(gray,127,255,cv2.THRESH_BINARY)
    #cv2.imshow("output in black & white",binary)
    return warped,binary


# 3rd, most preffered but tricky method to apply doc-scanner
def doc_scanner(image):
    image=cv2.resize(image,(800,650))
    img=image.copy()
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    _,binary=cv2.threshold(gray,127,255,cv2.THRESH_BINARY)
    edge=cv2.Canny(binary,100,200)
    while True:
        thres=int(input("Enter threshold value: "))
        res=find_threshold(image.copy(),edge,thres)
        if res:
            lu=res
            break
    #checking for possible hough line edges
    img=draw_lines(img,lu)
    cv2.imshow("check",img)
    key=cv2.waitKey(0) & 0xFF
    lu=np.asarray(lu).reshape((len(lu),2))
    interp_M=np.zeros((len(lu),len(lu),2))
    M=np.zeros((len(lu),len(lu)))
    for i in range(len(lu)):
        interp_M[i,i]=np.NaN
    points,M,interp_M=points_inter(lu,M,interp_M)
    points=np.asarray(points).reshape(len(points),2)
    rect=[]
    rect1=[]
    def find_rect_lines(idx,L):
        nonlocal M,rect,rect1
        L.append(idx)
        if len(L)==4 and M[idx][L[0]]==1:
            if set(L) not in rect1:
                rect.append(L)
                rect1.append(set(L))
                return
        indices=np.where(M[idx]==1)[0]
        indices=list(set(indices)-set(L))
        if len(indices)==0:
            return
        for i in indices:
            find_rect_lines(i,L.copy())
    for i in range(len(lu)):
        find_rect_lines(i,[])
    #checking for possible intersecting points
    for i in points:
        res=cv2.circle(img,tuple(i),5,(0,255,0),-1)
    cv2.imshow("check",img)
    key=cv2.waitKey(0) & 0xFF
    rect_list=[]
    for i in rect:
        rec_obj=rect_details(i,interp_M)
        rect_list.append(rec_obj)
    rect_list.sort(key = lambda r: r.area,reverse=True)
    #checking for predicted edges
    for i in range(4):
        res=cv2.line(img,tuple(rect_list[0].points[i]),tuple(rect_list[0].points[(i+1)%4]),(255,0,0),2)
    cv2.imshow("check",img)
    key=cv2.waitKey(0) & 0xFF
    coor=rect_list[0].points
    warped=four_point_transform(image.copy(),coor)
    #cv2.imshow("output in colour",warped)
    gray=cv2.cvtColor(warped,cv2.COLOR_BGR2GRAY)
    _,binary=cv2.threshold(gray,127,255,cv2.THRESH_BINARY)
    #cv2.imshow("output in black & white",binary)
    return warped,binary


if __name__=='__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("image", required=True, help="path to input image")
    args = vars(ap.parse_args())
    img = cv2.imread(args.image)
    print("--------Instruction--------")
    print("Press 'r' to continue after every step")
    print("Press 'c' to reset the change applied")
    warped,binary=doc_scanner(img)	# can change this method as per user's choice
    cv2.imshow("warped",warped)
    cv2.imshow("binary",binary)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    ans=int(input("Want to save? (0 to quit, 1 to save original scan, 2 to save B&W scan) : "))
    if(ans!=0):
        output_path=input("Enter output path: ")
	if(ans==1):
	    cv2.imwrite(output_path,warped)
	else:
	    cv2.imwrite(output_path,binary)
