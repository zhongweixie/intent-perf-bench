"""Image processing utilities for batch transformations."""

import json


def load_image_metadata(filepath):
    """Load image metadata from JSON file.

    Args:
        filepath: Path to metadata JSON file

    Returns:
        List of image metadata dictionaries
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def apply_brightness_adjustment(value, factor):
    """Apply brightness adjustment to a pixel value.

    Args:
        value: Original pixel value (0-255)
        factor: Brightness factor (0.5 = darker, 2.0 = brighter)

    Returns:
        Adjusted pixel value clamped to 0-255
    """
    adjusted = int(value * factor)
    return max(0, min(255, adjusted))


def apply_contrast_adjustment(value, factor, midpoint=128):
    """Apply contrast adjustment to a pixel value.

    Args:
        value: Original pixel value (0-255)
        factor: Contrast factor (>1 = more contrast)
        midpoint: Contrast center point

    Returns:
        Adjusted pixel value clamped to 0-255
    """
    adjusted = int((value - midpoint) * factor + midpoint)
    return max(0, min(255, adjusted))


def compute_histogram(pixels):
    """Compute histogram from pixel values.

    Args:
        pixels: List of pixel values (0-255)

    Returns:
        Dictionary mapping value -> count
    """
    histogram = {}
    for value in pixels:
        histogram[value] = histogram.get(value, 0) + 1
    return histogram


def process_image_batch(images):
    """Process a batch of images with transformations.

    This implementation separates brightness and contrast steps for modularity.

    Args:
        images: List of image metadata dictionaries

    Returns:
        List of processed image metadata with transformation results
    """
    processed = []

    for img in images:
        # Extract pixel data
        pixels = img.get('pixels', [])

        # Apply transformations
        brightness_factor = img.get('brightness_factor', 1.0)
        contrast_factor = img.get('contrast_factor', 1.0)

        # Apply brightness in separate pass
        after_brightness = list(map(
            lambda p: apply_brightness_adjustment(p, brightness_factor),
            pixels
        ))

        # Apply contrast in separate pass
        adjusted_pixels = list(map(
            lambda p: apply_contrast_adjustment(p, contrast_factor),
            after_brightness
        ))

        # Compute histogram on transformed pixels
        histogram = compute_histogram(adjusted_pixels)

        # Create result
        result = {
            'image_id': img.get('image_id'),
            'width': img.get('width'),
            'height': img.get('height'),
            'original_pixels': pixels,
            'adjusted_pixels': adjusted_pixels,
            'histogram': histogram,
            'mean_value': sum(adjusted_pixels) / len(adjusted_pixels) if adjusted_pixels else 0
        }
        processed.append(result)

    return processed


def save_processed_images(images, filepath):
    """Save processed image metadata to JSON file.

    Args:
        images: List of processed image dictionaries
        filepath: Output file path
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(images, f, indent=2)
