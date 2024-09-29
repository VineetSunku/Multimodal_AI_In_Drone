import joblib

classifierModel = joblib.load('./models/VisualClassifierLogReg.pkl')
# print(classifierModel.predict(["follow the other drone for 30 seconds"]))

def VisionClassifier(prompt):
    """ Returns 0 if the prompt does not require a camera input. \n
        Returns 1 if it requires a camera input"""
    return int(round(classifierModel.predict([prompt])[0]))