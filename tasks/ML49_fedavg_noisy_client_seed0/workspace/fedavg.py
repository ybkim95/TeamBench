"""FedAvg server and client — contains noisy-large-client bias bug."""
import torch
import torch.nn as nn
import copy


class ClientModel(nn.Module):
    def __init__(self, input_dim: int = 16, hidden_dim: int = 64,
                 n_classes: int = 4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_classes),
        )

    def forward(self, x):
        return self.net(x)


class FedAvgClient:
    def __init__(self, model: ClientModel, client_id: int, lr: float = 0.01):
        self.model = copy.deepcopy(model)
        self.client_id = client_id
        self.lr = lr

    def local_train(self, X: torch.Tensor, y: torch.Tensor,
                    n_epochs: int = 5, batch_size: int = 32) -> dict:
        """Train locally and return updated state dict."""
        optimizer = torch.optim.SGD(self.model.parameters(), lr=self.lr)
        criterion = nn.CrossEntropyLoss()
        self.model.train()
        n = len(X)
        for _ in range(n_epochs):
            indices = torch.randperm(n)
            for i in range(0, n, batch_size):
                idx = indices[i:i + batch_size]
                optimizer.zero_grad()
                loss = criterion(self.model(X[idx]), y[idx])
                loss.backward()
                optimizer.step()
        return {k: v.clone() for k, v in self.model.state_dict().items()}


class FedAvgServer:
    """FedAvg aggregation server.

    BUG: Aggregation weights each client by its number of samples.
    When one client has many more samples (even if noisy/corrupted),
    it dominates the aggregated model.

    A large noisy client with 10x more samples gets 10x the weight,
    effectively overwriting the useful updates from other clients.

    Fix: use norm clipping on client updates before aggregation.
    Clip each client's update delta (new_params - global_params) to
    have L2 norm <= clip_norm. This limits any single client's influence.
    """

    def __init__(self, model: ClientModel, clip_norm: float = 2.0):
        self.global_model = model
        self.clip_norm = clip_norm

    def aggregate(self, client_updates: list, n_samples: list) -> None:
        """Aggregate client updates into global model.

        Args:
            client_updates: list of state dicts from clients
            n_samples: list of sample counts per client

        BUG: weights proportional to n_samples — noisy large client dominates.
        Fix: clip update deltas before aggregation.
        """
        global_state = self.global_model.state_dict()
        n_total = sum(n_samples)
        new_state = {k: torch.zeros_like(v) for k, v in global_state.items()}

        for update, n in zip(client_updates, n_samples):
            # BUG: weight proportional to sample count — large noisy client dominates
            weight = n / n_total
            # CORRECT: compute delta, clip it, then aggregate uniformly:
            # delta = {k: update[k] - global_state[k] for k in global_state}
            # total_norm = sum(d.norm()**2 for d in delta.values())**0.5
            # scale = min(1.0, self.clip_norm / (total_norm + 1e-8))
            # weight = 1.0 / len(client_updates)
            # for k: new_state[k] += weight * (global_state[k] + scale * delta[k])
            for k in global_state:
                new_state[k] += weight * update[k]

        self.global_model.load_state_dict(new_state)

    def distribute(self) -> ClientModel:
        """Return a copy of the global model for clients."""
        return copy.deepcopy(self.global_model)
