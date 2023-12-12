import React from 'react';
import { getAuth, signInWithCustomToken } from "firebase/auth";
import { Spin } from 'antd';
import { useNavigate } from "react-router-dom";


export default function CompleteLogin() {

  const navigate = useNavigate();

  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  const token = urlParams.get('token')
  // if we have a token, login
  if (token) {
    const auth = getAuth();
    signInWithCustomToken(auth, token)
      .then((userCredential) => {
        window.history.pushState(null, "", window.location.href.split("?")[0]);
        navigate("/");
      })
  }

  return (<Spin />)
}