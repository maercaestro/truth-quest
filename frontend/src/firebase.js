import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, GithubAuthProvider } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIzaSyDinCHAekCL0sRDUA64QRq_jl4THqx68EU",
  authDomain: "truth-quest.firebaseapp.com",
  projectId: "truth-quest",
  storageBucket: "truth-quest.firebasestorage.app",
  messagingSenderId: "587771292165",
  appId: "1:587771292165:web:042fe664bd86838e9f0a6c",
  measurementId: "G-EDW4SYT4X8"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication
export const auth = getAuth(app);

// Auth providers
export const googleProvider = new GoogleAuthProvider();
export const githubProvider = new GithubAuthProvider();

export default app;
