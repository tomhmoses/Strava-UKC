import { Typography, Button, Spin } from 'antd';
import { getAuth } from "firebase/auth";
import { useAuthState } from 'react-firebase-hooks/auth';
import UserHome from './UserHome';
import PropTypes from "prop-types";

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
      <UserHome firestore={props.firestore} functions={props.functions} user={user}/>
    )
  }
  return (
    <>
      <Title level={3}>Strava to UKC Integration</Title>
      <Paragraph>Connect your Strava account to UKC to automatically upload your public Strava activities to your UKClimbing and UKHillwalking Activity Diary.</Paragraph>
      <Button
        type="primary"
        href="/api/authorize_strava"
        style={{ background: '#fc4c02', height: 64}}
      >
        <img src='/btn_strava_connectwith_orange.svg' height={48} alt='Connect with STRAVA' />
      </Button>
    </>
  )
}

Home.propTypes = {
  firestore: PropTypes.object,
  functions: PropTypes.object,
};

export default Home