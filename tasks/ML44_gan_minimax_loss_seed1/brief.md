# ML44: GAN Minimax Loss Bug (Brief)

## Your Task
Fix the generator loss in `gan.py`.

Training a GAN on **tabular feature distribution** fails because the generator uses
the original minimax loss which saturates when the discriminator is confident.

## Symptoms
- Generator loss is near 0 but coverage of real data modes is low
- Generator doesn't improve after initial discriminator becomes confident
- Gradient norms near 0 for the generator

## What to Fix
- `gan.py`: `GAN.generator_loss()` — change `log(1 - D(G(z)))` to `-log(D(G(z)))`
- Do NOT modify `train.py`

## Success Criteria
- `python check_gan.py` exits 0
- Data coverage > 0.5
