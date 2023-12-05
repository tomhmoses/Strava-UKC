import { HomeTwoTone, EditTwoTone, CheckCircleTwoTone } from '@ant-design/icons';
import { Menu } from 'antd';
import { useState } from 'react';
import { Outlet, Link } from 'react-router-dom';
// use auth from firebase
import { getAuth, signOut } from "firebase/auth";
import { useAuthState } from 'react-firebase-hooks/auth';



const Header = () => {
  const [current, setCurrent] = useState('h');
  const onClick = (e) => {
    console.log('click ', e);
    setCurrent(e.key);
  };

  const logout = () => {
    signOut(auth);
  };

  const auth = getAuth();
  const [user, loading, error] = useAuthState(auth);


  return (
    <>
     <Menu onClick={onClick} selectedKeys={[current]} mode="horizontal">
      <Menu.Item key="h" icon= {<HomeTwoTone />}>
       <Link to="/">Home</Link>
      </Menu.Item>
      {!loading && !error && !user &&
        <Menu.Item key="l" icon= {<CheckCircleTwoTone />}>
          <Link to="/login">Login</Link>
        </Menu.Item>
      }
      {!loading && !error && user &&
        <Menu.Item key="l" icon= {<CheckCircleTwoTone />} onClick={logout}>
          <Link to="/">Logout</Link>
        </Menu.Item>
      }
     </Menu>
     <Outlet/>
    </>
   
  )
};
export default Header;