import { getAuth, signInWithCustomToken } from "firebase/auth";
import { Button, Result, Spin } from 'antd';
import { useNavigate } from "react-router-dom";
import { useState } from "react";


export default function CompleteLogin() {

  const navigate = useNavigate();
  const [error, setError] = useState(false)

  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  const token = urlParams.get('token')
  // if we have a token, login
  if (error) {
    return (
      <Result 
        status="error"
        title="Login Failed"
        subTitle={error.message}
        extra={
          <Button href="/">Login</Button>
        }
      />
    )
  }
  if (token) {
    const auth = getAuth();
    signInWithCustomToken(auth, token)
      .then(() => {
        window.history.pushState(null, "", window.location.href.split("?")[0]);
        navigate("/");
      })
      .catch((error) => {
        setError(error);
      });
  } else {
    return (
      <Result 
        status="error"
        title="Login Failed"
        subTitle="No token was provided"
        extra={
          <Button href="/">Login</Button>
        }
      />
    )
  }
  
  return (<Spin />);
}