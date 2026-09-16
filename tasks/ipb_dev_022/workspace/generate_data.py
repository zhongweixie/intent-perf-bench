#!/usr/bin/env python3
"""Generate test image data for batch processing."""

import json
import random


def generate_test_images(num_images=200, pixels_per_image=5000):
    """Generate test image metadata with pixel data.

    Args:
        num_images: Number of images to generate
        pixels_per_image: Number of pixels per image

    Returns:
        List of image metadata dictionaries
    """
    images = []

    for i in range(num_images):
        # Generate random pixel values
        pixels = [random.randint(0, 255) for _ in range(pixels_per_image)]

        # Random transformation parameters
        brightness_factor = random.uniform(0.8, 1.2)
        contrast_factor = random.uniform(0.9, 1.1)

        image = {
            'image_id': f"img_{i:04d}",
            'width': 100,
            'height': 50,
            'pixels': pixels,
            'brightness_factor': brightness_factor,
            'contrast_factor': contrast_factor
        }
        images.append(image)

    return images


if __name__ == '__main__':
    print("Generating test image data...")
    images = generate_test_images(num_images=200, pixels_per_image=2500)

    with open('test_images.json', 'w', encoding='utf-8') as f:
        json.dump(images, f, indent=2)

    print(f"Generated {len(images)} images -> test_images.json")
    print(f"Each image: {len(images[0]['pixels'])} pixels")
    print(f"Total pixels: {len(images) * len(images[0]['pixels']):,}")
