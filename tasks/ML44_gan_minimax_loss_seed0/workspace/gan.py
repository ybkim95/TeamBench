"""GAN implementation — contains minimax loss saturation bug."""
import torch
import torch.nn as nn
import torch.optim as optim


class Generator(nn.Module):
    def __init__(self, latent_dim: int = 16, data_dim: int = 8,
                 hidden_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, data_dim),
        )

    def forward(self, z):
        return self.net(z)


class Discriminator(nn.Module):
    def __init__(self, data_dim: int = 8, hidden_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(data_dim, hidden_dim),
            nn.LeakyReLU(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LeakyReLU(0.2),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


class GAN:
    """GAN trainer.

    BUG: Generator uses original minimax loss log(1 - D(G(z))).
    When the discriminator is confident (D(G(z)) ≈ 0), this saturates:
      d/dG log(1 - D(G(z))) ≈ 0  (gradient vanishes)

    This causes the generator to stall early in training before learning
    a useful distribution.

    Correct fix: use non-saturating loss -log(D(G(z))).
    This provides strong gradients even when D is confident.
    """

    def __init__(self, latent_dim: int = 16, data_dim: int = 8,
                 hidden_dim: int = 64, lr_g: float = 0.0002,
                 lr_d: float = 0.0001):
        self.latent_dim = latent_dim
        self.G = Generator(latent_dim, data_dim, hidden_dim)
        self.D = Discriminator(data_dim, hidden_dim)
        self.opt_G = optim.Adam(self.G.parameters(), lr=lr_g, betas=(0.5, 0.999))
        self.opt_D = optim.Adam(self.D.parameters(), lr=lr_d, betas=(0.5, 0.999))

    def discriminator_loss(self, real: torch.Tensor, fake: torch.Tensor) -> torch.Tensor:
        """Standard discriminator loss."""
        d_real = self.D(real)
        d_fake = self.D(fake.detach())
        loss_real = -torch.log(d_real + 1e-8).mean()
        loss_fake = -torch.log(1 - d_fake + 1e-8).mean()
        return loss_real + loss_fake

    def generator_loss(self, fake: torch.Tensor) -> torch.Tensor:
        """Generator loss.

        BUG: Uses minimax formulation log(1 - D(G(z))).
        When D is confident (D(G(z)) ≈ 0), gradient ≈ 0 → training stalls.

        CORRECT: Use non-saturating loss -log(D(G(z))).
        """
        d_fake = self.D(fake)
        # BUG: minimax loss — saturates when d_fake → 0
        loss = torch.log(1 - d_fake + 1e-8).mean()
        # CORRECT would be:
        # loss = -torch.log(d_fake + 1e-8).mean()
        return loss

    def train_step(self, real: torch.Tensor, batch_size: int):
        z = torch.randn(batch_size, self.latent_dim)
        fake = self.G(z)

        # Update discriminator
        self.opt_D.zero_grad()
        d_loss = self.discriminator_loss(real, fake)
        d_loss.backward()
        self.opt_D.step()

        # Update generator
        z2 = torch.randn(batch_size, self.latent_dim)
        fake2 = self.G(z2)
        self.opt_G.zero_grad()
        g_loss = self.generator_loss(fake2)
        g_loss.backward()
        self.opt_G.step()

        return d_loss.item(), g_loss.item()

    def sample(self, n: int) -> torch.Tensor:
        with torch.no_grad():
            z = torch.randn(n, self.latent_dim)
            return self.G(z)
