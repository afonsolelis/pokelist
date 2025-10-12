export function normalizeCloudinary(url, { width = 900, height = 1200, pad = true } = {}) {
  if (!url || !url.includes('res.cloudinary.com') || !url.includes('/image/upload')) return url
  try {
    const [before, after] = url.split('/image/upload/')
    const firstSeg = after.split('/', 1)[0]
    if (/(^|,)w_|(^|,)h_|(^|,)c_|(^|,)q_|(^|,)f_|(^|,)ar_/.test(firstSeg)) return url
    const transform = pad
      ? `f_auto,q_auto,c_pad,b_white,w_${width},h_${height}`
      : `f_auto,q_auto,c_limit,w_${width}`
    return `${before}/image/upload/${transform}/${after}`
  } catch {
    return url
  }
}

export function thumbCloudinary(url, size = 80) {
  if (!url || !url.includes('res.cloudinary.com') || !url.includes('/image/upload')) return url
  try {
    const [before, after] = url.split('/image/upload/')
    const transform = `f_auto,q_auto,c_fill,g_auto,w_${size},h_${size}`
    return `${before}/image/upload/${transform}/${after}`
  } catch {
    return url
  }
}

