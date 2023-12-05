import React, {useState} from 'react'
import { getAuth, sendSignInLinkToEmail } from "firebase/auth";
import { UserOutlined } from '@ant-design/icons';
import { Input, Button } from 'antd';


const Login = () => {

  const [email, setEmail] = useState('');

  const actionCodeSettings = {
      // URL you want to redirect back to. The domain (www.example.com) for this
      // URL must be in the authorized domains list in the Firebase Console.
      url: 'strava-ukc.web.app',
      // This must be true.
      handleCodeInApp: true,
    };

  const auth = getAuth();
  const handleClick = () => {
    if(email !== '') {
      sendSignInLinkToEmail(auth, email, actionCodeSettings)
      .then(() => {
        // The link was successfully sent. Inform the user.
        // Save the email locally so you don't need to ask the user for it again
        // if they open the link on the same device.
        window.localStorage.setItem('emailForSignIn', email);
        // ...
      })
      .catch((error) => {
        const errorCode = error.code;
        const errorMessage = error.message;
        // ...
      });
    } else {
      alert("Please enter an email address")
    }
  };

  const handleChange = (e) => {
    setEmail(e.target.value)
  }
      

  return (
    <>
        <Input placeholder="default size" prefix={<UserOutlined />} value={email} onChange={handleChange}/>
        <Button type="primary" onClick={handleClick}>Log In</Button>
    </>
  )
}

export default Login