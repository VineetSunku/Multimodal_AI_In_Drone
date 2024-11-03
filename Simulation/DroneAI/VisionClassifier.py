import joblib

classifierModel = joblib.load('./DroneAI/models/VisualClassifierLogReg.pkl')

def visionClassifier(prompt):
    """ Returns 0 if the prompt does not require a camera input. \n
        Returns 1 if it requires a camera input"""
    return int(round(classifierModel.predict([prompt])[0]))