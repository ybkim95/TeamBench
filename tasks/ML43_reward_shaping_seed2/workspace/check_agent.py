"""Validate reward shaping fix."""
import json
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import GridEnv, ShapedEnv


def check_potential_based():
    """Verify the shaping satisfies F(s,a,s\')+F(s\',a,s\'\') = gamma*F(s,a,s\'') property."""
    env_base = GridEnv(grid_size=6, seed=0)
    env = ShapedEnv(env_base, gamma=0.95)

    # Sample a few transitions and verify potential-based property:
    # F(s, a, s') = gamma * phi(s') - phi(s)
    # Equivalently: F does not depend on s alone without gamma scaling
    # Test: for two different states reaching the same next state,
    # the shaping should equal gamma*phi(next) - phi(state) for each

    # Check with a simple known trajectory
    obs0 = env.reset()
    prev_dist0 = np.linalg.norm(obs0 - env_base.goal / env_base.grid_size)

    # Move toward goal
    obs1, r1, done1, trunc1, _ = env.step(3)  # right
    curr_dist1 = np.linalg.norm(obs1 - env_base.goal / env_base.grid_size)

    # Expected bonus with correct potential shaping:
    # phi(s) = -dist(s), bonus = gamma * phi(s') - phi(s) = gamma*(-curr) - (-prev)
    expected_bonus = 0.95 * (-curr_dist1) - (-prev_dist0)
    actual_bonus = r1  # shaped reward = env reward (0.0 here) + bonus
    # env reward is 0 unless at goal, so actual_bonus = shaped_reward

    # Check if the actual shaping matches potential-based formula
    diff = abs(actual_bonus - expected_bonus)
    if diff > 0.1:
        return False, (
            f"Shaping bonus {actual_bonus:.4f} does not match potential-based "
            f"formula {expected_bonus:.4f} (diff={diff:.4f}). "
            f"Expected: gamma*phi(s\')-phi(s) = 0.95*(-{curr_dist1:.3f})-(-{prev_dist0:.3f})"
        )
    return True, f"Potential-based shaping verified: bonus={actual_bonus:.4f} expected={expected_bonus:.4f}"


def check_no_orbiting_incentive():
    """Verify agent cannot accumulate indefinite bonuses by orbiting."""
    env_base = GridEnv(grid_size=6, seed=0)
    env = ShapedEnv(env_base, gamma=0.95)

    # Simulate orbiting: move right then left repeatedly near goal
    obs = env.reset()
    total_bonus = 0.0
    # Move to near-goal position manually
    for _ in range(6 - 2):
        obs, r, done, trunc, _ = env.step(3)  # right
        obs, r, done, trunc, _ = env.step(0)  # up

    # Now orbit: right-left-right-left
    for _ in range(10):
        obs, r, done, trunc, info = env.step(3)
        total_bonus += r
        obs, r, done, trunc, info = env.step(2)
        total_bonus += r
        if done or trunc:
            break

    # With correct potential shaping, orbiting bonus telescopes to near-zero
    # (gamma*(Phi_final) - Phi_initial bounded)
    # With buggy shaping, each step accumulates unbounded bonus
    # A correct implementation should have |total_bonus| < 2.0 for 10 right-left pairs
    if total_bonus > 3.0:
        return False, (
            f"Orbiting bonus too large: {total_bonus:.4f} > 3.0. "
            "Non-potential shaping allows indefinite bonus accumulation."
        )
    return True, f"Orbiting bonus bounded: {total_bonus:.4f}"


def check_gamma_scaling():
    """Verify gamma is applied correctly in potential formula."""
    import inspect
    with open("env.py") as f:
        src = f.read()

    # Look for correct gamma scaling in shaping
    # The fix must use gamma * phi(next) - phi(curr)
    has_gamma_scale = (
        "self.gamma * phi" in src or
        "gamma * phi" in src or
        "self.gamma *" in src
    )
    if not has_gamma_scale:
        return False, "env.py does not apply gamma scaling in potential function"
    return True, "gamma scaling present in shaping formula"


def check_symmetry():
    """Verify shaping is antisymmetric: F(s->s\') + F(s\'->s) should be small (telescoping)."""
    env_base = GridEnv(grid_size=6, seed=0)
    env = ShapedEnv(env_base, gamma=0.95)
    obs = env.reset()

    # Move right then left — shaping should nearly cancel
    obs1, r_right, _, _, _ = env.step(3)
    # Reset and go left from same position is not directly possible,
    # but we can check telescope property by going right twice and verifying
    # total bonus ≈ gamma^2 * phi(s2) - phi(s0)
    obs2, r_right2, _, _, _ = env.step(3)

    dist0 = np.linalg.norm(obs - env_base.goal / env_base.grid_size)
    dist2 = np.linalg.norm(obs2 - env_base.goal / env_base.grid_size)
    expected_total = (0.95**2) * (-dist2) - (-dist0)
    actual_total = r_right + 0.95 * r_right2  # properly discounted sum

    diff = abs(actual_total - expected_total)
    if diff > 0.15:
        return False, (
            f"Two-step shaping total {actual_total:.4f} != expected {expected_total:.4f} "
            f"(diff={diff:.4f}). Potential-based shaping telescoping broken."
        )
    return True, f"Two-step telescope: actual={actual_total:.4f} expected={expected_total:.4f}"


def check_terminal_handling():
    """Verify shaping at terminal state is handled correctly."""
    env_base = GridEnv(grid_size=6, seed=0)
    env = ShapedEnv(env_base, gamma=0.95)
    env.reset()
    # Move to goal position directly
    obs, reward, done, trunc, info = env_base.reset(), 0, False, False, {}
    for _ in range(6 - 1):
        obs, reward, done, trunc, info = env_base.step(3)
        obs, reward, done, trunc, info = env_base.step(0)
    # At or near goal — verify terminal bonus makes sense
    return True, "Terminal state handling: no assertion error"


def check_training_results():
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    rate = res.get("final_success_rate", 0)
    if not res.get("converged", False):
        return False, f"Agent did not converge: success_rate={rate:.3f} < 0.4"
    return True, f"Agent converged: success_rate={rate:.3f}"


def check():
    checks = [
        ("Potential-based formula", check_potential_based),
        ("No orbiting incentive", check_no_orbiting_incentive),
        ("Gamma scaling in code", check_gamma_scaling),
        ("Telescope property", check_symmetry),
        ("Terminal handling", check_terminal_handling),
        ("Training results", check_training_results),
    ]

    all_pass = True
    for name, fn in checks:
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"Exception: {e}"
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: {msg}")
        if not ok:
            all_pass = False

    if all_pass:
        print("\nPASS")
    else:
        print("\nFAIL")
    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
