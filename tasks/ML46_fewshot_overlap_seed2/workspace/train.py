"""Train prototypical network with episodic training."""
import json
import sys
import os
import torch
import torch.optim as optim
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from episode_sampler import EpisodeSampler
from model import ProtoNet


def make_dataset(n_classes: int = 15, n_per_class: int = 30,
                 input_dim: int = 24):
    torch.manual_seed(42)
    centers = torch.randn(n_classes, input_dim) * 3.0
    class_data = {}
    for c in range(n_classes):
        class_data[c] = centers[c] + 0.5 * torch.randn(n_per_class, input_dim)
    return class_data


def train():
    torch.manual_seed(0)
    np.random.seed(0)

    class_data = make_dataset()
    sampler = EpisodeSampler(n_way=3, k_shot=1, n_query=5)
    model = ProtoNet(input_dim=24, hidden_dim=48)
    optimizer = optim.Adam(model.parameters(), lr=0.0005)

    train_history = []
    for ep in range(828):
        model.train()
        episode = sampler.sample_episode(class_data)
        loss, acc = model.episode_loss(
            episode["support"], episode["support_labels"],
            episode["query"], episode["query_labels"],
            n_way=3
        )
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if (ep + 1) % 200 == 0:
            train_history.append({"episode": ep+1, "loss": loss.item(), "acc": acc})
            print(f"Ep {ep+1}/{828} loss={loss.item():.4f} train_acc={acc:.4f}")

    # Evaluate on test episodes with FRESH random seeds (different from train)
    model.eval()
    np.random.seed(99)
    torch.manual_seed(99)
    test_accs = []
    for _ in range(223):
        with torch.no_grad():
            episode = sampler.sample_episode(class_data)
            _, acc = model.episode_loss(
                episode["support"], episode["support_labels"],
                episode["query"], episode["query_labels"],
                n_way=3
            )
            test_accs.append(acc)

    test_acc = np.mean(test_accs)
    results = {
        "final_test_acc": test_acc,
        "converged": test_acc > 0.4,
        "train_history": train_history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Test acc: {test_acc:.4f}")
    return results


if __name__ == "__main__":
    train()
