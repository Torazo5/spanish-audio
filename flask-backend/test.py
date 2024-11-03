import torch
if torch.backends.mps.is_available() and torch.backends.mps.is_built():
    device = 'mps'
elif torch.cuda.is_available():
    device = 'cuda'
else:
    device = 'cpu'
print(device)