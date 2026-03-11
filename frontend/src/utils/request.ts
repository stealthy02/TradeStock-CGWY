// src/utils/request.ts
import axios from 'axios';
import { message } from 'ant-design-vue';

import { BASE_URL } from '@/env';

const request = axios.create({
  baseURL: BASE_URL,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json;charset=utf-8'
  }
});

// 请求拦截器（不变，按需加token）
request.interceptors.request.use(
  (config) => {
    // const token = localStorage.getItem('token');
    // if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => {
    console.error('请求错误：', error);
    return Promise.reject(error);
  }
);

// 响应拦截器：核心修改【msg → message】，匹配接口文档
request.interceptors.response.use(
  (response) => {
    if (response.config.responseType === 'blob') {
      return response;
    }
    const res = response.data;
    if (res.code !== 200) {
      message.error(res.message || '请求失败');
      return Promise.reject(new Error(res.message || '请求失败'));
    }
    return res;
  },
  (error) => {
    console.error('响应错误：', error);
    message.error(error.message || '网络异常，请稍后再试');
    return Promise.reject(error);
  }
);

export default request;