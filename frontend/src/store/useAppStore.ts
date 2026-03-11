// 应用状态管理
import { create } from 'zustand'

interface AppState {
  // 应用状态
  isLoading: boolean
  currentUser: {
    id: string
    name: string
  } | null
  
  // 操作方法
  setLoading: (loading: boolean) => void
  setCurrentUser: (user: { id: string; name: string } | null) => void
  resetState: () => void
}

export const useAppStore = create<AppState>((set) => ({
  // 初始状态
  isLoading: false,
  currentUser: null,
  
  // 操作方法
  setLoading: (loading) => set({ isLoading: loading }),
  setCurrentUser: (user) => set({ currentUser: user }),
  resetState: () => set({
    isLoading: false,
    currentUser: null
  })
}))
