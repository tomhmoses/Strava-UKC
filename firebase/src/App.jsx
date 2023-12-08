import React from 'react';
import { Route, createBrowserRouter, createRoutesFromElements, RouterProvider } from 'react-router-dom';
import Home from './pages/Home';
import CompleteLogin from './pages/auth/CompleteLogin';
import Header from './components/nav/Header';
// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getFirestore } from 'firebase/firestore';
import { getFunctions } from 'firebase/functions';
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyBDMDOBiuMFOtZj7nADTuel3jLZSZzedTo",
  authDomain: "strava-ukc.firebaseapp.com",
  projectId: "strava-ukc",
  storageBucket: "strava-ukc.appspot.com",
  messagingSenderId: "225137813134",
  appId: "1:225137813134:web:695b0d75e629bfd592cbdf",
  measurementId: "G-DE6RNFDTPS"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const firestore = getFirestore(app);
const functions = getFunctions(app, 'europe-west2');




const router = createBrowserRouter(
  createRoutesFromElements(
    <Route path="/" element={<Header />}>
      <Route index element={<Home firestore={firestore} functions={functions}/>} />
      <Route path="completelogin" element={<CompleteLogin />} />
      <Route path="*" element={<h1>Not Found</h1>} />
    </Route>
  )
)

function App({routes}) {

  return (
    <>
      <RouterProvider router={router}/>
    </>
  );
}

export default App;