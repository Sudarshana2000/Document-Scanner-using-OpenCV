# Document-Scanner-using-OpenCV

Students like me are regular users of Document Scanners. Several doc-scanner apps like Adobe Scan and Camscanner are popular for clear and sharp image/PDF scan results, editing and sharing etc. Being fascinated by the application and having the knowledge of OpenCV, I chose to build one by myself.


This is an interractive document scanner.


- The user needs to provide the image.
![1](images/IMG1.JPG)


- All possible edges in the image will be determined using cv2.HoughLines().
![2](images/IMG2.JPG)


- Out of bunch of closely fitted lines, only unique lines are chosen.
![3](images/IMG3.JPG)


- Then, all possible intersecting points will be chosen.
![4](images/IMG4.JPG)


- Out of all possible quadrilaterals, the one with the largest area is chosen.
![5](images/IMG5.jpg)


- The predicted quadrilateral is displayed, which the user can modify using drag-and-drop of corner points.
![6](images/IMG6.GIF)


- In the entire procedure, to reset changes, press 'c', else press 'r' to proceed.
![7](images/IMG7.JPG)


- Finally the original scan and B&W scan are produced and displayed.
![8](images/IMG8.JPG)


- If the user is satisfied and wishes to store the results, go as per instructions provided and store the result(s) in the provided path.

