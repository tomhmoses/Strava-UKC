import React from 'react'
import { Typography } from 'antd';
import { getAuth } from "firebase/auth";
import { useAuthState } from 'react-firebase-hooks/auth';
import { doc } from 'firebase/firestore';
import { useDocumentData } from 'react-firebase-hooks/firestore';

const { Title } = Typography;

const Home = (props) => {

  const auth = getAuth();
  const [user, loading, error] = useAuthState(auth);

  const uid = user && user.uid || null;

  const userRef = doc(props.firestore, "users", uid);
  const [data] = useDocumentData(userRef);

  if (loading) {
    return <div>Loading...</div>;
  }
  if (error) {
    return <div>Error: {JSON.stringify(error)}</div>;
  }
  if (user) {
    return (
      <>
        <Title level={1}>Home</Title>
        <Title level={3}>Welcome {user.email}</Title>
        {data.stravaId && <Title level={3}>Your Strava ID is {data.stravaId}</Title>}
        {data && !data.stravaId && <Title level={3}>Please link your Strava account</Title>}
        {!data && <Title level={3}>Loading account data...</Title>}
      </>
    )
  }
  return (
    <>
      <Title level={3}>Please Log In</Title>
    </>
  )
}

export default Home