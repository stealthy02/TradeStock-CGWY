import request from '@/utils/request';
import {
  InventoryListQuery,
  InventoryListRes,
  InventoryDetailQuery,
  InventoryDetailRes,
  AddInventoryLossReq,
  AddInventoryLossRes,
  InventoryLossListQuery,
  InventoryLossListRes,
  InventoryWarningQuery,
  InventoryWarningRes,
  BaseSuccessResponse
} from '@/types';

// ===================================== 库存信息查询 =====================================
/** 分页查询当前库存列表 */
export const getInventoryList = (params?: InventoryListQuery): Promise<{ code: number; message: string; data: InventoryListRes }> => {
  return request({
    url: '/inventory/list',
    method: 'get',
    params
  });
};

/** 单个商品库存详情+变动记录（必传product_name） */
export const getInventoryDetail = (params: InventoryDetailQuery): Promise<{ code: number; message: string; data: InventoryDetailRes }> => {
  return request({
    url: '/inventory/detail',
    method: 'get',
    params
  });
};

// ===================================== 库存报损相关 =====================================
/** 新增库存报损（校验库存，同步扣减库存） */
export const addInventoryLoss = (data: AddInventoryLossReq): Promise<{ code: number; message: string; data: AddInventoryLossRes }> => {
  return request({
    url: '/inventory/loss/add',
    method: 'post',
    data
  });
};

/** 分页查询库存报损列表 */
export const getInventoryLossList = (params?: InventoryLossListQuery): Promise<{ code: number; message: string; data: InventoryLossListRes }> => {
  return request({
    url: '/inventory/loss/list',
    method: 'get',
    params
  });
};

/** 删除库存报损记录（Query传id，恢复库存） */
export const deleteInventoryLoss = (params: { id: number }): Promise<BaseSuccessResponse> => {
  return request({
    url: '/inventory/loss/delete',
    method: 'delete',
    params
  });
};

// ===================================== 库存预警/盘点 =====================================
/** 查询库存预警列表（低于预警线商品，默认预警线5） */
export const getInventoryWarningList = (params?: InventoryWarningQuery): Promise<{ code: number; message: string; data: InventoryWarningRes }> => {
  return request({
    url: '/inventory/warning',
    method: 'get',
    params
  });
};