import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, onAuthStateChanged, signOut, createUserWithEmailAndPassword, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import { getFirestore, collection, addDoc, query, where, getDocs, orderBy } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js";

// TODO: Replace this with your actual Firebase config from the Firebase Console
const firebaseConfig = {
  apiKey: "AIzaSyDChJzsccy4Ikbr7RJj3l8CCY5gtZOp1Qw",
  authDomain: "mirror-ai-9fc04.firebaseapp.com",
  projectId: "mirror-ai-9fc04",
  storageBucket: "mirror-ai-9fc04.firebasestorage.app",
  messagingSenderId: "394138518171",
  appId: "1:394138518171:web:24345f092c39c9adac3c3e"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const provider = new GoogleAuthProvider();

export { auth, db, provider, signInWithPopup, onAuthStateChanged, signOut, collection, addDoc, query, where, getDocs, orderBy, createUserWithEmailAndPassword, signInWithEmailAndPassword };
