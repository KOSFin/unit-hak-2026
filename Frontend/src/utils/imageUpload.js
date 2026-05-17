const DEFAULT_IMAGE_DIMENSION = 256;
const DEFAULT_IMAGE_QUALITY = 0.68;

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const image = new Image();

    image.onload = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error('Failed to read image'));
    };
    image.src = objectUrl;
  });
}

function canvasToBlob(canvas, type, quality) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) {
        resolve(blob);
        return;
      }
      reject(new Error('Failed to encode image'));
    }, type, quality);
  });
}

export async function compressImageBeforeUpload(
  file,
  {
    maxDimension = DEFAULT_IMAGE_DIMENSION,
    quality = DEFAULT_IMAGE_QUALITY,
    mimeType = 'image/webp',
  } = {},
) {
  if (!(file instanceof File) || !file.type.startsWith('image/')) {
    return file;
  }

  try {
    const image = await loadImage(file);
    const scale = Math.min(1, maxDimension / Math.max(image.width, image.height));
    const width = Math.max(1, Math.round(image.width * scale));
    const height = Math.max(1, Math.round(image.height * scale));

    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext('2d', { alpha: false });
    if (!context) {
      return file;
    }

    context.fillStyle = '#ffffff';
    context.fillRect(0, 0, width, height);
    context.drawImage(image, 0, 0, width, height);

    let blob;
    try {
      blob = await canvasToBlob(canvas, mimeType, quality);
    } catch {
      blob = await canvasToBlob(canvas, 'image/jpeg', quality);
    }

    if (blob.size >= file.size) {
      return file;
    }

    const extension = blob.type === 'image/webp' ? 'webp' : 'jpg';
    const nameBase = file.name.replace(/\.[^.]+$/, '') || 'upload';
    return new File([blob], `${nameBase}.${extension}`, {
      type: blob.type,
      lastModified: Date.now(),
    });
  } catch {
    return file;
  }
}
