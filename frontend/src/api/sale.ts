import request from '@/utils/request';
import {
  AddSaleInfoReq,
  AddSaleInfoRes,
  SaleInfoListQuery,
  SaleInfoListRes,
  UpdateSaleInfoReq,
  LastSalePriceQuery,
  LastSalePriceRes,
  SaleBillListQuery,
  SaleBillListRes,
  SaleBillDetailQuery,
  SaleBillDetailRes,
  AddSaleReceiveRecordReq,
  SaleReceiveRes,
  UpdateSaleInvoiceStatusReq,
  BaseSuccessResponse
} from '@/types';

export const addSaleInfo = (data: AddSaleInfoReq): Promise<{ code: number; message: string; data: AddSaleInfoRes }> => {
  return request({
    url: '/sale/info/add',
    method: 'post',
    data
  });
};

export const getSaleInfoList = (params?: SaleInfoListQuery): Promise<{ code: number; message: string; data: SaleInfoListRes }> => {
  return request({
    url: '/sale/info/list',
    method: 'get',
    params
  });
};

export const updateSaleInfo = (data: UpdateSaleInfoReq): Promise<BaseSuccessResponse> => {
  return request({
    url: '/sale/info/update',
    method: 'put',
    data
  });
};

export const deleteSaleInfo = (params: { id: number }): Promise<BaseSuccessResponse> => {
  return request({
    url: '/sale/info/delete',
    method: 'delete',
    params
  });
};

export const getSaleProductSelect = (params?: { keyword?: string }): Promise<{ code: number; message: string; data: string[] }> => {
  return request({
    url: '/sale/info/product_select',
    method: 'get',
    params
  });
};

export const getLastSalePrice = (params: LastSalePriceQuery): Promise<{ code: number; message: string; data: LastSalePriceRes }> => {
  return request({
    url: '/sale/info/last_record',
    method: 'get',
    params
  });
};

export const getSaleBillList = (params?: SaleBillListQuery): Promise<{ code: number; message: string; data: SaleBillListRes }> => {
  return request({
    url: '/sale/bill/list',
    method: 'get',
    params
  });
};

export const getSaleBillDetail = (params: SaleBillDetailQuery): Promise<{ code: number; message: string; data: SaleBillDetailRes }> => {
  return request({
    url: '/sale/bill/detail',
    method: 'get',
    params
  });
};

export const addSaleReceiveRecord = (data: AddSaleReceiveRecordReq): Promise<{ code: number; message: string; data: SaleReceiveRes }> => {
  return request({
    url: '/sale/bill/receive',
    method: 'post',
    data
  });
};

export const updateSaleInvoiceStatus = (data: UpdateSaleInvoiceStatusReq): Promise<BaseSuccessResponse> => {
  return request({
    url: '/sale/bill/update_invoice_status',
    method: 'put',
    data
  });
};

/** 删除销售收款记录 */
export const deleteSaleReceipt = (params: { receive_id: number }): Promise<{ code: number; message: string; data: any }> => {
  return request({
    url: '/sale/bill/receive/delete',
    method: 'delete',
    params
  });
};

/** 导出销售对账单 */
export const exportSaleBill = (params: SaleBillDetailQuery): Promise<Blob> => {
  return request({
    url: '/sale/bill/export',
    method: 'get',
    params,
    responseType: 'blob'
  }).then(res => res.data);
};
