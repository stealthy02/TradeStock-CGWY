// 根据环境设置不同的API基础URL
const baseUrl = import.meta.env.VITE_BASE_URL || ''
const apiUrl = import.meta.env.VITE_API_URL || '/api'
export const BASE_URL = baseUrl + apiUrl