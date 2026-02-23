export interface HomeTimeQuery {
  time_type?: 'month' | 'year' | 'all' | 'custom';
  start_date?: string;
  end_date?: string;
}

export interface HomeStatisticCard {
  inventory_value: number;
  purchase_unreceived: number;
  sale_unreceived: number;
}

export interface HomeTrendChart {
  xAxis: string[];
  revenue_data: number[];
  expend_data: number[];
}

export interface HomePieChartItem {
  name: string;
  value: number;
  proportion: number;
}

export interface HomePieChart {
  purchaser_profit: HomePieChartItem[];
  product_profit: HomePieChartItem[];
}

export interface HomeResponseData {
  statistic_card: HomeStatisticCard;
  trend_chart: HomeTrendChart;
  pie_chart: HomePieChart;
}

export interface HomeData {
  code: number;
  message: string;
  data: HomeResponseData;
}

export interface PageQuery {
  page_num?: number;
  page_size?: number;
}

export interface PageResponse<T> {
  total: number;
  pages: number;
  list: T[];
}

export interface IdNameOption {
  id: number;
  name?: string;
  supplier_name?: string;
  purchaser_name?: string;
  product_name?: string;
}

export interface BaseSuccessResponse {
  code: number;
  message: string;
  data: null;
}

export interface AddIdSuccessResponse {
  code: number;
  message: string;
  data: { id: number };
}

export enum PayStatus {
  UNPAID = 0,
  PAID = 1,
}

export enum InvoiceStatus {
  UNINVOICED = 0,
  INVOICED = 1,
}

export enum PayMethod {
  WECHAT = '微信',
  ALIPAY = '支付宝',
  BANK = '银行卡',
  CASH = '现金',
}

export enum FeeType {
  RENT = '房租',
  WATER_ELECTRIC = '水电',
  LABOR = '人工',
  LOGISTICS = '物流',
  OTHER = '其他',
}

export enum InventoryChangeType {
  PURCHASE_IN = '采购入库',
  SALE_OUT = '销售出库',
  LOSS = '库存报损',
  INIT = '库存初始化',
}

export interface AddSupplierReq {
  supplier_name: string;
  contact_person?: string;
  contact_phone?: string;
  company_address?: string;
  bank_name?: string;
  bank_account?: string;
  tax_no?: string;
  remark?: string;
  avatar_url?: string;
}

export interface UpdateSupplierReq extends AddSupplierReq {
  id: number;
}

export interface SupplierListQuery extends PageQuery {
  supplier_name?: string;
  contact_phone?: string;
}

export interface SupplierItem extends UpdateSupplierReq {
  create_time: string;
  update_time?: string;
  is_deleted?: boolean;
}

export type SupplierListRes = PageResponse<SupplierItem>;
export type SupplierSelectRes = IdNameOption[];

export interface AddPurchaserReq {
  purchaser_name: string;
  contact_person?: string;
  contact_phone?: string;
  company_address?: string;
  receive_address?: string;
  bank_name?: string;
  bank_account?: string;
  tax_no?: string;
  remark?: string;
  avatar?: string;
}

export interface UpdatePurchaserReq extends AddPurchaserReq {
  id: number;
}

export interface PurchaserListQuery extends PageQuery {
  purchaser_name?: string;
  contact_phone?: string;
}

export interface PurchaserItem {
  id: number;
  purchaser_name: string;
  contact_person?: string;
  contact_phone?: string;
  company_address?: string;
  receive_address?: string;
  bank_name?: string;
  bank_account?: string;
  tax_no?: string;
  remark?: string;
  avatar_url?: string;
  create_time: string;
  update_time?: string;
  is_deleted?: boolean;
}

export type PurchaserListRes = PageResponse<PurchaserItem>;
export type PurchaserSelectRes = IdNameOption[];

export interface AddPurchaseInfoReq {
  supplier_id?: number;
  supplier_name: string;
  product_name: string;
  product_spec: string;
  purchase_num: number;
  purchase_price: number;
  purchase_date?: string;
  remark?: string;
}

export interface AddPurchaseInfoRes {
  id: number;
  total_price: number;
}

export interface PurchaseInfoListQuery extends PageQuery {
  supplier_id?: number;
  supplier_name?: string;
  product_name?: string;
  start_date?: string;
  end_date?: string;
  sort_field?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PurchaseInfoItem {
  id: number;
  supplier_id: number;
  supplier_name: string;
  product_name: string;
  product_spec?: string;
  purchase_num: number;
  purchase_price: number;
  total_price: number;
  inventory_cost: number;
  purchase_date: string;
  remark?: string;
  create_time: string;
}

export type PurchaseInfoListRes = PageResponse<PurchaseInfoItem>;

export interface UpdatePurchaseInfoReq extends AddPurchaseInfoReq {
  id: number;
}

export interface LastPurchasePriceQuery {
  supplier_name: string;
  product_name: string;
}

export interface LastPurchasePriceRes {
  purchase_price?: number;
  product_spec?: string;
}

export interface PurchaseBillListQuery extends PageQuery {
  supplier_name?: string;
  pay_status?: PayStatus;
  invoice_status?: InvoiceStatus;
  min_amount?: number;
  max_amount?: number;
}

export interface PurchaseBillItem {
  id: number;
  supplier_id: number;
  supplier_name: string;
  bill_amount: number;
  received_amount: number;
  unreceived_amount: number;
  pay_status: PayStatus;
  pay_status_text: string;
  invoice_status: InvoiceStatus;
  invoice_status_text: string;
}

export type PurchaseBillListRes = PageResponse<PurchaseBillItem>;

export interface PurchaseBillDetailQuery {
  bill_id: number;
  end_date?: string;
}

export interface PurchaseBillDetailItem {
  product_name: string;
  purchase_date: string;
  total_num: number;
  total_price: number;
}

export interface PurchasePayRecordItem {
  id: number;
  pay_date: string;
  pay_amount: number;
  pay_method: PayMethod;
  remark?: string;
}

export interface PurchaseBillDetailRes {
  bill_info: {
    id: number;
    supplier_name: string;
    start_date: string;
    end_date: string | null;
    bill_amount: number;
    received_amount: number;
    unreceived_amount: number;
    pay_status: number;
    invoice_status: number;
    pay_status_text: string;
    invoice_status_text: string;
  };
  purchase_list: PageResponse<PurchaseBillDetailItem>;
  pay_record_list: PageResponse<PurchasePayRecordItem>;
}

export interface AddPurchasePayRecordReq {
  bill_id: number;
  pay_date?: string;
  pay_amount: number;
  pay_method: PayMethod;
  remark?: string;
}

export interface PurchasePayRes {
  pay_status: PayStatus;
}

export interface UpdatePurchaseInvoiceStatusReq {
  bill_id: number;
  invoice_status: InvoiceStatus;
}

export interface AddSaleInfoReq {
  purchaser_name: string;
  product_name: string;
  product_spec: string;
  customer_product_name?: string;
  sale_num: number;
  sale_price: number;
  sale_date?: string;
  delivery_no?: string;
  remark?: string;
}

export interface AddSaleInfoRes {
  id: number;
  total_price: number;
  unit_profit: number;
  total_profit: number;
}

export interface SaleInfoListQuery extends PageQuery {
  purchaser_name?: string;
  product_name?: string;
  customer_product_name?: string;
  start_date?: string;
  end_date?: string;
  sort_field?: string;
  sort_order?: 'asc' | 'desc';
}

export interface SaleInfoItem {
  id: number;
  purchaser_id: number;
  purchaser_name: string;
  product_name: string;
  product_spec: string;
  customer_product_name?: string;
  sale_num: number;
  sale_price: number;
  total_price: number;
  unit_profit: number;
  total_profit: number;
  inventory_cost?: number;
  sale_date: string;
  delivery_no?: string;
  remark?: string;
  create_time: string;
}

export type SaleInfoListRes = PageResponse<SaleInfoItem>;

export interface UpdateSaleInfoReq extends AddSaleInfoReq {
  id: number;
}

export interface SaleProductOption {
  product_name: string;
  customer_product_name?: string;
}
export type SaleProductSelectRes = SaleProductOption[];

export interface LastSalePriceQuery {
  purchaser_name: string;
  product_name: string;
}

export interface LastSalePriceRes {
  sale_price?: number;
  customer_product_name?: string;
  product_spec?: string;
}

export interface SaleBillListQuery extends PageQuery {
  purchaser_name?: string;
  receive_status?: PayStatus;
  invoice_status?: InvoiceStatus;
  min_amount?: number;
  max_amount?: number;
}

export interface SaleBillItem {
  id: number;
  purchaser_id: number;
  purchaser_name: string;
  statement_amount: number;
  total_cost: number;
  total_profit: number;
  received_amount: number;
  unreceived_amount: number;
  receive_status: PayStatus;
  receive_status_text: string;
  invoice_status: InvoiceStatus;
  invoice_status_text: string;
}

export type SaleBillListRes = PageResponse<SaleBillItem>;

export interface SaleBillDetailQuery {
  bill_id: number;
  end_date?: string;
}

export interface SaleBillDetailItem {
  product_name: string;
  customer_product_name?: string;
  sale_date: string;
  total_num: number;
  total_price: number;
  unit_profit: number;
  total_profit: number;
}

export interface SaleReceiveRecordItem {
  id: number;
  receive_date: string;
  receive_amount: number;
  receive_method: PayMethod;
  remark?: string;
}

export interface SaleBillDetailRes {
  bill_info: {
    id: number;
    purchaser_name: string;
    statement_amount: number;
    total_cost: number;
    total_profit: number;
    received_amount: number;
    unreceived_amount: number;
    receive_status_text: string;
    invoice_status_text: string;
    start_date: string | null;
    end_date: string | null;
  };
  sale_list: PageResponse<SaleBillDetailItem>;
  receipt_list: PageResponse<SaleReceiveRecordItem>;
}

export interface AddSaleReceiveRecordReq {
  bill_id: number;
  receive_date?: string;
  receive_amount: number;
  receive_method: PayMethod;
  remark?: string;
}

export interface SaleReceiveRes {
  pay_status: PayStatus;
}

export interface UpdateSaleInvoiceStatusReq {
  bill_id: number;
  invoice_status: InvoiceStatus;
}

export interface InventoryListQuery extends PageQuery {
  product_name?: string;
  min_num?: number;
  max_num?: number;
  sort_field?: string;
  sort_order?: 'asc' | 'desc';
}

export interface InventoryItem {
  product_name: string;
  product_spec: string;
  inventory_num: number;
  inventory_cost: number;
  inventory_value: number;
  last_purchase_date: string;
  last_sale_date?: string;
}

export type InventoryListRes = PageResponse<InventoryItem>;

export interface InventoryDetailQuery extends PageQuery {
  product_name: string;
  product_spec: string;
  start_date?: string;
  end_date?: string;
}

export interface InventoryInfo {
  product_name: string;
  product_spec: string;
  inventory_num: number;
  inventory_cost: number;
  inventory_value: number;
  total_purchase_num: number;
  total_sale_num: number;
}

export interface InventoryChangeRecordItem {
  id: number;
  change_type: InventoryChangeType;
  change_num: number;
  change_date: string;
  related_id: number;
  operator: string;
  remark?: string;
}

export interface InventoryDetailRes {
  inventory_info: InventoryInfo;
  change_record: PageResponse<InventoryChangeRecordItem>;
}

export interface AddInventoryLossReq {
  product_name: string;
  product_spec: string;
  loss_num: number;
  loss_date?: string;
  loss_reason?: string;
}

export interface AddInventoryLossRes {
  id: number;
  loss_cost: number;
}

export interface InventoryLossListQuery extends PageQuery {
  product_name?: string;
  start_date?: string;
  end_date?: string;
}

export interface InventoryLossItem {
  id: number;
  product_name: string;
  product_spec: string;
  loss_num: number;
  loss_cost: number;
  loss_date: string;
  loss_reason?: string;
  create_time: string;
}

export type InventoryLossListRes = PageResponse<InventoryLossItem>;

export interface InventoryWarningQuery extends PageQuery {
  warning_line?: number;
}

export interface InventoryWarningItem {
  product_name: string;
  product_spec: string;
  inventory_num: number;
  warning_line: number;
  last_purchase_date: string;
  supplier_name: string;
}

export type InventoryWarningRes = PageResponse<InventoryWarningItem>;

export interface AddCostFeeReq {
  fee_desc: string;
  fee_amount: number;
  fee_date?: string;
  fee_type: FeeType;
  remark?: string;
}

export interface UpdateCostFeeReq extends AddCostFeeReq {
  id: number;
}

export interface CostFeeListQuery extends PageQuery {
  fee_desc?: string;
  fee_type?: FeeType;
  start_date?: string;
  end_date?: string;
}

export interface CostFeeItem {
  id: number;
  fee_desc: string;
  fee_amount: number;
  fee_date: string;
  fee_type: FeeType;
  fee_type_text: string;
  remark?: string;
  create_time: string;
}

export type CostFeeListRes = PageResponse<CostFeeItem>;

