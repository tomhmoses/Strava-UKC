import { HomeTwoTone, CheckCircleTwoTone, ClockCircleTwoTone } from '@ant-design/icons';
import { Menu, Layout } from 'antd';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import PropTypes from "prop-types";
const { Header } = Layout;

const AppHeader = (props) => {
  // TODO: fix for when first page is not home
  const [current, setCurrent] = useState((window.location.href.includes('upload-previous'))? 'u' : 'h');
  const onClick = (e) => {
    setCurrent(e.key);
  };
  return (
    <Header style={{padding: "0"}}>
      <Menu onClick={onClick} selectedKeys={[current]} mode="horizontal">
      <Menu.Item key="h" icon= {<HomeTwoTone />}>
        <Link to="/">Home</Link>
      </Menu.Item>
      <Menu.Item key="u" icon= {<ClockCircleTwoTone />}>
        <Link to="/upload-previous">Upload previous activities</Link>
      </Menu.Item>
      <Menu.Item key="l" icon= {<CheckCircleTwoTone />} onClick={props.logout}>
        <Link to="/">Logout</Link>
      </Menu.Item>
      </Menu>
    </Header>
  );
};

AppHeader.propTypes = {
  logout: PropTypes.func,
};

export default AppHeader;
