import time
import timm
import torch

model = timm.create_model("mobilenetv3_large_100", pretrained=True, num_classes=10).eval()
x = torch.randn(1, 3, 224, 224)
with torch.no_grad():
    t = time.time()
    y = model(x)
print(y.shape, f"{(time.time() - t) * 1000:.0f} ms (CPU PC)")
print(f"{sum(p.numel() for p in model.parameters()) / 1e6:.1f} M paramètres")