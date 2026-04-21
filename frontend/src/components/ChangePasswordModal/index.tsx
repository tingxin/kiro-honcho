import React, { useState } from 'react';
import { Modal, Form, Input, message } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { authService } from '../../services';

interface ChangePasswordModalProps {
  open: boolean;
  onClose: () => void;
}

const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({ open, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const { t } = useTranslation();

  const handleSubmit = async (values: { currentPassword: string; newPassword: string; confirmPassword: string }) => {
    setLoading(true);
    try {
      const success = await authService.changePassword(values.currentPassword, values.newPassword);
      if (success) {
        message.success(t('password.changeSuccess'));
        form.resetFields();
        onClose();
      } else {
        message.error(t('password.changeFailed'));
      }
    } catch {
      message.error(t('password.changeFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={t('password.changeTitle')}
      open={open}
      onCancel={() => { form.resetFields(); onClose(); }}
      onOk={() => form.submit()}
      confirmLoading={loading}
      okText={t('password.confirmChange')}
      cancelText={t('common.cancel')}
    >
      <Form form={form} layout="vertical" onFinish={handleSubmit}>
        <Form.Item name="currentPassword" label={t('password.current')}
          rules={[{ required: true, message: t('password.current') }]}>
          <Input.Password prefix={<LockOutlined />} placeholder={t('password.current')} />
        </Form.Item>
        <Form.Item name="newPassword" label={t('password.new')}
          rules={[{ required: true }, { min: 6, message: t('password.minLength') }]}>
          <Input.Password prefix={<LockOutlined />} placeholder={t('password.new')} />
        </Form.Item>
        <Form.Item name="confirmPassword" label={t('password.confirm')}
          rules={[
            { required: true },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('newPassword') === value) return Promise.resolve();
                return Promise.reject(new Error(t('password.mismatch')));
              },
            }),
          ]}>
          <Input.Password prefix={<LockOutlined />} placeholder={t('password.confirm')} />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ChangePasswordModal;
