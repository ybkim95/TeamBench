"""DQN agent for the navigation environment."""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
import random


class QNetwork(nn.Module):
    def __init__(self, state_dim: int = 4, n_actions: int = 4,
                 hidden_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_actions),
        )

    def forward(self, x):
        return self.net(x)


class DQNAgent:
    def __init__(self, state_dim: int = 4, n_actions: int = 4,
                 hidden_dim: int = 128, lr: float = 0.001,
                 gamma: float = 0.95, buffer_size: int = 10000,
                 batch_size: int = 64, epsilon_start: float = 1.0,
                 epsilon_end: float = 0.05, epsilon_decay: int = 500):
        self.n_actions = n_actions
        self.gamma = gamma
        self.batch_size = batch_size
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.step_count = 0

        self.q_net = QNetwork(state_dim, n_actions, hidden_dim)
        self.target_net = QNetwork(state_dim, n_actions, hidden_dim)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.optimizer = optim.Adam(self.q_net.parameters(), lr=lr)
        self.buffer = deque(maxlen=buffer_size)

    def select_action(self, state: np.ndarray) -> int:
        self.epsilon = max(
            self.epsilon_end,
            self.epsilon_start if hasattr(self, "epsilon_start") else 1.0
        )
        # Decay epsilon
        eps = self.epsilon_end + (1.0 - self.epsilon_end) * np.exp(
            -self.step_count / self.epsilon_decay
        )
        self.step_count += 1
        if np.random.random() < eps:
            return np.random.randint(self.n_actions)
        with torch.no_grad():
            s = torch.FloatTensor(state).unsqueeze(0)
            return self.q_net(s).argmax(1).item()

    def store(self, s, a, r, s2, done):
        self.buffer.append((s, a, r, s2, done))

    def update(self):
        if len(self.buffer) < self.batch_size:
            return 0.0
        batch = random.sample(self.buffer, self.batch_size)
        s, a, r, s2, d = zip(*batch)
        s = torch.FloatTensor(np.array(s))
        a = torch.LongTensor(a).unsqueeze(1)
        r = torch.FloatTensor(r)
        s2 = torch.FloatTensor(np.array(s2))
        d = torch.FloatTensor(d)

        with torch.no_grad():
            target = r + self.gamma * self.target_net(s2).max(1)[0] * (1 - d)
        current = self.q_net(s).gather(1, a).squeeze(1)
        loss = nn.functional.mse_loss(current, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        return loss.item()

    def sync_target(self):
        self.target_net.load_state_dict(self.q_net.state_dict())
