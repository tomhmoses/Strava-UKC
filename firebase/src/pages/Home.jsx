import React from 'react'
import { Typography } from 'antd';
import { getAuth } from "firebase/auth";
import { useAuthState } from 'react-firebase-hooks/auth';

const { Title } = Typography;

const Home = () => {

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
      <>
        <Title level={1}>Home</Title>
        <Title level={3}>Welcome {user.email}</Title>
      </>
    )
  }
  return (
    <>
      <Title level={1}>Home</Title>
      <Title level={3}>Please Log In</Title>
    </>
  )
}

export default Home