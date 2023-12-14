import { useState } from 'react'
import { Typography, Form, Button, Alert, DatePicker, Steps, Space, message, Input, Progress, Spin } from 'antd';
import { getAuth } from "firebase/auth";
import { useAuthState } from 'react-firebase-hooks/auth';
import { doc } from 'firebase/firestore';
import { useDocumentData } from 'react-firebase-hooks/firestore';
import { httpsCallable } from "firebase/functions";
import PropTypes from "prop-types";
import { json } from "react-router-dom";

const { Title, Paragraph } = Typography;
const { RangePicker } = DatePicker;

const UploadPrev = (props) => {

  const auth = getAuth();
  const [user, loading, error] = useAuthState(auth);
  const userRef = doc(props.firestore, "users", user?.uid || 'a');
  const [data] = useDocumentData(userRef);

  const [form] = Form.useForm();
  const [loginForm] = Form.useForm();
  const [current, setCurrent] = useState(0);
  const [buttonLoading, setButtonLoading] = useState(false);
  const [completed, setCompleted] = useState(false);
  if (current == 2 && (data?.prev_upload_progress || 0) == (data?.prev_upload_goal || 1) && !completed) {
    setCompleted(true);
  }

  const [numActivities, setNumActivities] = useState(0);
  const percent = ((data?.prev_upload_progress || 0) / (data?.prev_upload_goal || 1))*100;

  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(0);

  const [errorText, setErrorText] = useState('');

  const onNext = async (values) => {
    setButtonLoading(true);
    const range = values.range;
    // start time in variable
    const rangeStart = range[0].startOf('day').unix();
    // end time in variable
    const rangeEnd = range[1].endOf('day').unix();

    setStart(rangeStart);
    setEnd(rangeEnd);
    const preview_activities = httpsCallable(props.functions, 'preview_previous_activities');
    await preview_activities({after: rangeStart, before: rangeEnd}).then((result) => {
      // console.log(result.data);
      setNumActivities(result.data.number);
      setCurrent(1);
      setButtonLoading(false);
    });
  };

  const onConfirm = async () => {
    setButtonLoading(true);
    const upload_activities = httpsCallable(props.functions, 'upload_previous_activities');
    const ukcUsername = loginForm.getFieldValue('ukcUsername');
    const ukcPassword = loginForm.getFieldValue('ukcPassword');
    await upload_activities({after: start, before: end, ukcUsername: ukcUsername, ukcPassword: ukcPassword, numActivities: numActivities}).then((result) => {
      // console.log(result.data);
      if (result.data.success) {
        if (result.data.status === 'complete') {
          setCompleted(true);
        }
      } else {
        message.error('There was an error uploading your activities.');
        setErrorText(result.data.error);
      }
      setCurrent(2);
      setButtonLoading(false);
    }).catch((error) => {
      console.log(error);
      message.error('There was an error uploading your activities.');
      setErrorText(error.message);
      setCurrent(2);
      setButtonLoading(false);
    });
  };

  const reset = () => {
    setCurrent(0);
    setButtonLoading(false);
    setNumActivities(0);
    setStart(0);
    setEnd(0);
    setErrorText('');
    setCompleted(false);
    form.resetFields();
  };
    

  const stepItems = [
    {
      title: 'Select date range',
      key: 'range',
    },
    {
      title: 'Confirm activities',
      key: 'confirm',
    },
    {
      title: 'Upload',
      key: 'upload',
    },
  ];


  if (loading) {
    return <Spin />;
  }
  if (error) {
    return <div>Error: {JSON.stringify(error)}</div>;
  }
  if (user) {
    return (
      <>
        <Typography>
          <Title>Upload previous activities</Title>
          <Paragraph>
            This page allows you to upload/update any activities from Strava in a given date range to your UKC Activity Diary.
          </Paragraph>
          <Paragraph>
            Some information such as activity description will be set to blank (even if it already exists).
          </Paragraph>
        </Typography>
        <br />
        <br />
        <Paragraph>
          <Steps current={current} items={stepItems} status={(completed)? 'finish' : (errorText? 'error': 'process')}/>
        </Paragraph>
        {current === 0 && 
          <Form 
            form={form}
            layout="vertical"
            onFinish={onNext}
          >
            <Form.Item
              name="range"
              label="Date range"
              rules={[
                { required: true, message: 'Please select a date range.' },
              ]}
            >
              <RangePicker />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={buttonLoading}>
                Next
              </Button>
            </Form.Item>
          </Form>
        }
        {current === 1 && <>
          <Paragraph>
            {numActivities}{(numActivities === 200)? '+': ''} activities will be uploaded to UKC.
          </Paragraph>
          {!data?.auto_upload && <>
            <Paragraph>
              Since you have not enabled auto upload, you will need to provide your UKC login details to upload these activities. They will be deleted after the upload is complete.
            </Paragraph>
            <Form
              layout='vertical'
              form={loginForm}
            >
              <Form.Item 
                label="UKC Email or Username"
                name="ukcUsername"
                rules={[
                  { required: true, message: 'Please enter your UKC username.' },
                ]}
              >
                <Input />
              </Form.Item>
              <Form.Item 
                label="UKC Password"
                name="ukcPassword"
                rules={[
                  { required: true, message: 'Please enter your UKC password.' },
                ]}
              >
                <Input.Password />
              </Form.Item>
            </Form>
          </>}
          <Space direction="horizontal">
            <Button type="primary" onClick={onConfirm} loading={buttonLoading}>
              Confirm
            </Button>
            <Button onClick={() => setCurrent(0)}>
              Back
            </Button>
          </Space>
        </>}
        {current === 2 && <>
          <Paragraph>
            {errorText && <Alert message={errorText} type="error" />}
            {errorText && <br />}
            {(!completed || ((data?.prev_upload_progress || 0) == (data?.prev_upload_goal || numActivities))) &&
              <Progress percent={percent} format={() => `${data?.prev_upload_progress} /  ${data?.prev_upload_goal}`}/>
            }
            {!errorText && !completed &&
              <Paragraph>
                Uploading activities...
              </Paragraph>
            }
            {completed &&<Button type="primary" onClick={reset}>
              Upload more
            </Button>}
          </Paragraph>
        </>}
      </>
    )
  } else {
    throw json({message: 'You must be logged in to view this page.'},{status: 401})
  }
}

UploadPrev.propTypes = {
  firestore: PropTypes.object,
  functions: PropTypes.object,
};

export default UploadPrev