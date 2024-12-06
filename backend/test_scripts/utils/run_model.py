### print python path
import sys
print(sys.path)

from Dual_BNN_untrainable import BayesianDensityNetwork
import numpy as np



def run_model(array):

    num_features = 293
    feature_extractor_NN = [num_features, 256, 128]
    output_NN = [64, 32, 1]
    model = BayesianDensityNetwork(feature_extractor_NN, output_NN)

    model_path = '../weights/BNN2'
    model.load_weights(model_path)

    return np.array(model(array))[0]


if __name__ == "__main__":
    print("test....")
    print("input shape should be (1, 293)")
    array = np.random.rand(1, 293)
    print(run_model(array)[0])
