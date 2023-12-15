import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Home from './pages/Home';
import CompleteLogin from './pages/auth/CompleteLogin';
import UploadPrev from './pages/UploadPrev';
// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
// import { getAnalytics } from "firebase/analytics";
import { getFirestore } from 'firebase/firestore';
import { getFunctions } from 'firebase/functions';
import { getAuth, signOut } from "firebase/auth";
import { useAuthState } from 'react-firebase-hooks/auth';
import AppTemplate from './components/AppTemplate';
import ErrorPage from './components/ErrorPage';

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
// const analytics = getAnalytics(app);
const firestore = getFirestore(app);
const functions = getFunctions(app, 'europe-west2');

function App() {

  const auth = getAuth();
  const logout = () => {
    signOut(auth);
  }

  const [user, loading, error] = useAuthState(auth);

  const router = createBrowserRouter([
    {
      path: '/',
      element: <AppTemplate user={user} logout={logout} />,
      errorElement: <ErrorPage />,
      children: [
        { path: '*', element: <ErrorPage notFound={true} /> },
        { path: '/', element: <Home firestore={firestore} functions={functions} user={user} loading={loading} error={error}/> },
        { path: 'upload-previous', element: <UploadPrev firestore={firestore} functions={functions}/> },
        { path: 'completelogin', element: <CompleteLogin /> }
      ]
    }
  ]);

  return (
    <>
      <RouterProvider router={router}/>
    </>
  );
}

export default App;