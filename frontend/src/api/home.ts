// src/api/home.ts
import request from '@/utils/request';
import { HomeTimeQuery, HomeStatisticCard, HomePieChart, HomeTrendChart } from '@/types';

// 获取数字卡片数据
export const getStatisticCard = (params?: HomeTimeQuery): Promise<{ code: number; message: string; data: HomeStatisticCard }> => {
  return request({
    url: '/home/statistic-card',
    method: 'get',
    params
  });
};

// 获取饼状图数据
export const getPieChart = (params?: HomeTimeQuery): Promise<{ code: number; message: string; data: HomePieChart }> => {
  return request({
    url: '/home/pie-chart',
    method: 'get',
    params
  });
};

// 获取趋势图数据
export const getTrendChart = (params?: HomeTimeQuery): Promise<{ code: number; message: string; data: HomeTrendChart }> => {
  return request({
    url: '/home/trend-chart',
    method: 'get',
    params
  });
};

// 获取首页核心数据
export const getHomeData = (params?: HomeTimeQuery): Promise<{ code: number; message: string; data: any }> => {
  return request({
    url: '/home/data',
    method: 'get',
    params
  });
};