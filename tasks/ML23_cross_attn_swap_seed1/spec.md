# ML23: Cross-Attention Q/K/V Sources Swapped

## Goal
Fix `cross_attention.py` so cross-attention uses Q from decoder and K/V from encoder.
Run `python train.py` then `python check_cross_attn.py` — both must pass.

## Task
Training a **encoder-decoder translation model** for sequence-to-sequence learning.
Model must achieve >0.40 validation accuracy on token prediction.

---

## The Bug: Encoder/Decoder Sources Reversed in Cross-Attention

**Location**: `CrossAttention.forward()` in `cross_attention.py`

### Background: Cross-Attention in Encoder-Decoder

In cross-attention (decoder attending to encoder):
- **Q** (queries): from **decoder** — "what information do I need?"
- **K** (keys): from **encoder** — "what information is available?"
- **V** (values): from **encoder** — "here is the actual information"

The decoder queries the encoder's key-value store.

### Current (Buggy) Code

```python
def forward(self, decoder_hidden, encoder_output):
    # BUG: sources are reversed
    q = self.q_proj(encoder_output)    # Q from encoder  — WRONG
    k = self.k_proj(decoder_hidden)    # K from decoder  — WRONG
    v = self.v_proj(decoder_hidden)    # V from decoder  — WRONG
```

**Consequences**:
1. Output shape becomes `(B, src_len=16, embed_dim)` not `(B, tgt_len=10, embed_dim)`
2. Decoder cannot extract encoder context
3. Each decoder position attends to decoder states (not encoder), losing source info

### Correct Fix

```python
def forward(self, decoder_hidden, encoder_output):
    q = self.q_proj(decoder_hidden)    # Q from decoder
    k = self.k_proj(encoder_output)    # K from encoder
    v = self.v_proj(encoder_output)    # V from encoder
    # Reshape:
    q = q.reshape(B, tgt_len, num_heads, head_dim).transpose(1, 2)
    k = k.reshape(B, src_len, num_heads, head_dim).transpose(1, 2)
    v = v.reshape(B, src_len, num_heads, head_dim).transpose(1, 2)
    # Attention: q @ k.T -> (B, heads, tgt_len, src_len)
    # Output: -> (B, tgt_len, embed_dim)
```

---

## Training Config
- embed_dim: 48, src_len: 16, tgt_len: 10
- LR: 0.002, Epochs: 29, Batch: 16

## Deliverables
1. Fixed `cross_attention.py` with correct Q/K/V sources
2. `training_results.json` after running `python train.py`
3. `python check_cross_attn.py` exits 0
