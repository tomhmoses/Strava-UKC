import { Form, Input, Modal, Alert } from 'antd';
import PropTypes from "prop-types";

const SetUpUKC = ({ open, onCreate, onCancel, defaultUsername, error, confirmLoading }) => {
  const [form] = Form.useForm();
  return (
    <Modal
      open={open}
      title="Connect UKC Account"
      okText="Confirm"
      cancelText="Cancel"
      onCancel={onCancel}
      confirmLoading={confirmLoading}
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
      {error && <Alert message={error} type="error" />}
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

SetUpUKC.propTypes = {
  open: PropTypes.bool,
  onCreate: PropTypes.func,
  onCancel: PropTypes.func,
  defaultUsername: PropTypes.string,
  error: PropTypes.string,
  confirmLoading: PropTypes.bool,
};

export default SetUpUKC;