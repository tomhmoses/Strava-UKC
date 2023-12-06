import React from 'react'
import { Typography } from 'antd';
import { doc } from 'firebase/firestore';
import { useDocumentData } from 'react-firebase-hooks/firestore';

const { Title } = Typography;

const UserHome = (props) => {

  const userRef = doc(props.firestore, "users", props.user.uid);
  const [data] = useDocumentData(userRef);
  console.log(data);
  return (
    <>
    <Title level={1}>Home</Title>
    <Title level={3}>Welcome {props.user.email}</Title>
    {data.stravaId && <Title level={3}>Your Strava ID is {data.stravaId}</Title>}
    {data && !data.stravaId && <Title level={3}>Please link your Strava account</Title>}
    {!data && <Title level={3}>Loading account data...</Title>}
    </>
  )
}

export default UserHome