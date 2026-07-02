import os
import numpy as np
import cv2
from PIL import Image as PILImage
from features_extraction import arthur_extract_features


def _normalize_lighting(gray):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _zone_features(edges, grid=4):
    h, w = edges.shape
    zh, zw = h // grid, w // grid
    scores = []
    for i in range(grid):
        for j in range(grid):
            ze = edges[i*zh:(i+1)*zh, j*zw:(j+1)*zw]
            if ze.size:
                scores.append((ze > 0).sum() / ze.size)
    return float(max(scores)), float(np.var(scores))


def _ground_clutter(gray_norm):
    h = gray_norm.shape[0]
    band = gray_norm[int(h * 0.6):, :]
    if band.size == 0:
        return 0.0
    return float(cv2.Laplacian(band, cv2.CV_64F).std())


def _hue_zone_features(arr, grid=4):
    r = arr[:, :, 0].astype(int)
    g = arr[:, :, 1].astype(int)
    b = arr[:, :, 2].astype(int)
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b))
    hue = np.where(hue < 0, hue + 360, hue)
    green = ((hue >= 60) & (hue <= 180)).astype(float)
    h, w = green.shape
    zh, zw = h // grid, w // grid
    zones = []
    for i in range(grid):
        for j in range(grid):
            z = green[i*zh:(i+1)*zh, j*zw:(j+1)*zw]
            if z.size:
                zones.append(z.mean())
    return float(max(zones)), float(np.var(zones))


def extract_features(filepath):
    file_size = os.path.getsize(filepath)

    with PILImage.open(filepath) as img:
        img = img.convert("RGB")
        width, height = img.size
        arr = np.array(img)

    aspect_ratio = round(width / height, 3) if height else 0

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    avg_r, avg_g, avg_b = float(r.mean()), float(g.mean()), float(b.mean())

    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    gray_norm = _normalize_lighting(gray)

    brightness = float(gray.mean())
    contrast = float(gray.max() - gray.min())
    dark_ratio = float((gray_norm < 50).sum() / gray_norm.size)

    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
    saturation = float(hsv[:, :, 1].mean())

    rg = r.astype(int) - g.astype(int)
    yb = 0.5 * (r.astype(int) + g.astype(int)) - b.astype(int)
    colorfulness = float(np.sqrt(rg.std() ** 2 + yb.std() ** 2)
                         + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2))

    edges = cv2.Canny(gray_norm, 100, 200)
    edge_density = float((edges > 0).sum() / edges.size)

    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    texture = float(cv2.Laplacian(gray_norm, cv2.CV_64F).std())

    hist = np.histogram(gray, bins=256, range=(0, 256))[0]
    hist = hist / hist.sum()
    hist = hist[hist > 0]
    entropy = float(-(hist * np.log2(hist)).sum())

    green_mask = (g > r) & (g > b)
    green_ratio = float(green_mask.sum() / g.size)

    max_zone_edges, zone_variance = _zone_features(edges)

    h = edges.shape[0]
    band = edges[int(h * 0.6):, :]
    bottom_edge_density = float((band > 0).sum() / band.size) if band.size else 0.0

    ground_clutter = _ground_clutter(gray_norm)

    green_zone_max, green_zone_var = _hue_zone_features(arr)

    dict_features = {
        "file_size": file_size,
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "avg_r": round(avg_r, 2),
        "avg_g": round(avg_g, 2),
        "avg_b": round(avg_b, 2),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "saturation": round(saturation, 2),
        "colorfulness": round(colorfulness, 2),
        "dark_ratio": round(dark_ratio, 4),
        "edge_density": round(edge_density, 4),
        "sharpness": round(sharpness, 2),
        "texture": round(texture, 2),
        "entropy": round(entropy, 3),
        "green_ratio": round(green_ratio, 4),
        "max_zone_edges": round(max_zone_edges, 4),
        "zone_variance": round(zone_variance, 6),
        "bottom_edge_density": round(bottom_edge_density, 4),
        "ground_clutter": round(ground_clutter, 2),
        "green_zone_max": round(green_zone_max, 4),
        "green_zone_var": round(green_zone_var, 6),
    }

    # Arthur features:
    dict_features = arthur_extract_features(filepath) | dict_features

    return dict_features
