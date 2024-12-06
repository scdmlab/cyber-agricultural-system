import numpy as np
from sklearn.metrics import mean_absolute_error, make_scorer, mean_squared_error
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import pandas as pd

import tensorflow as tf
import tensorflow_probability as tfp

tfd = tfp.distributions
#from tensorflow_probability.random import rademacher
from tensorflow import keras
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, BatchNormalization
from tensorflow.keras.layers import ReLU, Dropout
from tensorflow.keras.optimizers import Adam
from numpy.random import seed
from utils.file_organize import model_prediction, evaluate_regression_results


# Xavier initializer
def xavier(shape):
    return tf.random.truncated_normal(shape,
                                      mean=0.0,
                                      stddev=np.sqrt(2 / sum(shape)))


class BayesianDenseLayer(tf.keras.Model):
    """A fully-connected Bayesian neural network layer

    Parameters
    ----------
    d_in : int
        Dimensionality of the input (# input features)
    d_out : int
        Output dimensionality (# units in the layer)
    name : str
        Name for the layer

    Attributes
    ----------
    losses : tensorflow.Tensor
        Sum of the Kullback–Leibler divergences between
        the posterior distributions and their priors

    Methods
    -------
    call : tensorflow.Tensor
        Perform the forward pass of the data through
        the layer
    """

    def __init__(self, d_in, d_out, name):

        super(BayesianDenseLayer, self).__init__(name=name)
        self.d_in = d_in
        self.d_out = d_out

        self.w_loc = tf.Variable(xavier([d_in, d_out]), name=name + '_w_loc')
        self.w_std = tf.Variable(xavier([d_in, d_out]) - 6.0,
                                 name=name + '_w_std')
        self.b_loc = tf.Variable(xavier([1, d_out]), name=name + '_b_loc')
        self.b_std = tf.Variable(xavier([1, d_out]) - 6.0,
                                 name=name + '_b_std')

    def call(self, x, sampling=True):
        """Perform the forward pass"""

        if sampling:

            # Flipout-estimated weight samples
            s = tfp.random.rademacher(tf.shape(x))
            r = tfp.random.rademacher([x.shape[0], self.d_out])
            w_samples = tf.nn.softplus(self.w_std) * tf.random.normal(
                [self.d_in, self.d_out])
            w_perturbations = r * tf.matmul(x * s, w_samples)
            w_outputs = tf.matmul(x, self.w_loc) + w_perturbations

            # Flipout-estimated bias samples
            r = tfp.random.rademacher([x.shape[0], self.d_out])
            b_samples = tf.nn.softplus(self.b_std) * tf.random.normal(
                [self.d_out])
            b_outputs = self.b_loc + r * b_samples

            return w_outputs + b_outputs

        else:
            return x @ self.w_loc + self.b_loc

    @property
    def losses(self):
        """Sum of the KL divergences between priors + posteriors"""
        weight = tfd.Normal(self.w_loc, tf.nn.softplus(self.w_std))
        bias = tfd.Normal(self.b_loc, tf.nn.softplus(self.b_std))
        prior = tfd.Normal(0, 1)
        return (tf.reduce_sum(tfd.kl_divergence(weight, prior)) +
                tf.reduce_sum(tfd.kl_divergence(bias, prior)))


class BayesianDenseNetwork(tf.keras.Model):
    """A multilayer fully-connected Bayesian neural network

    Parameters
    ----------
    dims : List[int]
        List of units in each layer
    name : str
        Name for the network

    Attributes
    ----------
    losses : tensorflow.Tensor
        Sum of the Kullback–Leibler divergences between
        the posterior distributions and their priors,
        over all layers in the network

    Methods
    -------
    call : tensorflow.Tensor
        Perform the forward pass of the data through
        the network
    """

    def __init__(self, dims, name):

        super(BayesianDenseNetwork, self).__init__(name=name)

        self.steps = []
        self.acts = []
        for i in range(len(dims) - 1):
            layer_name = name + '_Layer_' + str(i)
            self.steps += [
                BayesianDenseLayer(dims[i], dims[i + 1], name=layer_name)
            ]
            self.acts += [tf.nn.relu]

        self.acts[-1] = lambda x: x

    def call(self, x, sampling=True):
        """Perform the forward pass"""

        for i in range(len(self.steps)):
            x = self.steps[i](x, sampling=sampling)
            x = self.acts[i](x)

        return x

    @property
    def losses(self):
        """Sum of the KL divergences between priors + posteriors"""
        return tf.reduce_sum([s.losses for s in self.steps])


class BayesianDensityNetwork(tf.keras.Model):
    """Multilayer fully-connected Bayesian neural network, with
    two heads to predict both the mean and the standard deviation.

    Parameters
    ----------
    units : List[int]
        Number of output dimensions for each layer
        in the core network.
    units : List[int]
        Number of output dimensions for each layer
        in the head networks.
    name : None or str
        Name for the layer
    """

    def __init__(self, units, head_units, name=None):
        # Initialize
        super(BayesianDensityNetwork, self).__init__(name=name)

        # Create sub-networks
        self.core_net = BayesianDenseNetwork(units, 'core')
        self.loc_net = BayesianDenseNetwork([units[-1]] + head_units, 'loc')
        self.std_net = BayesianDenseNetwork([units[-1]] + head_units, 'std')

    def call(self, x, sampling=True):
        """Pass data through the model

        Parameters
        ----------
        x : tf.Tensor
            Input data
        sampling : bool
            Whether to sample parameter values from their
            variational distributions (if True, the default), or
            just use the Maximum a Posteriori parameter value
            estimates (if False).

        Returns
        -------
        preds : tf.Tensor of shape (Nsamples, 2)
            Output of this model, the predictions.  First column is
            the mean predictions, and second column is the standard
            deviation predictions.
        """

        # Pass data through core network
        x = self.core_net(x, sampling=sampling)
        x = tf.nn.relu(x)

        # Make predictions with each head network
        loc_preds = self.loc_net(x, sampling=sampling)
        std_preds = self.std_net(x, sampling=sampling)
        std_preds = tf.nn.softplus(std_preds)

        # Return mean and std predictions
        return tf.concat([loc_preds, std_preds], 1)

    def log_likelihood(self, x, y, sampling=True):
        """Compute the log likelihood of y given x"""

        # Compute mean and std predictions
        preds = self.call(x, sampling=sampling)

        # Return log likelihood of true data given predictions
        return tfd.Normal(preds[:, 0], preds[:, 1]).log_prob(y[:, 0])

    @tf.function
    def sample(self, x):
        """Draw one sample from the predictive distribution"""
        preds = self.call(x)
        return tfd.Normal(preds[:, 0], preds[:, 1]).sample()

    def samples(self, x, n_samples=10):
        """Draw multiple samples from predictive distributions"""
        samples = np.zeros((x.shape[0], n_samples))
        for i in range(n_samples):
            samples[:, i] = self.sample(x)
        return samples

    @property
    def losses(self):
        """Sum of the KL divergences between priors + posteriors"""
        return (self.core_net.losses + self.loc_net.losses +
                self.std_net.losses)


def train_Dual_BNN(feature_extractor_NN, output_NN, N, data_train, data_val,
                   BATCH_SIZE, EPOCHS, L_RATE):
    # feature_extractor_NN: the feature extracion network
    # output_NN: the yield prediction net and the uncertainty net
    # N: the number of samples
    # data_train: the data used for training
    # data_val: the data used for evaluation
    # BATCH_SIZE: the batch size
    # EPOCHS: the total number of epochs
    # L_RATE: the learning rate

    # Define the model
    model = BayesianDensityNetwork(feature_extractor_NN, output_NN)

    # Use the Adam optimizer
    lr_schedule = tf.keras.optimizers.schedules.ExponentialDecay(
        initial_learning_rate=L_RATE, decay_steps=2000, decay_rate=0.8)
    optimizer = tf.keras.optimizers.Adam(learning_rate=lr_schedule)
    optimizer = tf.keras.optimizers.Adam(learning_rate=L_RATE, clipvalue=0.5)

    @tf.function
    def train_step(x_data, y_data):
        with tf.GradientTape() as tape:
            log_likelihoods = model.log_likelihood(x_data, y_data)
            kl_loss = model.losses
            elbo_loss = kl_loss / N - tf.reduce_mean(log_likelihoods)

        gradients = tape.gradient(elbo_loss, model.trainable_variables)
        print("Number of trainable variables:", len(model.trainable_variables))
        optimizer.apply_gradients(zip(gradients, model.trainable_variables))
        return elbo_loss

    # Fit the model
    elbo = np.zeros(EPOCHS)
    mae1 = np.zeros(EPOCHS)

    for epoch in range(EPOCHS):
        for x_data, y_data in data_train:
            elbo[epoch] = train_step(x_data, y_data)

        # Evaluate performance on validation data
        for x_data, y_data in data_val:
            y_pred = model(x_data, sampling=False)[:, 0]
            mae1[epoch] = mean_absolute_error(y_pred, y_data)

    return model


def retrain_Dual_BNN(model, N, data_train, data_val, save_image_path,
                     BATCH_SIZE, EPOCHS, L_RATE):
    print("make the layer untrainable!!!")

    # Use the Adam optimizer
    optimizer = tf.keras.optimizers.Adam(lr=L_RATE, clipvalue=0.5)

    @tf.function
    def train_step(x_data, y_data):
        with tf.GradientTape() as tape:
            log_likelihoods = model.log_likelihood(x_data, y_data)
            kl_loss = model.losses
            elbo_loss = kl_loss / N - tf.reduce_mean(log_likelihoods)
        # Only train the layers not shared with loc and std:
        print("Number of trainable variables:", len(model.trainable_variables))
        t_vars = model.trainable_variables
        print(t_vars)
        train_vars = [
            var for var in t_vars
            if var.name.startswith('loc') or var.name.startswith('std')
        ]

        gradients = tape.gradient(elbo_loss, train_vars)
        optimizer.apply_gradients(zip(gradients, train_vars))
        return elbo_loss

    # Fit the model
    elbo = np.zeros(EPOCHS)
    mae1 = np.zeros(EPOCHS)

    for epoch in range(EPOCHS):
        for x_data, y_data in data_train:
            elbo[epoch] = train_step(x_data, y_data)

        # Evaluate performance on validation data
        for x_data, y_data in data_val:
            y_pred = model(x_data, sampling=False)[:, 0]
            mae1[epoch] = mean_absolute_error(y_pred, y_data)

    # Plot the ELBO loss
    save_image_path1 = save_image_path + '_ELBO.png'
    plt.figure(1)
    plt.plot(elbo)
    plt.xlabel('Epoch')
    plt.ylabel('ELBO Loss')
    plt.title('ELBO loss')
    plt.savefig(save_image_path1)

    # Plot validation error over training
    # Plot the ELBO loss
    target_name = 'ELBO Loss'
    plot_and_save(elbo, target_name, save_image_path)

    # Plot validation error over training
    target_name = 'validation MAE over source domain'
    plot_and_save(mae1, target_name, save_image_path)

    return model


# prediction
def Dual_BNN_model_prediction(model, x_test):
    y_pred = model(x_test, sampling=False)[:, 0]
    y_var = model(x_test, sampling=False)[:, 1]
    return y_pred, y_var


# Markov sampling
def MS_BNN_model_prediction(model, x_test):
    y_pred_list = []
    y_std_list = []

    for i in range(100):
        y = model(x_test, sampling=True)

        y_pred = y[:, 0]
        y_pred = tf.expand_dims(y_pred, 1)

        y_std = y[:, 1]
        y_std = tf.expand_dims(y_std, 1)

        y_pred_list.append(y_pred)
        y_std_list.append(y_std)

    y_preds = np.concatenate(y_pred_list, axis=1)
    y_stds = np.concatenate(y_std_list, axis=1)

    y_pred_mean = np.mean(y_preds, axis=1)
    y_pred_sigma = np.std(y_preds, axis=1, ddof=1)

    y_std_mean = np.mean(y_stds, axis=1)
    y_std_sigma = np.std(y_stds, axis=1, ddof=1)

    return y_pred_mean, y_pred_sigma, y_std_mean, y_std_sigma


def save_uncertainty(uncertainty_filename, y_test_pred_var_source_domain,
                     y_test_pred_var_target_domain):
    f_s = open(uncertainty_filename, "a+")
    f_s.write('Sigma on source domain test data:/n')
    f_s.write(str(y_test_pred_var_source_domain))
    f_s.write('/n')
    f_s.write('Sigma on target domain test data:/n')
    f_s.write(str(y_test_pred_var_target_domain))
    f_s.close()


def train_BNN2(current_years,
               num_years,
               x_train,
               y_train,
               x_test,
               y_test,
               BATCH_SIZE,
               EPOCHS,
               L_RATE,
               dropnum=9):

    # current_years: all training and testing years
    # num_years: the number of testing years
    # x_train, y_train, x_test, y_test: Training and testing data
    # BATCH_SIZE: the batch size
    # EPOCHS: the total number of epochs
    # L_RATE: the learning rate
    # dropnum: it defines the time window of yield prediction. When it is 9, it means keeping all features and made the yield prediction on Oct 4th. When it is 0, it means that we drop the features on the last 9 observation dates and make yield prediction on May 13rd.
    experiment_years = current_years[0:num_years]

    # Organize the training data
    # Make a TensorFlow Dataset from training data
    data_train = tf.data.Dataset.from_tensor_slices(
        (x_train, y_train)).shuffle(10000).batch(BATCH_SIZE)

    data_test = tf.data.Dataset.from_tensor_slices(
        (x_test, y_test)).batch(x_test.shape[0])

    # Train
    N_source = x_train.shape[0]
    num_features = x_test.shape[1]
    feature_extractor_NN = [num_features, 256, 128]
    output_NN = [64, 32, 1]

    model_trained = train_Dual_BNN(feature_extractor_NN, output_NN, N_source,
                                   data_train, data_test, BATCH_SIZE, EPOCHS,
                                   L_RATE)

    # evaluation
    y_train_pred, y_train_pred_uncertainty = Dual_BNN_model_prediction(
        model_trained, x_train)
    y_test_pred, y_test_pred_uncertainty = Dual_BNN_model_prediction(
        model_trained, x_test)

    print("Evaluation on training set: ")
    RMSE_train, R2_train, MAPE_train = evaluate_regression_results(
        y_train,
        tf.expand_dims(y_train_pred, 1).numpy())
    print("Evaluation on test set: ")
    RMSE_test, R2_test, MAPE_test = evaluate_regression_results(
        y_test,
        tf.expand_dims(y_test_pred, 1).numpy())
    print("__________________________________")

    return model_trained, y_train_pred, y_test_pred


def load_BNN(num_features, save_model_path):
    # Load the pretrained model
    #save_model_path = '_transfer_result/model/BNN2_weights_' + str(experiment_years[-1]) + '.h5'
    model_before = BayesianDensityNetwork([num_features, 256, 128],
                                          [64, 32, 1])
    model_before.load_weights(save_model_path)

    return model_before


def predict_T(model, x_i, y_i, T=10):

    # predict stochastic dropout model T times
    p_hat = []
    p_hat_std = []
    for t in range(T):
        pred_t = model(x_i, sampling=True)
        p_hat.append(pred_t[0, 0])
        p_hat_std.append(pred_t[0, 1])
    p_hat = np.array(p_hat)
    p_hat_std = np.array(p_hat_std)

    # mean prediction
    prediction = np.mean(p_hat, axis=0)
    prediction_std = np.mean(p_hat_std, axis=0)
    # threshold mean prediction
    #prediction = np.where(prediction > 0.5, 1, 0)

    # estimate uncertainties (eq. 4 )
    # eq.4 in https://openreview.net/pdf?id=Sk_P2Q9sG
    # see https://github.com/ykwon0407/UQ_BNN/issues/1
    aleatoric = np.mean(p_hat * (1 - p_hat), axis=0)
    epistemic = np.mean(p_hat**2, axis=0) - np.mean(p_hat, axis=0)**2
    error = prediction - y_i

    return np.squeeze(prediction), np.squeeze(aleatoric), np.squeeze(
        epistemic), prediction_std, error
