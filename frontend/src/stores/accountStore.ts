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
      set({ 
        accounts: response.accounts, 
        currentAccount: response.accounts.length > 0 ? response.accounts[0] : null,
        isLoading: false 
      })
    } catch (error) {
      set({ isLoading: false })
      console.error('Failed to fetch accounts:', error)
    }
  },
}))
