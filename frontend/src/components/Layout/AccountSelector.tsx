import React from 'react';
import { Select, Space } from 'antd';
import { CloudServerOutlined } from '@ant-design/icons';
import { AWSAccount } from '../../services/accounts';

const { Option } = Select;

interface AccountSelectorProps {
  accounts: AWSAccount[];
  currentAccount: AWSAccount | null;
  onSelect?: (account: AWSAccount) => void;
}

const AccountSelector: React.FC<AccountSelectorProps> = ({ accounts, currentAccount, onSelect }) => {
  return (
    <Select
      style={{ width: 250 }}
      placeholder="选择 AWS 账号"
      value={currentAccount?.id}
      onChange={(value) => {
        const account = accounts.find(a => a.id === value);
        if (account && onSelect) {
          onSelect(account);
        }
      }}
    >
      {accounts.map((account) => (
        <Option key={account.id} value={account.id}>
          <Space>
            <CloudServerOutlined />
            {account.name}
          </Space>
        </Option>
      ))}
    </Select>
  );
};

export default AccountSelector;
