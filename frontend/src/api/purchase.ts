import request from '@/utils/request';
import {
  AddPurchaseInfoReq,
  AddPurchaseInfoRes,
  PurchaseInfoListQuery,
  PurchaseInfoListRes,
  UpdatePurchaseInfoReq,
  LastPurchasePriceQuery,
  LastPurchasePriceRes,
  PurchaseBillListQuery,
  PurchaseBillListRes,
  PurchaseBillDetailQuery,
  PurchaseBillDetailRes,
  AddPurchasePayRecordReq,
  PurchasePayRes,
  UpdatePurchaseInvoiceStatusReq,
  BaseSuccessResponse
} from '@/types';

// ===================================== 采购信息相关接口 =====================================
/** 新增采购信息 */
export const addPurchaseInfo = (data: AddPurchaseInfoReq): Promise<{ code: number; message: string; data: AddPurchaseInfoRes }> => {
  return request({
    url: '/purchase/info/add',
    method: 'post',
    data
  });
};

/** 分页查询采购信息列表 */
export const getPurchaseInfoList = (params?: PurchaseInfoListQuery): Promise<{ code: number; message: string; data: PurchaseInfoListRes }> => {
  return request({
    url: '/purchase/info/list',
    method: 'get',
    params
  });
};

/** 修改采购信息 */
export const updatePurchaseInfo = (data: UpdatePurchaseInfoReq): Promise<BaseSuccessResponse> => {
  return request({
    url: '/purchase/info/update',
    method: 'put',
    data
  });
};

/** 删除采购信息（Query传id） */
export const deletePurchaseInfo = (params: { id: number }): Promise<BaseSuccessResponse> => {
  return request({
    url: '/purchase/info/delete',
    method: 'delete',
    params
  });
};

/** 采购商品下拉联想（keyword可选，为空返回前5条） */
export const selectPurchaseProduct = (params?: { keyword?: string }): Promise<{ code: number; message: string; data: string[] }> => {
  return request({
    url: '/purchase/info/product_select',
    method: 'get',
    params
  });
};

/** 获取上一次采购单价（必传supplier_id+product_name） */
export const getLastPurchasePrice = (params: LastPurchasePriceQuery): Promise<{ code: number; message: string; data: LastPurchasePriceRes }> => {
  return request({
    url: '/purchase/info/last_record',
    method: 'get',
    params
  });
};

// ===================================== 采购对账单相关接口 =====================================
/** 分页查询采购对账单列表 */
export const getPurchaseBillList = (params?: PurchaseBillListQuery): Promise<{ code: number; message: string; data: PurchaseBillListRes }> => {
  return request({
    url: '/purchase/bill/list',
    method: 'get',
    params
  });
};

/** 查看采购对账单细则（必传bill_id） */
export const getPurchaseBillDetail = (params: PurchaseBillDetailQuery): Promise<{ code: number; message: string; data: PurchaseBillDetailRes }> => {
  return request({
    url: '/purchase/bill/detail',
    method: 'get',
    params
  });
};

/** 录入采购付款记录 */
export const addPurchasePayRecord = (data: AddPurchasePayRecordReq): Promise<{ code: number; message: string; data: PurchasePayRes }> => {
  return request({
    url: '/purchase/bill/pay',
    method: 'post',
    data
  });
};

/** 修改采购对账单开票状态 */
export const updatePurchaseInvoiceStatus = (data: UpdatePurchaseInvoiceStatusReq): Promise<BaseSuccessResponse> => {
  return request({
    url: '/purchase/bill/update_invoice_status',
    method: 'put',
    data
  });
};

/** 删除采购付款记录 */
export const deletePurchasePayment = (params: { payment_id: number }): Promise<{ code: number; message: string; data: any }> => {
  return request({
    url: '/purchase/bill/pay/delete',
    method: 'delete',
    params
  });
};

/** 导出采购对账单 */
export const exportPurchaseBill = (params: PurchaseBillDetailQuery): Promise<Blob> => {
  return request({
    url: '/purchase/bill/export',
    method: 'get',
    params,
    responseType: 'blob'
  }).then(res => res.data);
};