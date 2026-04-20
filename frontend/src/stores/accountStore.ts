import { create } from 'zustand'
import { accountService, AWSAccount } from '../services/accounts'

interface AccountState {
  currentAccount: AWSAccount | null
  accounts: AWSAccount[]
  isLoading: boolean
  setCurrentAccount: (account: AWSAccount | null) => void
  setAccounts: (accounts: AWSAccount[]) => void
  fetchAccounts: () => Promise<void>
}

export const useAccountStore = create<AccountState>((set) => ({
  currentAccount: null,
  accounts: [],
  isLoading: false,

  setCurrentAccount: (account) =>
    set({ currentAccount: account }),

  setAccounts: (accounts) =>
    set({ accounts, currentAccount: accounts.length > 0 ? accounts[0] : null }),

  fetchAccounts: async () => {
    set({ isLoading: true })
    try {
      const response = await accountService.list()
      const accounts = response.accounts
      // 优先选择默认账号
      const defaultAccount = accounts.find(a => a.is_default) || (accounts.length > 0 ? accounts[0] : null)
      set({
        accounts,
        currentAccount: defaultAccount,
        isLoading: false
      })
    } catch (error) {
      set({ isLoading: false })
      console.error('Failed to fetch accounts:', error)
    }
  },
}))
