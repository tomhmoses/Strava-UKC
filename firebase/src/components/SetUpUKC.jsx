import React from 'react';
import { Form, Input, Modal, Radio } from 'antd';


const SetUpUKC = ({ open, onCreate, onCancel, defaultUsername }) => {
    const [form] = Form.useForm();
    return (
      <Modal
        open={open}
        title="Connect UKC Account"
        okText="Confirm"
        cancelText="Cancel"
        onCancel={onCancel}
        onOk={() => {
          form
            .validateFields()
            .then((values) => {
              form.resetFields();
              onCreate(values);
            })
            .catch((info) => {
              console.log('Validate Failed:', info);
            });
        }}
      >
        <Form
          form={form}
          layout="vertical"
          name="form_in_modal"
          initialValues={{
            modifier: 'public',
          }}
        >
          <Form.Item 
            label="UKC Username or Email"
            name="username"
            initialValue={defaultUsername}
            rules={[
              { 
                required: true, 
                message: 'Enter your username or email' 
              }
            ]}
          >
            <Input />
          </Form.Item>
          <Form.Item 
            label="UKC Password"
            name="password"
            rules={[
              { 
                required: true, 
                message: 'Enter your password' 
              }
            ]}
          >
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>
    );
  };

export default SetUpUKC;