"""Physical manuscript artifact and imperfection effects layer."""

import math
from typing import Optional

import numpy as np
from PIL import Image, ImageFilter

from src.config.settings import EffectsConfig


class ManuscriptEffects:
    """Applies realistic physical artifacts, aging, and optical/ink imperfections to manuscript folios."""

    def __init__(self, config: Optional[EffectsConfig] = None) -> None:
        self.config = config or EffectsConfig()

    def apply(self, image: Image.Image, seed: Optional[int] = None) -> Image.Image:
        """Apply configured physical effects pipeline to a rendered PIL image.

        Ensures:
        - Output image has the exact same dimensions as input.
        - Text remains crisp and completely readable.
        - Execution is 100% deterministic when seed is provided.
        """
        if not self.config.enabled:
            return image

        active_seed = seed if seed is not None else self.config.seed
        rng = np.random.default_rng(active_seed)

        img = image.convert("RGB") if image.mode != "RGB" else image.copy()

        # Step 1: Ink variation & stroke fading
        if self.config.enable_fade and self.config.fade_strength > 0:
            img = self._apply_ink_variation_and_fade(img, rng)

        # Step 2: Ink bleed into paper fibers
        if self.config.enable_ink_bleed and self.config.ink_bleed_strength > 0:
            img = self._apply_ink_bleed(img, rng)

        # Step 3: Sparse localized ink smudging
        if self.config.enable_smudge and self.config.smudge_strength > 0:
            img = self._apply_smudging(img, rng)

        # Step 4: Physical creases and folds
        if (
            self.config.enable_folds
            and self.config.fold_count > 0
            and self.config.fold_strength > 0
        ):
            img = self._apply_folds(img, rng)

        # Step 5: Page curvature and subtle geometric warping
        if self.config.enable_warp and self.config.warp_strength > 0:
            img = self._apply_warp(img, rng)

        # Step 6: Edge wear and boundary oxidation
        if self.config.edge_wear_strength > 0:
            img = self._apply_edge_wear(img, rng)

        return img

    def _extract_ink_mask(self, arr: np.ndarray) -> np.ndarray:
        """Calculate continuous float ink stroke mask in range [0.0, 1.0]."""
        lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        # Background is typically >180, ink is <70
        return np.clip((145.0 - lum) / 80.0, 0.0, 1.0)

    def _apply_ink_variation_and_fade(
        self, img: Image.Image, rng: np.random.Generator
    ) -> Image.Image:
        """Introduce subtle natural variation in ink density and light stroke fading."""
        w, h = img.size
        arr = np.array(img, dtype=np.float32)
        ink_mask = self._extract_ink_mask(arr)

        if not np.any(ink_mask > 0.05):
            return img

        # Low-frequency spatial density variation across folio
        grid_h = max(4, h // 48)
        grid_w = max(4, w // 48)
        low_noise = rng.uniform(0.75, 1.25, (grid_h, grid_w)).astype(np.float32)
        noise_img = Image.fromarray(low_noise).resize((w, h), Image.Resampling.BICUBIC)
        fade_map = np.array(noise_img)

        # Modulate ink pixels: lighter areas blend slightly with surrounding paper
        # Base paper tone estimation
        paper_tone = np.percentile(arr, 75, axis=(0, 1))

        # Attenuation factor for ink
        fade_factor = (
            ink_mask[:, :, None]
            * np.clip(1.0 - fade_map[:, :, None], -0.2, 0.4)
            * (self.config.fade_strength * 0.45)
        )
        arr += (paper_tone[None, None, :] - arr) * fade_factor

        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    def _apply_ink_bleed(
        self, img: Image.Image, rng: np.random.Generator
    ) -> Image.Image:
        """Simulate microscopic ink liquid diffusion into paper fibers along stroke contours."""
        w, h = img.size
        arr = np.array(img, dtype=np.float32)
        ink_mask = self._extract_ink_mask(arr)

        if not np.any(ink_mask > 0.05):
            return img

        # Microscopic dilation/blur of stroke mask
        mask_pil = Image.fromarray((ink_mask * 255).astype(np.uint8))
        blurred = mask_pil.filter(ImageFilter.GaussianBlur(radius=0.75))
        blurred_mask = np.array(blurred, dtype=np.float32) / 255.0

        # Bleed fringe is the outer dilated halo around ink strokes
        bleed_halo = np.clip(blurred_mask - ink_mask * 0.75, 0.0, 1.0)
        bleed_intensity = (
            bleed_halo[:, :, None] * (self.config.ink_bleed_strength * 22.0)
        )

        arr -= bleed_intensity
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    def _apply_smudging(
        self, img: Image.Image, rng: np.random.Generator
    ) -> Image.Image:
        """Introduce rare, tiny localized smudge streaks on manuscript folios."""
        w, h = img.size
        arr = np.array(img, dtype=np.float32)
        ink_mask = self._extract_ink_mask(arr)

        ink_y, ink_x = np.where(ink_mask > 0.6)
        if len(ink_x) < 20:
            return img

        # Select 1 or 2 small spots to smudge
        num_smudges = int(rng.integers(1, 3))
        for _ in range(num_smudges):
            idx = rng.integers(0, len(ink_x))
            cx, cy = int(ink_x[idx]), int(ink_y[idx])

            # Small smudge footprint
            dx_len = int(rng.integers(8, 16))
            dy_len = int(rng.integers(-2, 3))
            x0 = max(0, cx)
            x1 = min(w, cx + dx_len)
            y0 = max(0, cy + min(0, dy_len) - 2)
            y1 = min(h, cy + max(0, dy_len) + 3)

            if x1 > x0 and y1 > y0:
                # Soft horizontal smear
                smudge_patch = arr[y0:y1, x0:x1].copy()
                smudge_blur = Image.fromarray(smudge_patch.astype(np.uint8)).filter(
                    ImageFilter.GaussianBlur(radius=1.5)
                )
                smudge_arr = np.array(smudge_blur, dtype=np.float32)
                alpha = self.config.smudge_strength * 0.25
                arr[y0:y1, x0:x1] = (1.0 - alpha) * arr[
                    y0:y1, x0:x1
                ] + alpha * smudge_arr

        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    def _apply_folds(
        self, img: Image.Image, rng: np.random.Generator
    ) -> Image.Image:
        """Create subtle 3D physical crease/fold lines with shadow and highlight sides."""
        w, h = img.size
        arr = np.array(img, dtype=np.float32)

        xs = np.arange(w, dtype=np.float32)
        ys = np.arange(h, dtype=np.float32)
        X, Y = np.meshgrid(xs, ys)

        for _ in range(self.config.fold_count):
            # Choose fold line: vertical crease (common in binding) or slightly angled
            is_vertical = bool(rng.random() > 0.35)
            if is_vertical:
                x_pos = rng.uniform(w * 0.25, w * 0.75)
                angle = rng.uniform(-0.06, 0.06)
                nx, ny = math.cos(angle), math.sin(angle)
                d = (X - x_pos) * nx + (Y - h * 0.5) * ny
            else:
                y_pos = rng.uniform(h * 0.3, h * 0.7)
                angle = rng.uniform(-0.05, 0.05)
                nx, ny = -math.sin(angle), math.cos(angle)
                d = (X - w * 0.5) * nx + (Y - y_pos) * ny

            sigma = rng.uniform(4.0, 8.0)
            amp = rng.uniform(7.0, 14.0) * self.config.fold_strength

            # Shadow on d < 0 side, highlight on d > 0 side
            shadow = amp * np.exp(-0.5 * (d / sigma) ** 2) * (d < 0)
            highlight = (
                (amp * 0.6)
                * np.exp(-0.5 * (d / (sigma * 1.2)) ** 2)
                * (d >= 0)
            )

            arr -= shadow[:, :, None] * 1.1
            arr += highlight[:, :, None] * 0.85

        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    def _apply_warp(self, img: Image.Image, rng: np.random.Generator) -> Image.Image:
        """Apply subtle geometric mesh warping, center curvature, and perspective tilt."""
        w, h = img.size
        nx, ny = 8, 6
        x_steps = np.linspace(0, w, nx + 1)
        y_steps = np.linspace(0, h, ny + 1)

        # Conservative maximum displacement (subtle, non-destructive)
        max_disp = 7.0 * self.config.warp_strength

        vx = np.zeros((ny + 1, nx + 1), dtype=np.float32)
        vy = np.zeros((ny + 1, nx + 1), dtype=np.float32)

        # Subtle cylindrical arch across folio width
        arch_profile = np.sin(np.linspace(0, np.pi, nx + 1))[None, :] * (
            max_disp * 0.7
        )
        vy += arch_profile

        # Gentle internal vertex displacement
        vx[1:-1, 1:-1] += rng.uniform(
            -max_disp * 0.25, max_disp * 0.25, (ny - 1, nx - 1)
        )
        vy[1:-1, 1:-1] += rng.uniform(
            -max_disp * 0.25, max_disp * 0.25, (ny - 1, nx - 1)
        )

        mesh = []
        for j in range(ny):
            for i in range(nx):
                box = (
                    int(x_steps[i]),
                    int(y_steps[j]),
                    int(x_steps[i + 1]),
                    int(y_steps[j + 1]),
                )
                quad = (
                    x_steps[i] + vx[j, i],
                    y_steps[j] + vy[j, i],
                    x_steps[i] + vx[j + 1, i],
                    y_steps[j + 1] + vy[j + 1, i],
                    x_steps[i + 1] + vx[j + 1, i + 1],
                    y_steps[j + 1] + vy[j + 1, i + 1],
                    x_steps[i + 1] + vx[j, i + 1],
                    y_steps[j] + vy[j, i + 1],
                )
                mesh.append((box, quad))

        return img.transform(
            (w, h),
            Image.Transform.MESH,
            mesh,
            resample=Image.Resampling.BILINEAR,
        )

    def _apply_edge_wear(
        self, img: Image.Image, rng: np.random.Generator
    ) -> Image.Image:
        """Apply subtle boundary oxidation and edge wear around the outer margins."""
        w, h = img.size
        arr = np.array(img, dtype=np.float32)

        dist_x = (
            np.minimum(np.arange(w), w - 1 - np.arange(w))[None, :]
            / (w * 0.5)
        )
        dist_y = (
            np.minimum(np.arange(h), h - 1 - np.arange(h))[:, None]
            / (h * 0.5)
        )
        edge_dist = np.minimum(dist_x, dist_y)

        # Affects only the outer ~3% border region
        wear_zone = np.clip(1.0 - edge_dist * 16.0, 0.0, 1.0) ** 1.8
        wear_noise = rng.uniform(0.8, 1.2, (h, w)).astype(np.float32)

        darkening = (
            wear_zone * wear_noise * (self.config.edge_wear_strength * 12.0)
        )
        arr -= darkening[:, :, None]

        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
