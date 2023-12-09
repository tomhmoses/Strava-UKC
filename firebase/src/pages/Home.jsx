import React from 'react'
import { Typography, Layout, Button, App } from 'antd';
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
    return <div>Loading...</div>;
  }
  if (error) {
    return <div>Error: {JSON.stringify(error)}</div>;
  }
  if (user) {
    return (
      <Layout style={{ minHeight: "100vh" }}>
        <AppHeader />
        <Content><UserHome firestore={props.firestore} functions={props.functions} user={user}/></Content>
        <AppFooter />
      </Layout>
    )
  }
  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Content>
        <Title level={3}>Strava to UKC</Title>
        <Paragraph>Connect your Strava account to UKC to automatically upload your public Strava activities to your UKClimbing and UKHillwalking Activity Dairy.</Paragraph>
        <a href="/api/authorize_strava">
          <img src='/btn_strava_connectwith_orange@2x.png' height={48} />
        </a>
      </Content>
      <AppFooter />
    </Layout>
  )
}

export default Home