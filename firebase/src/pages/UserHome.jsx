import React from 'react'
import { Typography, Paragraph } from 'antd';
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
        <Paragraph>
          How does this work? Good question. I'm not sure yet, but it'll probably be something like this:
        </Paragraph>
        <Paragraph>
          <ol>
            <li>Sign in with Strava ✅</li>
            <li>Any activity updates get sent to this app ✅</li>
            <li>Choose how you want to filter activities to go to UKC/UKH</li>
            <li>2 options now:</li>
            <ul>
              <li>You can trust this site with your UKC/UKH login detials (they dont have an API 😔) and it can automatically add your activities to your UKC/UKH Activity Dairy (after an optional delay)</li>
              <li>You can get an export of activties, ready to load into a local script that uploads them to UKC/UKH.</li>
            </ul>
          </ol>
        </Paragraph>
      </>
    }
    </>
  )
}

export default UserHome