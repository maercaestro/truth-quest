import { createContext, useContext, useEffect, useState } from 'react';
import { 
  signInWithPopup, 
  signOut, 
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  GoogleAuthProvider
} from 'firebase/auth';
import { auth, googleProvider, githubProvider } from '../firebase';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [idToken, setIdToken] = useState(null);

  console.log('🔐 AuthContext State:', { 
    currentUser: currentUser?.email, 
    loading, 
    hasToken: !!idToken
  });

  // Sign in with Google
  const signInWithGoogle = async () => {
    console.log('🟢 Attempting Google sign-in...');
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const token = await result.user.getIdToken();
      setIdToken(token);
      console.log('✅ Google sign-in successful:', result.user.email);
      return result.user;
    } catch (error) {
      console.error('❌ Google sign in error:', error);
      throw error;
    }
  };

  // Sign in with GitHub
  const signInWithGithub = async () => {
    console.log('🔵 Attempting GitHub sign-in...');
    try {
      const result = await signInWithPopup(auth, githubProvider);
      const token = await result.user.getIdToken();
      setIdToken(token);
      return result.user;
    } catch (error) {
      console.error('GitHub sign in error:', error);
      throw error;
    }
  };

  // Sign in with Email/Password
  const signInWithEmail = async (email, password) => {
    try {
      const result = await signInWithEmailAndPassword(auth, email, password);
      const token = await result.user.getIdToken();
      setIdToken(token);
      return result.user;
    } catch (error) {
      console.error('Email sign in error:', error);
      throw error;
    }
  };

  // Sign up with Email/Password
  const signUpWithEmail = async (email, password) => {
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password);
      const token = await result.user.getIdToken();
      setIdToken(token);
      return result.user;
    } catch (error) {
      console.error('Email sign up error:', error);
      throw error;
    }
  };

  // Sign out
  const logout = async () => {
    try {
      await signOut(auth);
      setIdToken(null);
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  };

  // Get fresh token
  const getToken = async () => {
    if (currentUser) {
      const token = await currentUser.getIdToken();
      setIdToken(token);
      return token;
    }
    return null;
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setCurrentUser(user);
      if (user) {
        const token = await user.getIdToken();
        setIdToken(token);
      } else {
        setIdToken(null);
      }
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const value = {
    currentUser,
    idToken,
    signInWithGoogle,
    signInWithGithub,
    signInWithEmail,
    signUpWithEmail,
    logout,
    getToken
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}
