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
    {!data && <Title level={3}>Loading account data...</Title>}
    {data &&
      <>
        {!data.firstname && <Title level={3}>
          User data is incomplete.
        </Title>}
        {data.firstname && <Title level={3}>Welcome {data.firstname}</Title>}
      </>
    }
    </>
  )
}

export default UserHome