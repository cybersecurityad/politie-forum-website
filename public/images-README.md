# Politie-Forum.nl - Image Assets

This directory contains all the image assets for the Politie-Forum.nl website, optimized for web performance and SEO.

## 📁 Image Assets Overview

### Favicon & App Icons
- `favicon-16x16.svg` - Small favicon (16x16px)
- `favicon-32x32.svg` - Standard favicon (32x32px)
- `apple-touch-icon.svg` - Apple touch icon (180x180px)
- `android-chrome-192x192.svg` - Android Chrome icon (192x192px)
- `android-chrome-512x512.svg` - Android Chrome icon (512x512px)
- `mstile-150x150.svg` - Windows tile icon (150x150px)

### News & Content Images
- `placeholder-news-1.svg` - News article placeholder (400x200px)
- `placeholder-news-2.svg` - Opsporing Verzocht placeholder (400x200px)
- `placeholder-news-3.svg` - Verkeersveiligheid placeholder (400x200px)

### User Interface Icons
- `default-avatar.svg` - Default user avatar (32x32px)
- `icon-news.svg` - News category icon (64x64px)
- `icon-legal.svg` - Legal category icon (64x64px)
- `icon-security.svg` - Security category icon (64x64px)

### Screenshots (PWA)
- `screenshot-mobile.svg` - Mobile app preview (390x844px)
- `screenshot-desktop.svg` - Desktop app preview (1280x720px)

### Logo
- `politie-nl-logo.png` - Main website logo

## 🎨 Design Guidelines

### Color Scheme
- **Primary Blue**: `#00008b` (Police blue)
- **Secondary Blue**: `#002d6b` (Dark blue)
- **Accent Red**: `#f60707` (Police red)
- **Background**: `#f4f6f9` (Light gray)
- **Text**: `#333333` (Dark gray)

### Icon Style
- **Format**: SVG (scalable vector graphics)
- **Background**: Circular with primary blue
- **Elements**: White or red details
- **Size**: Optimized for web performance

## 📱 Usage Instructions

### HTML Implementation
```html
<!-- Favicon -->
<link rel="icon" href="/favicon-32x32.svg" sizes="32x32" type="image/svg+xml">

<!-- Apple Touch Icon -->
<link rel="apple-touch-icon" href="/apple-touch-icon.svg">

<!-- Social Media Images -->
<meta property="og:image" content="/politie-nl-logo.png">
```

### CSS Implementation
```css
/* Category Icons */
.news-icon {
  background-image: url('/icon-news.svg');
  background-size: contain;
  background-repeat: no-repeat;
}
```

### PWA Manifest
The `site.webmanifest` file automatically references all necessary icons for progressive web app installation.

## 🔧 Technical Specifications

### Image Formats
- **SVG**: Primary format for icons and scalable graphics
- **PNG**: Used for logo and complex graphics
- **Responsive**: All images are optimized for different screen sizes

### Performance Optimization
- **File Size**: All SVGs are optimized for web delivery
- **Loading**: Critical images are preloaded in HTML
- **Caching**: Proper cache headers implemented

### Accessibility
- **Alt Text**: All images include descriptive alt attributes
- **Contrast**: High contrast ratios for visibility
- **Scalability**: Vector graphics maintain quality at all sizes

## 🚀 Deployment Notes

### File Organization
- All images are stored in the `/public/` directory
- File names follow kebab-case convention
- Related images are grouped logically

### CDN Considerations
- Images are optimized for fast loading
- Consider using a CDN for global distribution
- Implement lazy loading for non-critical images

### Browser Support
- **SVG**: Supported in all modern browsers
- **PNG**: Universal compatibility
- **WebP**: Consider adding WebP versions for better compression

## 📝 Maintenance

### Adding New Images
1. Follow the existing naming convention
2. Use SVG format when possible
3. Include in appropriate HTML/meta tags
4. Update this README

### Image Updates
1. Maintain consistent style and colors
2. Test across different devices
3. Update references in HTML and CSS
4. Clear browser cache for testing

## 📞 Support

For questions about image assets or requests for new images, refer to the SEO audit checklist or contact the development team.

---

**Last Updated**: August 29, 2025
**Format**: SVG (Scalable Vector Graphics)
**Total Images**: 15 image assets