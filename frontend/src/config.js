// API Configuration for different environments
const getApiUrl = () => {
  // Check if we're in development (localhost)
  if (window.location.hostname === 'localhost') {
    return 'http://localhost:3001';
  }
  
  // Check if deployed on Firebase Hosting
  if (window.location.hostname.includes('web.app') || 
      window.location.hostname.includes('firebaseapp.com')) {
    // Use HTTPS backend URL - IMPORTANT: Must be HTTPS for Firebase deployment
    // Option 1: Use your domain with SSL (e.g., https://api.yourdomain.com)
    // Option 2: Use Cloudflare Tunnel (free HTTPS without domain/SSL setup)
    return import.meta.env.VITE_API_URL || 'https://YOUR_BACKEND_DOMAIN';
  }
  
  // If deployed on Azure VM with frontend (future option)
  return `${window.location.protocol}//${window.location.hostname}:3001`;
};

export const API_URL = getApiUrl();

export default API_URL;

