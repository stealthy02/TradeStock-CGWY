import request from '@/utils/request';
import {
  AddSupplierReq,
  UpdateSupplierReq,
  SupplierListQuery,
  SupplierItem,
  AddPurchaserReq,
  PurchaserItem,
  UpdatePurchaserReq,
  PurchaserListQuery,
  AddIdSuccessResponse,
  BaseSuccessResponse
} from '@/types';

export const getSupplierList = (params?: SupplierListQuery): Promise<{ code: number; message: string; data: { list: SupplierItem[]; total: number; pages: number } }> => {
  return request({
    url: '/basic/supplier/list',
    method: 'get',
    params
  });
};

export const addSupplier = (data: AddSupplierReq): Promise<AddIdSuccessResponse> => {
  return request({
    url: '/basic/supplier/add',
    method: 'post',
    data
  });
};

export const updateSupplier = (data: UpdateSupplierReq): Promise<BaseSuccessResponse> => {
  return request({
    url: '/basic/supplier/update',
    method: 'put',
    data
  });
};

export const deleteSupplier = (params: { id: number }): Promise<BaseSuccessResponse> => {
  return request({
    url: '/basic/supplier/delete',
    method: 'delete',
    params
  });
};

export const getSupplierSelect = (params?: { keyword?: string }): Promise<{ code: number; message: string; data: string[] }> => {
  return request({
    url: '/basic/supplier/select',
    method: 'get',
    params
  });
};

export const getPurchaserList = (params?: PurchaserListQuery): Promise<{ code: number; message: string; data: { list: PurchaserItem[]; total: number; pages: number } }> => {
  return request({
    url: '/basic/purchaser/list',
    method: 'get',
    params
  });
};

export const addPurchaser = (data: AddPurchaserReq): Promise<AddIdSuccessResponse> => {
  return request({
    url: '/basic/purchaser/add',
    method: 'post',
    data
  });
};

export const updatePurchaser = (data: UpdatePurchaserReq): Promise<BaseSuccessResponse> => {
  return request({
    url: '/basic/purchaser/update',
    method: 'put',
    data
  });
};

export const deletePurchaser = (params: { id: number }): Promise<BaseSuccessResponse> => {
  return request({
    url: '/basic/purchaser/delete',
    method: 'delete',
    params
  });
};

export const getPurchaserSelect = (params?: { keyword?: string }): Promise<{ code: number; message: string; data: string[] }> => {
  return request({
    url: '/basic/purchaser/select',
    method: 'get',
    params
  });
};
