// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import{ getFirestore}   from "firebase/firestore";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDj_8EemOJjOnFHGTlhmpUAU7Oq7ejnoJ4",
  authDomain: "techaire-6eff2.firebaseapp.com",
  projectId: "techaire-6eff2",
  storageBucket: "techaire-6eff2.firebasestorage.app",
  messagingSenderId: "345878976470",
  appId: "1:345878976470:web:5cae519a0de457e62b3677",
  measurementId: "G-D7Z48W0WF3"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

export const db = getFirestore(app);
