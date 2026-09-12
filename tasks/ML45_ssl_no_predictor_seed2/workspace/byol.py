"""BYOL-style SSL — contains missing predictor MLP bug."""
import torch
import torch.nn as nn
import copy


class Encoder(nn.Module):
    def __init__(self, input_dim: int = 24, hidden_dim: int = 96,
                 proj_dim: int = 48):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
        )
        self.projector = nn.Sequential(
            nn.Linear(hidden_dim, proj_dim),
            nn.BatchNorm1d(proj_dim),
            nn.ReLU(),
            nn.Linear(proj_dim, proj_dim),
        )

    def forward(self, x):
        h = self.backbone(x)
        z = self.projector(h)
        return h, z


class Predictor(nn.Module):
    """Predictor MLP applied only on the online network."""
    def __init__(self, proj_dim: int = 48, pred_dim: int = 24):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(proj_dim, pred_dim),
            nn.BatchNorm1d(pred_dim),
            nn.ReLU(),
            nn.Linear(pred_dim, proj_dim),
        )

    def forward(self, z):
        return self.net(z)


class BYOL:
    """Bootstrap Your Own Latent (BYOL) SSL trainer.

    BUG: The online network is missing the predictor MLP.
    Without the predictor, the BYOL loss has a trivial solution:
    both online and target networks collapse to constant outputs.

    The predictor breaks the symmetry by giving the online network
    an asymmetric pathway that must "predict" the target projection.
    Without it, there is no incentive to avoid collapsed representations.

    Fix: apply the predictor to the online projections before computing loss.
    """

    def __init__(self, input_dim: int = 24, hidden_dim: int = 96,
                 proj_dim: int = 48, pred_dim: int = 24,
                 ema_decay: float = 0.99):
        self.ema_decay = ema_decay

        self.online = Encoder(input_dim, hidden_dim, proj_dim)
        self.target = copy.deepcopy(self.online)
        self.predictor = Predictor(proj_dim, pred_dim)

        # Freeze target network (updated via EMA only)
        for p in self.target.parameters():
            p.requires_grad_(False)

    def _ema_update(self):
        for o_param, t_param in zip(self.online.parameters(), self.target.parameters()):
            t_param.data = self.ema_decay * t_param.data + (1 - self.ema_decay) * o_param.data

    def loss(self, x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
        """BYOL loss.

        BUG: online_z is used directly without the predictor.
        This means both online and target have the same architecture,
        and the trivial solution (constant output) satisfies the loss.

        CORRECT: apply self.predictor to online_z before computing similarity.
        """
        # Online network (should apply predictor)
        _, online_z1 = self.online(x1)
        _, online_z2 = self.online(x2)

        # BUG: predictor not applied — collapses
        pred_z1 = online_z1   # should be: self.predictor(online_z1)
        pred_z2 = online_z2   # should be: self.predictor(online_z2)

        # Target network (no predictor, no grad)
        with torch.no_grad():
            _, target_z1 = self.target(x1)
            _, target_z2 = self.target(x2)

        # Normalize
        pred_z1 = nn.functional.normalize(pred_z1, dim=-1)
        pred_z2 = nn.functional.normalize(pred_z2, dim=-1)
        target_z1 = nn.functional.normalize(target_z1, dim=-1)
        target_z2 = nn.functional.normalize(target_z2, dim=-1)

        # Symmetric loss
        loss = (
            2 - 2 * (pred_z1 * target_z2.detach()).sum(dim=-1).mean() +
            2 - 2 * (pred_z2 * target_z1.detach()).sum(dim=-1).mean()
        ) / 2
        return loss

    def update(self, x1: torch.Tensor, x2: torch.Tensor,
               optimizer: torch.optim.Optimizer) -> float:
        optimizer.zero_grad()
        loss = self.loss(x1, x2)
        loss.backward()
        optimizer.step()
        self._ema_update()
        return loss.item()

    def get_representation(self, x: torch.Tensor) -> torch.Tensor:
        """Get backbone representations for downstream evaluation."""
        self.online.eval()
        with torch.no_grad():
            h, _ = self.online(x)
        return h
