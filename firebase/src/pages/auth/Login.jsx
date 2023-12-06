import React, {useState} from 'react'
import { getAuth, sendSignInLinkToEmail } from "firebase/auth";
import { UserOutlined } from '@ant-design/icons';
import { Input, Button } from 'antd';
import { useNavigate } from "react-router-dom";


const Login = () => {

  const defaultEmail = window.localStorage.getItem('emailForSignIn') || '';

  const [email, setEmail] = useState(defaultEmail);

  const navigate = useNavigate();

  const actionCodeSettings = {
      // URL you want to redirect back to. The domain (www.example.com) for this
      // URL must be in the authorized domains list in the Firebase Console.
      url: 'https://strava-ukc.web.app/completelogin',
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
        // ask user to check email for link
        alert("Please check your email for the link to log in")
        navigate("/");
      })
      .catch((error) => {
        console.log(error);
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