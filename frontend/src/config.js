// API Configuration for different environments
const getApiUrl = () => {
  // Check if we're in development (localhost)
  if (window.location.hostname === 'localhost') {
    return 'http://localhost:3001';
  }
  
  // Check if deployed on Firebase Hosting
  if (window.location.hostname.includes('web.app') || 
      window.location.hostname.includes('firebaseapp.com')) {
    // Use Azure VM backend for Firebase deployment
    return import.meta.env.VITE_API_URL || 'http://YOUR_AZURE_VM_IP:3001';
  }
  
  // If deployed on Azure VM with frontend (future option)
  return `${window.location.protocol}//${window.location.hostname}:3001`;
};

export const API_URL = getApiUrl();

export default API_URL;

