from utils.Dual_BNN_untrainable import BayesianDensityNetwork
import numpy as np
import os
from pathlib import Path

def run_model(array):
    try:
        num_features = 293
        feature_extractor_NN = [num_features, 256, 128]
        output_NN = [64, 32, 1]
        model = BayesianDensityNetwork(feature_extractor_NN, output_NN)

        # Get the absolute path to the weights file
        current_dir = Path(__file__).resolve().parent
        weights_path = current_dir.parent / 'weights' / 'BNN2'
        
        # Debug print
        print(f"Looking for weights at: {weights_path}")
        
        # Check if weights file exists
        # if not weights_path.exists():
        #     raise FileNotFoundError(f"Model weights not found at {weights_path}")

        model.load_weights(str(weights_path))  # Convert Path to string for TensorFlow

        # model_path = '../weights/BNN2'
        # model.load_weights(model_path)
        result = model(array)
        if result is None:
            raise ValueError("Model returned None")
        return np.array(result)[0]

    except Exception as e:
        print(f"Error running model: {str(e)}")
        return None

if __name__ == "__main__":
    print("test....")
    print("input shape should be (1, 293)")
    array = np.random.rand(1, 293)
    result = run_model(array)
    if result is not None:
        print(result)
