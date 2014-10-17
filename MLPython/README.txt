Three main scripts:
1. MLPython.py -> extracting features and storing them into .txt and .arff files
	Requirements to check:
	a. the format of math: MATH_* or __MATH_*__
	b. dumping either the text or position index of descriptions
	c. the candidates are either NP, NX, or NP_NX

2. SplitSet.py -> splitting a directory into training and test sets
3. CreateSingleFile.py -> concatenating current .arff files into either single training or testing file.
4. ReformatTagFile.py -> obtaining the predicted information from Weka returned files
5. Evaluation.py -> mostly copy the eval2.py used in ntcir10
6. DescriptionToXML.py -> convert the extracted descriptions into XML
7. CheckGraphAccuracy.py -> evaluates the context and description by considering the leaves and #hops of the math dependency graph
8. GraphOutsideWorld.py -> convert the apgl graph into igraph, and finally into a plotting-available format

Note:
1. Better to add NP/NX info in the printed *.txt files (ones associated with *.arff files)