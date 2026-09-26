"""Procedural historical manuscript background and texture generation."""

from typing import Callable, Dict, Optional, Tuple

import numpy as np
from PIL import Image

from src.config.settings import BackgroundConfig


class BackgroundGenerator:
    """Procedurally generates authentic historical manuscript backgrounds."""

    def __init__(
        self,
        config: Optional[BackgroundConfig] = None,
        width: int = 1200,
        height: int = 800,
    ) -> None:
        self.config = config or BackgroundConfig()
        self.width = width
        self.height = height

        # Extensible material dispatch registry
        self._generators: Dict[
            str, Callable[[int, int, np.random.Generator], Image.Image]
        ] = {
            "paper": self._generate_paper,
            "palm_leaf": self._generate_palm_leaf,
        }

    def register_material(
        self,
        name: str,
        generator_fn: Callable[[int, int, np.random.Generator], Image.Image],
    ) -> None:
        """Register a new manuscript material generator for future extensions."""
        self._generators[name] = generator_fn

    def generate(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> Image.Image:
        """Generate a procedural manuscript background.

        Args:
            width: Target image width in pixels.
            height: Target image height in pixels.
            seed: Optional integer seed for deterministic generation.

        Returns:
            Pillow Image in RGB mode with authentic historical texture.
        """
        w = width if width is not None else self.width
        h = height if height is not None else self.height

        active_seed = seed if seed is not None else self.config.seed
        rng = np.random.default_rng(active_seed)

        material = self.config.background_type
        if material not in self._generators:
            raise ValueError(
                f"Unsupported material type '{material}'. Registered: {list(self._generators.keys())}"
            )

        return self._generators[material](w, h, rng)

    def _generate_paper(
        self, width: int, height: int, rng: np.random.Generator
    ) -> Image.Image:
        """Generate aged handmade paper with subtle fibers, mottling, and organic edges."""
        # 1. Base color (historical warm parchment / antique buff)
        if self.config.base_color:
            base_rgb = np.array(self.config.base_color, dtype=np.float32)
        else:
            base_rgb = np.array([244.0, 237.0, 221.0], dtype=np.float32)

        # Subtle natural base tint shift
        base_tint = rng.uniform(-1.5, 1.5, 3).astype(np.float32)
        canvas = np.empty((height, width, 3), dtype=np.float32)
        canvas[:, :] = base_rgb + base_tint

        # 2. Low-frequency color variation (smooth cloudiness / paper mottling)
        if self.config.texture_strength > 0:
            grid_h = max(4, height // 64)
            grid_w = max(4, width // 64)
            low_noise = rng.uniform(-1.0, 1.0, (grid_h, grid_w)).astype(np.float32)
            mottling_img = Image.fromarray(low_noise).resize(
                (width, height), Image.Resampling.BICUBIC
            )
            mottling = np.array(mottling_img) * (self.config.texture_strength * 7.0)
            # Apply warm tint to mottling
            canvas[:, :, 0] += mottling * 1.0
            canvas[:, :, 1] += mottling * 0.9
            canvas[:, :, 2] += mottling * 0.75

        # 3. Fine paper grain
        if self.config.texture_strength > 0:
            grain = rng.normal(0.0, 1.0, (height, width)).astype(np.float32) * (
                self.config.texture_strength * 2.8
            )
            canvas += grain[:, :, None]

        # 4. Sparse plant fibers
        if self.config.texture_strength > 0:
            fiber_prob = 0.0004 * self.config.texture_strength
            fiber_mask = rng.random((height, width)) < fiber_prob
            canvas[fiber_mask] -= np.array([12.0, 14.0, 16.0], dtype=np.float32)

        # 5. Faint historical water stains / aging droplets
        if self.config.stain_strength > 0:
            num_stains = int(rng.integers(2, 5))
            for _ in range(num_stains):
                cx = rng.integers(int(width * 0.1), int(width * 0.9))
                cy = rng.integers(int(height * 0.1), int(height * 0.9))
                rx = rng.uniform(35.0, 90.0)
                ry = rng.uniform(35.0, 90.0)
                intensity = rng.uniform(3.0, 7.5) * self.config.stain_strength

                # Bounding box of stain to keep computation localized and fast
                x0 = max(0, int(cx - 3 * rx))
                x1 = min(width, int(cx + 3 * rx))
                y0 = max(0, int(cy - 3 * ry))
                y1 = min(height, int(cy + 3 * ry))

                if x1 > x0 and y1 > y0:
                    xs = np.arange(x0, x1, dtype=np.float32)
                    ys = np.arange(y0, y1, dtype=np.float32)
                    dx = ((xs - cx) / rx) ** 2
                    dy = ((ys - cy) / ry) ** 2
                    dist_sq = dy[:, None] + dx[None, :]
                    stain_kernel = np.exp(-0.5 * dist_sq) * intensity

                    canvas[y0:y1, x0:x1, 0] -= stain_kernel * 0.9
                    canvas[y0:y1, x0:x1, 1] -= stain_kernel * 1.1
                    canvas[y0:y1, x0:x1, 2] -= stain_kernel * 1.4

        # 6. Organic edge darkening / oxidation
        if self.config.edge_variation > 0 and self.config.aging_strength > 0:
            dist_x = (
                np.minimum(np.arange(width), width - 1 - np.arange(width))[None, :]
                / (width * 0.5)
            )
            dist_y = (
                np.minimum(np.arange(height), height - 1 - np.arange(height))[:, None]
                / (height * 0.5)
            )
            edge_dist = np.minimum(dist_x, dist_y)
            edge_vignette = (
                np.clip(1.0 - edge_dist * 3.2, 0.0, 1.0).astype(np.float32) ** 1.6
            )

            # Modulate with low-resolution organic noise for non-rigid irregular edges
            edge_noise_raw = rng.uniform(0.75, 1.25, (8, 12)).astype(np.float32)
            edge_noise = np.array(
                Image.fromarray(edge_noise_raw).resize(
                    (width, height), Image.Resampling.BILINEAR
                )
            )

            darkening = (
                edge_vignette
                * edge_noise
                * (self.config.edge_variation * 14.0)
                * (self.config.aging_strength * 1.2)
            )
            canvas[:, :, 0] -= darkening * 0.95
            canvas[:, :, 1] -= darkening * 1.05
            canvas[:, :, 2] -= darkening * 1.3

        clipped = np.clip(canvas, 0, 255).astype(np.uint8)
        return Image.fromarray(clipped, mode="RGB")

    def _generate_palm_leaf(
        self, width: int, height: int, rng: np.random.Generator
    ) -> Image.Image:
        """Generate authentic palm-leaf (tala-patra) manuscript surface with longitudinal fibers."""
        # 1. Base color (dry golden-amber palm leaf)
        if self.config.base_color:
            base_rgb = np.array(self.config.base_color, dtype=np.float32)
        else:
            base_rgb = np.array([218.0, 188.0, 136.0], dtype=np.float32)

        leaf_tint = rng.uniform(-2.0, 2.0, 3).astype(np.float32)
        canvas = np.empty((height, width, 3), dtype=np.float32)
        canvas[:, :] = base_rgb + leaf_tint

        # 2. Longitudinal fibers and vein striations along folio width
        if self.config.texture_strength > 0:
            vein_h = max(8, height // 16)
            vein_profile = rng.normal(0.0, 1.0, (vein_h, 1)).astype(np.float32)
            veins_img = Image.fromarray(vein_profile).resize(
                (width, height), Image.Resampling.BILINEAR
            )
            veins = np.array(veins_img) * (self.config.texture_strength * 6.5)

            # Fine micro-grain along the horizontal leaf fibers
            fine_w = max(8, width // 8)
            fine_grain = rng.normal(0.0, 1.0, (height, fine_w)).astype(np.float32)
            fine_img = Image.fromarray(fine_grain).resize(
                (width, height), Image.Resampling.BICUBIC
            )
            fine_fibers = np.array(fine_img) * (self.config.texture_strength * 3.5)

            fiber_pattern = veins + fine_fibers
            canvas[:, :, 0] += fiber_pattern * 1.0
            canvas[:, :, 1] += fiber_pattern * 0.95
            canvas[:, :, 2] += fiber_pattern * 0.8

        # 3. Occasional natural horizontal rib lines
        if self.config.aging_strength > 0:
            num_ribs = int(rng.integers(2, 5))
            for _ in range(num_ribs):
                rib_y = rng.integers(10, height - 10)
                rib_thickness = rng.integers(1, 3)
                y_start = max(0, rib_y - rib_thickness)
                y_end = min(height, rib_y + rib_thickness + 1)
                rib_intensity = rng.uniform(4.0, 8.0) * self.config.aging_strength
                canvas[y_start:y_end, :, 0] -= rib_intensity * 0.9
                canvas[y_start:y_end, :, 1] -= rib_intensity * 1.1
                canvas[y_start:y_end, :, 2] -= rib_intensity * 1.4

        # 4. Top/bottom edge darkening (where palm leaves are cut and trimmed)
        if self.config.edge_variation > 0 and self.config.aging_strength > 0:
            dist_tb = (
                np.minimum(np.arange(height), height - 1 - np.arange(height))[:, None]
                / (height * 0.5)
            )
            leaf_vignette = (
                np.clip(1.0 - dist_tb * 3.8, 0.0, 1.0).astype(np.float32) ** 1.5
            )

            side_dist = (
                np.minimum(np.arange(width), width - 1 - np.arange(width))[None, :]
                / (width * 0.5)
            )
            side_vignette = (
                np.clip(1.0 - side_dist * 4.0, 0.0, 1.0).astype(np.float32) ** 2.0
            )

            total_vignette = np.maximum(leaf_vignette, side_vignette * 0.7)
            edge_darkening = total_vignette * (
                self.config.edge_variation * self.config.aging_strength * 20.0
            )
            canvas[:, :, 0] -= edge_darkening * 0.9
            canvas[:, :, 1] -= edge_darkening * 1.05
            canvas[:, :, 2] -= edge_darkening * 1.3

        clipped = np.clip(canvas, 0, 255).astype(np.uint8)
        return Image.fromarray(clipped, mode="RGB")
