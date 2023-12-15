import { useState } from 'react'
import { Typography, Form, Switch, message, Alert, Skeleton } from 'antd';

import { doc } from 'firebase/firestore';
import { useDocumentData } from 'react-firebase-hooks/firestore';
import SetUpUKC from '../components/SetUpUKC';
import { httpsCallable } from "firebase/functions";
import PropTypes from "prop-types";

const { Title, Paragraph } = Typography;

const UserHome = (props) => {

  const userRef = doc(props.firestore, "users", props.user.uid);
  const [data] = useDocumentData(userRef);

  const [modalVisible, setModalVisible] = useState(false);
  const [switchLoading, setSwitchLoading] = useState(false);
  const [gpxSwitchLoading, setGPXSwitchLoading] = useState(false);

  const [error, setError] = useState('');
  const [modalSubmitLoading, setModalSubmitLoading] = useState(false);

  const onCreate = async (values) => {
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
      if (result.data.success) {
        message.success('UKC account connected successfully');
        setModalSubmitLoading(false);
        setModalVisible(false);
        setSwitchLoading(false);
      } else if (result.data.error === "Incorrect UKC username or password.") {
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
  const onToggle = (changedValues) => {
    // This should open the modal to set up UKC account if changed to true
    // if changedValues contains ukcAutoUpload and is changed to true
    if ('ukcAutoUpload' in changedValues && changedValues.ukcAutoUpload === true){
      setModalVisible(true);
      setSwitchLoading(true);
    } else if ('ukcAutoUpload' in changedValues && changedValues.ukcAutoUpload === false) {
      setSwitchLoading(true);
      // call firebase function to remove UKC username and password
      const disableUpload = httpsCallable(props.functions,'disable_auto_upload');
      disableUpload().then((result) => {
        if (result.data.success) {
          // show success message
          setSwitchLoading(false);
          message.success('UKC auto upload disabled and login authentication deleted');
        }
      });
    }
    if ('uploadGPX' in changedValues && changedValues.uploadGPX === true){
      setGPXSwitchLoading(true);
      const enableGPXUpload = httpsCallable(props.functions,'enable_gpx_upload');
      enableGPXUpload().then((result) => {
        if (result.data.success) {
          setGPXSwitchLoading(false);
          message.success('GPX upload enabled');
        } else if (result.data.error === "Must be UKC Supporter to upload GPX.") {
          setGPXSwitchLoading(false);
          form.setFieldsValue({uploadGPX: false});
          message.error('You must be a UKC Supporter to upload GPX.');
        }
      });
    } else if ('uploadGPX' in changedValues && changedValues.uploadGPX === false) {
      setGPXSwitchLoading(true);
      const disableGPXUpload = httpsCallable(props.functions,'disable_gpx_upload');
      disableGPXUpload().then((result) => {
        if (result.data.success) {
          // show success message
          setGPXSwitchLoading(false);
          message.success('GPX upload disabled');
        }
      });
    }

  };

  return (
    <>
    {!data && <Skeleton active />}
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
            <li>You can trust this site with your UKC/UKH login detials (they dont have an API yet...) and public Strava Activities wil be uploaded and updated for you.</li>
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
            <Switch loading={switchLoading} aria-label='Enable UKC Auto Upload'/>
          </Form.Item>
          {data.auto_upload &&
            // switch for GPX upload
            <Form.Item 
              label="Upload GPX to UKC"
              name="uploadGPX"
              valuePropName="checked"
              initialValue={data?.gpx_upload || false}
            >
              <Switch loading={gpxSwitchLoading} aria-label='Upload GPX to UKC'/>
            </Form.Item>
          }

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

UserHome.propTypes = {
  firestore: PropTypes.object,
  functions: PropTypes.object,
  user: PropTypes.object,
};

export default UserHome