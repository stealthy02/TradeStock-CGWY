import request from '@/utils/request';
import {
  AddCostFeeReq,
  CostFeeListQuery,
  CostFeeListRes,
  UpdateCostFeeReq,
  AddIdSuccessResponse,
  BaseSuccessResponse
} from '@/types';

// ===================================== 运营杂费相关接口 =====================================
/** 新增运营杂费 */
export const addCostFee = (data: AddCostFeeReq): Promise<AddIdSuccessResponse> => {
  return request({
    url: '/cost/fee/add',
    method: 'post',
    data
  });
};

/** 分页查询运营杂费列表 */
export const getCostFeeList = (params?: CostFeeListQuery): Promise<{ code: number; message: string; data: CostFeeListRes }> => {
  return request({
    url: '/cost/fee/list',
    method: 'get',
    params
  });
};

/** 修改运营杂费信息 */
export const updateCostFee = (data: UpdateCostFeeReq): Promise<BaseSuccessResponse> => {
  return request({
    url: '/cost/fee/update',
    method: 'put',
    data
  });
};

/** 删除运营杂费记录（Query传id） */
export const deleteCostFee = (params: { id: number }): Promise<BaseSuccessResponse> => {
  return request({
    url: '/cost/fee/delete',
    method: 'delete',
    params
  });
};