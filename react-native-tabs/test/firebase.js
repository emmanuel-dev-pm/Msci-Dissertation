// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getFirestore } from "firebase/firestore";
import { initializeAuth, browserLocalPersistence, getReactNativePersistence } from "firebase/auth";
import { Platform } from "react-native";

// For React Native only
let ReactNativeAsyncStorage;
if (Platform.OS !== 'web') {
  ReactNativeAsyncStorage = require("@react-native-async-storage/async-storage").default;
}

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDj_8EemOJjOnFHGTlhmpUAU7Oq7ejnoJ4",
  authDomain: "techaire-6eff2.firebaseapp.com",
  projectId: "techaire-6eff2",
  storageBucket: "techaire-6eff2.firebasestorage.app"
  ,
  messagingSenderId: "345878976470",
  appId: "1:345878976470:web:5cae519a0de457e62b3677",
  measurementId: "G-D7Z48W0WF3"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
console.log("Firebase App Initialized", app);

// Choose persistence based on platform
const persistence = Platform.OS === 'web' 
  ? browserLocalPersistence 
  : getReactNativePersistence(ReactNativeAsyncStorage);

export const FIREBASE_AUTH = initializeAuth(app, {
  persistence: persistence
});
console.log(FIREBASE_AUTH);
export const db = getFirestore(app);
