import React, { useState } from 'react'
import { Typography, Form, Input, Switch, Button } from 'antd';
import { doc } from 'firebase/firestore';
import { useDocumentData } from 'react-firebase-hooks/firestore';
import SetUpUKC from '../components/SetUpUKC';
import { getFunctions, httpsCallable } from "firebase/functions";

const { Title, Paragraph } = Typography;

const UserHome = (props) => {

  const userRef = doc(props.firestore, "users", props.user.uid);
  const [data] = useDocumentData(userRef);
  console.log(data);

  const [modalVisible, setModalVisible] = useState(false);
  const [switchLoading, setSwitchLoading] = useState(false);

  const onCreate = (values) => {
    console.log('Received values of form: ', values);
    // call function to set UKC username and password
    // function is called set_up_UKC_auth and is a firebase function
    // it takes the username and password and sets them in the database
    // it also checks the login is valid
    // it returns {'success': True} if it worked else it returns an error

    // call firebase function
    // const setUpUKCAuth = props.functions.httpsCallable('set_up_UKC_auth');
    const functions = getFunctions();
    const setUpUKCAuth = httpsCallable(functions, 'set_up_UKC_auth');
    setUpUKCAuth(values).then((result) => {
      console.log(result.data);
      if (result.data.success) {
        // set the username in the database
        userRef.set({
          ukc_username: values.username,
          auto_upload: true
        }, { merge: true });
      } else {
        // show error message
        console.log(result.data.error);
      }
    });
    setModalVisible(false);
    setSwitchLoading(false);
  }; 
  const onCancel = () => {
    setModalVisible(false);
    // toggle switch back to false
    form.setFieldsValue({ukcAutoUpload: false});
    setSwitchLoading(false);
  };

  const [form] = Form.useForm();
  // const [username, setUsername] = useState(data?.ukc_username || '');
  // const [autoUpload, setAutoUpload] = useState(data?.auto_upload || false);
  const onToggle = (changedValues, allValues) => {
    // This should open the modal to set up UKC account if changed to true
    console.log(changedValues);
    console.log(allValues);
    if (allValues.ukcAutoUpload) {
      console.log("open modal");
      setModalVisible(true);
      setSwitchLoading(true);
    }

  };

  return (
    <>
    <Title level={1}>Home</Title>
    {!data && <Title level={3}>Loading account data...</Title>}
    {data &&
      <>
        <SetUpUKC open={modalVisible} onCreate={onCreate} onCancel={onCancel} defaultUsername={data?.ukc_username || ''} />
        {!data.firstname && <Title level={3}>
          User data is incomplete.
        </Title>}
        {data.firstname && <Title level={3}>Welcome {data.firstname}</Title>}
        <Paragraph>
          How does this work? Good question. I'm not sure yet, but it'll probably be something like this:
        </Paragraph>
        <Paragraph>
          <ol>
            <li>Sign in with Strava ✅</li>
            <li>Any activity updates get sent to this app ✅</li>
            <li>Choose how you want to filter activities to go to UKC/UKH</li>
            <li>2 options now:</li>
            <ul>
              <li>You can trust this site with your UKC/UKH login detials (they dont have an API 😔) and it can automatically add your activities to your UKC/UKH Activity Dairy (after an optional delay)</li>
              <li>You can get an export of activties, ready to load into a local script that uploads them to UKC/UKH.</li>
            </ul>
          </ol>
        </Paragraph>
        <Title level={2}>Set up UKC Auto Upload</Title>
        <Paragraph>
          To automatically upload your activities to UKC, you need to give this app your UKC login details. These will be stored securely, and only used to upload activities to UKC.
        </Paragraph>
        <Form
          layout='vertical'
          form={form}
          onValuesChange={onToggle}
        >
          <Form.Item 
            label="Enable UKC Auto Upload"
            name="ukcAutoUpload"
            valuePropName="checked"
            initialValue={data?.auto_upload || false}
            
          >
            {/* set loading if modal is open */}
            <Switch loading={switchLoading} />
          </Form.Item>
        </Form>

      </>
    }
    </>
  )
}

export default UserHome