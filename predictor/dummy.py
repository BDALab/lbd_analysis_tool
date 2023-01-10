import random
import pickle
import numpy as np


class DummyPredictor(object):
    """Class implementing the Dummy Predictor"""

    def predict(self, X):
        return self.predict_proba(X)[0, 1]

    def predict_proba(self, X):
        a = random.random()
        b = 1 - a
        return np.array([a, b]).reshape(1, -1)


if __name__ == '__main__':
    p = DummyPredictor()
    print(p.predict_proba(np.array([1, 2, 3])))
    print(p.predict(np.array([1, 2, 3])))

    with open('models/dummy_predictor.pkl', 'wb') as f:
        pickle.dump(p, f)

    with open('models/dummy_predictor.pkl', 'rb') as f:
        pickle.load(f)
