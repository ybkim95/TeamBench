"""Validate cross-attention Q/K/V fix."""
import json
import sys
import os
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cross_attention import CrossAttention


def check_cross_attn_sources():
    """Verify Q comes from decoder, K/V from encoder."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cross_attention.py')) as f:
        src = f.read()

    # Find CrossAttention.forward
    # Check that q_proj is applied to first arg (decoder_hidden) not second (encoder_output)
    # Heuristic: look for "q_proj(decoder" or "q_proj(enc" in wrong position
    import re
    # Extract forward method lines
    lines = src.split('\n')
    in_forward = False
    forward_lines = []
    for line in lines:
        if 'def forward' in line and 'decoder_hidden' in line:
            in_forward = True
        if in_forward:
            forward_lines.append(line)
            if line.strip().startswith('return') and in_forward and len(forward_lines) > 2:
                break

    forward_src = '\n'.join(forward_lines)

    # Check: q_proj should take decoder_hidden (1st arg), k/v_proj should take encoder_output (2nd arg)
    # Buggy: q_proj(encoder_output), k_proj(decoder_hidden)
    q_from_encoder = bool(re.search(r'q_proj\s*\(\s*encoder_output', forward_src))
    k_from_decoder = bool(re.search(r'k_proj\s*\(\s*decoder_hidden', forward_src))
    if q_from_encoder or k_from_decoder:
        return False, f"Q/K/V still swapped: q_from_encoder={q_from_encoder}, k_from_decoder={k_from_decoder}"

    # Check correct assignment
    q_from_decoder = bool(re.search(r'q_proj\s*\(\s*decoder_hidden', forward_src))
    k_from_encoder = bool(re.search(r'k_proj\s*\(\s*encoder_output', forward_src))
    if not (q_from_decoder and k_from_encoder):
        return False, "Q from decoder + K/V from encoder pattern not found"

    return True, "Q from decoder, K/V from encoder — correct"


def check_output_shape():
    """Cross-attention output should have tgt_len shape, not src_len."""
    attn = CrossAttention(embed_dim=64, num_heads=4)
    attn.eval()
    with torch.no_grad():
        dec_hidden = torch.randn(2, 8, 64)
        enc_out = torch.randn(2, 20, 64)
        out = attn(dec_hidden, enc_out)
    # Correct: output matches decoder (tgt_len), not encoder (src_len)
    if out.shape[1] != 8:
        return False, f"Output seq len {out.shape[1]} != tgt_len=8"
    return True, f"Output shape {list(out.shape)} correct (tgt_len=8)"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    print(f"Final val acc: {acc:.4f}")

    ok, msg = check_cross_attn_sources()
    print(f"Cross-attn sources: {msg}")
    if not ok:
        print("FAIL: Cross-attention Q/K/V not fixed")
        return False

    ok2, msg2 = check_output_shape()
    print(f"Output shape: {msg2}")
    if not ok2:
        print("FAIL: Cross-attention output shape wrong")
        return False

    if not res.get("converged", False):
        print(f"FAIL: Did not converge (acc={acc:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
