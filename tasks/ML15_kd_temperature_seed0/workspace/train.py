"""Knowledge distillation training — contains temperature asymmetry bug."""
import json, sys, os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def build_teacher():
    return nn.Sequential(
        nn.Linear(32, 128), nn.ReLU(),
        nn.Linear(128, 128), nn.ReLU(),
        nn.Linear(128, 128), nn.ReLU(),
        nn.Linear(128, 5)
    )


def build_student():
    return nn.Sequential(
        nn.Linear(32, 32), nn.ReLU(),
        nn.Linear(32, 5)
    )


def get_data():
    torch.manual_seed(42)
    X = torch.randn(997, 32)
    centers = torch.randn(5, 32)
    dists = torch.cdist(X, centers)
    y = dists.argmin(dim=1)
    n_train = int(997 * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def train_teacher(X_train, y_train):
    """Pre-train teacher model."""
    teacher = build_teacher()
    opt = optim.Adam(teacher.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    for epoch in range(30):
        teacher.train()
        indices = torch.randperm(len(X_train))
        for i in range(0, len(X_train), 64):
            idx = indices[i:i+64]
            opt.zero_grad()
            loss = criterion(teacher(X_train[idx]), y_train[idx])
            loss.backward()
            opt.step()
    teacher.eval()
    return teacher


def kd_loss(student_logits, teacher_logits, targets, T=4.0, alpha=0.9):
    """Knowledge distillation loss.

    BUG: Temperature not applied to student logits, and T^2 scaling missing.
    The teacher is divided by T but the student is not — asymmetric temperature.
    """
    # Teacher soft labels (correct — divided by T)
    teacher_probs = F.softmax(teacher_logits / T, dim=-1)

    # BUG: Student log-probs computed WITHOUT temperature division
    student_log_probs = F.log_softmax(student_logits, dim=-1)  # BUG: should be / T

    # BUG: Missing T^2 scaling factor
    kd = F.kl_div(student_log_probs, teacher_probs, reduction="batchmean")
    # kd = kd * (T * T)  # <-- missing T^2 scaling

    # Hard label loss
    ce = F.cross_entropy(student_logits, targets)
    return alpha * kd + (1 - alpha) * ce


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()

    print("Pre-training teacher...")
    teacher = train_teacher(X_train, y_train)
    with torch.no_grad():
        teacher_acc = (teacher(X_val).argmax(1) == y_val).float().mean().item()
    print(f"Teacher val acc: {teacher_acc:.4f}")

    student = build_student()
    optimizer = optim.Adam(student.parameters(), lr=1e-3)

    n_train = len(X_train)
    history = []
    for epoch in range(38):
        student.train()
        teacher.eval()
        epoch_loss = 0.0
        indices = torch.randperm(n_train)
        for i in range(0, n_train, 32):
            idx = indices[i:i + 32]
            xb, yb = X_train[idx], y_train[idx]
            optimizer.zero_grad()
            with torch.no_grad():
                t_logits = teacher(xb)
            s_logits = student(xb)
            loss = kd_loss(s_logits, t_logits, yb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
        epoch_loss /= n_train

        student.eval()
        with torch.no_grad():
            val_acc = (student(X_val).argmax(1) == y_val).float().mean().item()

        history.append({"epoch": epoch+1, "loss": epoch_loss, "val_acc": val_acc})
        if (epoch+1) % 5 == 0:
            print(f"Epoch {epoch+1}/{38} loss={epoch_loss:.4f} val_acc={val_acc:.4f}")

    results = {
        "final_val_acc": history[-1]["val_acc"],
        "teacher_val_acc": teacher_acc,
        "converged": history[-1]["val_acc"] > 0.65,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final student val acc: {results['final_val_acc']:.4f}")
    return results


if __name__ == "__main__":
    train()
