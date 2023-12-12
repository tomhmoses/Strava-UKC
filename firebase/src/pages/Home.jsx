import React from 'react'
import { Typography, Layout, Button, Spin } from 'antd';
import { ApiTwoTone } from '@ant-design/icons';
import { getAuth } from "firebase/auth";
import { useAuthState } from 'react-firebase-hooks/auth';
import { doc } from 'firebase/firestore';
import { useDocumentData } from 'react-firebase-hooks/firestore';
import UserHome from './UserHome';
import AppFooter from '../components/AppFooter';
import AppHeader from '../components/nav/AppHeader';

const { Content } = Layout;

const { Title, Paragraph } = Typography;

const Home = (props) => {

  const auth = getAuth();
  const [user, loading, error] = useAuthState(auth);

  if (loading) {
    return <Spin />;
  }
  if (error) {
    return <div>Error: {JSON.stringify(error)}</div>;
  }
  if (user) {
    return (
      <Layout style={{ minHeight: "100vh", background: 'white'}}>
        <AppHeader />
        <Content style={{
          padding: 12,
          margin: 'auto',
          width: '100%',
          maxWidth: 800,
        }}>
          <UserHome firestore={props.firestore} functions={props.functions} user={user}/>
        </Content>
        <AppFooter />
      </Layout>
    )
  }
  return (
    <Layout style={{ minHeight: "100vh", background: 'white'}}>
      <Content style={{
          padding: 12,
          margin: 'auto',
          width: '100%',
          maxWidth: 800,
        }}>
        <ApiTwoTone />
        <Title level={3}>Strava to UKC Integration</Title>
        <Paragraph>Connect your Strava account to UKC to automatically upload your public Strava activities to your UKClimbing and UKHillwalking Activity Diary.</Paragraph>
        <Button
          type="primary"
          href="/api/authorize_strava"
          style={{ background: '#fc4c02', height: 60}}
        >
          <img src='/btn_strava_connectwith_orange.svg' height={48} alt='Connect with STRAVA' />
        </Button>
      </Content>
      <AppFooter />
    </Layout>
  )
}

export default Home