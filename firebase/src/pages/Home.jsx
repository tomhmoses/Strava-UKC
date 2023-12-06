import React from 'react'
import { Typography } from 'antd';
import { getAuth } from "firebase/auth";
import { useAuthState } from 'react-firebase-hooks/auth';
import { doc } from 'firebase/firestore';
import { useDocumentData } from 'react-firebase-hooks/firestore';
import UserHome from './UserHome';

const { Title } = Typography;

const Home = (props) => {

  const auth = getAuth();
  const [user, loading, error] = useAuthState(auth);

  if (loading) {
    return <div>Loading...</div>;
  }
  if (error) {
    return <div>Error: {JSON.stringify(error)}</div>;
  }
  if (user) {
    return (
      <UserHome firestore={props.firestore} user={user}/>
    )
  }
  return (
    <>
      <Title level={3}>Please Log In</Title>
    </>
  )
}

export default Home