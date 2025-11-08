// Production API configuration
export const API_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:3001'
  : `${window.location.protocol}//${window.location.hostname}:3001`;

export default API_URL;
