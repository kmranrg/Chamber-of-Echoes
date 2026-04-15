import numpy as np


class ReservoirComputer:
    def __init__(self, input_dim, output_dim=4, res_size=400, alpha=0.3, spectral_radius=0.95):
        self.input_dim = input_dim
        self.res_size = res_size
        self.alpha = alpha
        self.output_dim = output_dim

        self.W_in = np.random.uniform(-0.5, 0.5, (self.res_size, self.input_dim))

        W_raw = np.random.uniform(-0.5, 0.5, (self.res_size, self.res_size))
        eigenvalues = np.linalg.eigvals(W_raw)
        max_eig = np.max(np.abs(eigenvalues))
        self.W = W_raw * (spectral_radius / max_eig)

        self.W_out = np.zeros((self.output_dim, self.res_size))

    def _get_final_state(self, sequence):
        """Processes a sequence of audio features through the reservoir over time."""
        x = np.zeros(self.res_size)     # initial state
        all_states = []                 # keep track of states over time
        for u in sequence:
            x = (1 - self.alpha) * x + self.alpha * np.tanh(np.dot(self.W_in, u) + np.dot(self.W, x))
            all_states.append(x)
        # returing the average of state across all timesteps, not just the last one!
        return np.mean(all_states, axis=0)
    
    def train(self, X_train, Y_train, beta=1e-4):
        """
        Trains W_out using Ridge Regression.
        X_train: list of MFCC sequences
        Y_tain: list of one-hot encoded labels
        """
        print(f"Training RC on {len(X_train)} samples.")

        states = np.array([self._get_final_state(seq) for seq in X_train])
        R = states.T
        Y_true = np.array(Y_train).T

        identity = np.eye(self.res_size)
        R_Rt = np.dot(R, R.T)
        inv_part = np.linalg.inv(R_Rt + beta * identity)

        self.W_out = np.dot(np.dot(Y_true, R.T), inv_part)
        print("Traning complete! Optimal W_out computed.")

    def predict(self, sequence):
        """Runs an audio sequence through the network and returns the predicted label index."""
        x = self._get_final_state(sequence)
        y_pred = np.dot(self.W_out, x)
        return np.argmax(y_pred)    # returns index: 0, 1, 2, or 3