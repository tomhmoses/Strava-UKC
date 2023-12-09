import React, { useState } from 'react'
import { Typography, Form, Switch, message, Alert } from 'antd';

import { doc } from 'firebase/firestore';
import { useDocumentData } from 'react-firebase-hooks/firestore';
import SetUpUKC from '../components/SetUpUKC';
import { httpsCallable } from "firebase/functions";

const { Title, Paragraph } = Typography;

const UserHome = (props) => {

  const userRef = doc(props.firestore, "users", props.user.uid);
  const [data] = useDocumentData(userRef);
  console.log(data);

  const [modalVisible, setModalVisible] = useState(false);
  const [switchLoading, setSwitchLoading] = useState(false);

  const [error, setError] = useState('');
  const [modalSubmitLoading, setModalSubmitLoading] = useState(false);

  const onCreate = async (values) => {
    console.log('Received values of form: ', values);
    setError('');
    setModalSubmitLoading(true);
    // call function to set UKC username and password
    // function is called set_up_UKC_auth and is a firebase function
    // it takes the username and password and sets them in the database
    // it also checks the login is valid
    // it returns {'success': True} if it worked else it returns an error

    // call firebase function
    const setUpUKCAuth = httpsCallable(props.functions,'set_up_UKC_auth');
    await setUpUKCAuth(values).then((result) => {
      console.log(result.data);
      if (result.data.success) {
        // show success message
        console.log("success");
        message.success('UKC account connected successfully');
        setModalSubmitLoading(false);
        setModalVisible(false);
        setSwitchLoading(false);
      } else if (result.data.error === "Incorrect UKC username or password.") {
        // show error message
        console.log("wrong username or password");
        // show this in the model
        setError("The username or password is incorrect.");
        setModalSubmitLoading(false);
      }
    });
  }; 
  const onCancel = () => {
    setModalVisible(false);
    // toggle switch back to false
    form.setFieldsValue({ukcAutoUpload: false});
    setSwitchLoading(false);
    setError('');
    setModalSubmitLoading(false);
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
    } else {
      setSwitchLoading(true);
      // call firebase function to remove UKC username and password
      const disableUpload = httpsCallable(props.functions,'disable_auto_upload');
      disableUpload().then((result) => {
        console.log(result.data);
        if (result.data.success) {
          // show success message
          console.log("success");
          setSwitchLoading(false);
          message.success('UKC auto upload disabled and login authentication deleted');
        }
      });
    }

  };

  return (
    <>
    {!data && <Title level={3}>Loading account data...</Title>}
    {data &&
      <>
        <SetUpUKC open={modalVisible} onCreate={onCreate} onCancel={onCancel} defaultUsername={data?.ukc_username || ''} error={error} confirmLoading={modalSubmitLoading} />
        {!data.firstname && <Title level={3}>
          User data is incomplete.
        </Title>}
        {data.firstname && <Title level={1}>Welcome {data.firstname}</Title>}
        <Paragraph>
          This integration allows you to automatically upload your Strava activities to your UKC/UKH Activity Diary.
        </Paragraph>
        <Paragraph>
          <ul>
            <li>You can trust this site with your UKC/UKH login detials (they dont have an API 😔) and public Strava Activities wil be uploaded and updated for you.</li>
            <li>Or you can get an export of activties, ready to load into a local script that uploads them to UKC/UKH.</li>
          </ul>
        </Paragraph>
        <Title level={2}>Set up UKC Auto Upload</Title>
        <Paragraph>
          To automatically upload your activities to UKC, you need to give this app your UKC login details. These will be stored securely, and only used to upload activities to UKC.
        </Paragraph>
        {data.auto_upload_error && <Alert message={data.auto_upload_error} type="error" />}
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
        {data.auto_upload && 
          <Paragraph>
            UKC Auto Upload is enabled. Your public activities on Strava will be uploaded to UKC automatically.
          </Paragraph>
        }
      </>
    }
    </>
  )
}

export default UserHome