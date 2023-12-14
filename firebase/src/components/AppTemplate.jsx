import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import AppFooter from './AppFooter';
import AppHeader from './AppHeader';
import PropTypes from "prop-types";
const { Content } = Layout;

const AppTemplate = (props) => {

  return (
    <Layout style={{ minHeight: "100vh", background: 'white'}}>
      {props.user && 
        <AppHeader logout={props.logout}/>
      }
      <Content style={{
        padding: 12,
        margin: 'auto',
        width: '100%',
        maxWidth: 800,
      }}>
        <Outlet/>
      </Content>
      <AppFooter/>
    </Layout>
  )
};

AppTemplate.propTypes = {
  user: PropTypes.object,
  logout: PropTypes.func,
};

export default AppTemplate;