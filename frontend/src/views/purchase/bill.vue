<template>
  <div class="page-container">
    <h1>采购对账单管理</h1>
    

    
    <!-- 高级搜索栏 -->
    <a-form
      v-if="showSearch"
      :model="searchParams"
      layout="inline"
      style="margin-bottom: 16px; padding: 16px; background: #fafafa; border-radius: 8px"
    >
      <a-form-item label="供货商名称">
        <a-select
          v-model:value="searchParams.supplier_name"
          placeholder="请选择供货商"
          show-search
          :filter-option="false"
          :options="supplierOptions"
          @search="handleSupplierSearch"
          style="width: 200px"
        />
      </a-form-item>

      <a-form-item label="结款状态">
        <a-select
          v-model:value="searchParams.pay_status"
          placeholder="请选择结款状态"
          style="width: 150px"
        >
          <a-select-option value="">全部</a-select-option>
          <a-select-option :value="0">未结清</a-select-option>
          <a-select-option :value="1">已结清</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="开票状态">
        <a-select
          v-model:value="searchParams.invoice_status"
          placeholder="请选择开票状态"
          style="width: 150px"
        >
          <a-select-option value="">全部</a-select-option>
          <a-select-option :value="0">未开票</a-select-option>
          <a-select-option :value="1">已开票</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="对账金额范围">
        <a-input-group compact>
          <a-input-number
            v-model:value="searchParams.min_amount"
            placeholder="最小"
            :min="0"
            :step="0.01"
            :precision="2"
            style="width: 100px"
          />
          <span style="margin: 0 8px">-</span>
          <a-input-number
            v-model:value="searchParams.max_amount"
            placeholder="最大"
            :min="0"
            :step="0.01"
            :precision="2"
            style="width: 100px"
          />
        </a-input-group>
      </a-form-item>
      <a-form-item>
        <a-button type="primary" @click="fetchData">查询</a-button>
        <a-button style="margin-left: 8px" @click="resetSearch">重置</a-button>
        <a-button style="margin-left: 8px" @click="handleExport">导出</a-button>
      </a-form-item>
    </a-form>
    
    <a-checkbox v-model:checked="showSearch" style="margin-bottom: 16px">显示搜索栏</a-checkbox>
    
    <!-- 数据表格 -->
    <a-table
      :columns="columns"
      :data-source="dataSource"
      :row-key="(record) => record.id"
      :pagination="{
        showSizeChanger: true,
        pageSizeOptions: ['10', '20', '50', '100'],
        showTotal: (total) => `共 ${total} 条记录`,
        current: searchParams.page_num,
        pageSize: searchParams.page_size,
        onChange: handlePageChange,
        onShowSizeChange: handlePageSizeChange
      }"
      :scroll="{ x: 1200 }"
      :loading="loading"
    />
    
    <!-- 查看细则抽屉 -->
    <a-drawer
      title="采购对账单细则"
      placement="right"
      :width="800"
      :open="detailDrawerVisible"
      @close="detailDrawerVisible = false"
    >
      <template #extra>
        <a-button type="primary" @click="handleExportSubmit">导出</a-button>
      </template>
      <div v-if="currentBill">
        <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #f0f0f0">
          <p><strong>供货商名称：</strong>{{ currentBill.supplier_name || '-' }}</p>
          <p><strong>对账开始日期：</strong>{{ currentBill.start_date || '-' }}</p>
          <p><strong>对账结束日期：</strong>
            <template v-if="!currentBill.end_date">
              <a-date-picker
                v-model:value="tempEndDate"
                format="YYYY-MM-DD"
                style="width: 150px; margin-left: 8px"
                :disabled-date="confirmDisabledDate"
                @change="handleEndDateChange"
              />
            </template>
            <template v-else>{{ currentBill.end_date }}</template>
          </p>
          <p><strong>对账金额：</strong>{{ previewBillAmount ? previewBillAmount.toFixed(2) : (currentBill.bill_amount ? currentBill.bill_amount.toFixed(2) : '0.00') }} 元</p>
          <p><strong>已付金额：</strong>{{ currentBill.received_amount ? currentBill.received_amount.toFixed(2) : '0.00' }} 元</p>
          <p><strong>未付金额：</strong>{{ previewUnreceivedAmount ? previewUnreceivedAmount.toFixed(2) : (currentBill.unreceived_amount ? currentBill.unreceived_amount.toFixed(2) : '0.00') }} 元</p>
          <div style="margin-top: 16px">
            <a-button 
              v-if="!currentBill.end_date" 
              type="primary" 
              @click="handleConfirmStatement(currentBill)"
            >
              确认对账单
            </a-button>
            <a-button 
              v-else 
              type="default" 
              @click="handleUnconfirmStatement(currentBill)"
            >
              撤销确认
            </a-button>
          </div>
        </div>
        
        <!-- 采购明细 -->
        <div style="margin-bottom: 24px">
          <h3>采购明细</h3>
          <a-table
            :columns="detailColumns"
            :data-source="purchaseDetailList"
            :row-key="(record) => record.id"
            :pagination="{
              showSizeChanger: true,
              pageSizeOptions: ['10', '20', '50'],
              showTotal: (total) => `共 ${total} 条记录`,
              current: detailPageNum,
              pageSize: detailPageSize,
              onChange: handleDetailPageChange,
              onShowSizeChange: handleDetailPageSizeChange
            }"
            :loading="detailLoading"
          />
        </div>
        
        <!-- 付款记录 -->
        <div>
          <h3>付款记录</h3>
          <a-table
            :columns="payRecordColumns"
            :data-source="payRecordList"
            :row-key="(record) => record.id"
            :pagination="false"
          >
            <template #empty>
              <p>暂无付款记录</p>
            </template>
          </a-table>
        </div>
      </div>
    </a-drawer>
    
    <!-- 录入付款弹窗 -->
    <a-modal
      v-model:open="payModalVisible"
      title="录入付款"
      width="600px"
      destroyOnClose
    >
      <a-form
        ref="payFormRef"
        :model="payFormData"
        :rules="payFormRules"
        layout="vertical"
      >
        <a-form-item label="付款日期" name="pay_date">
          <a-date-picker
            v-model:value="payFormData.pay_date"
            format="YYYY-MM-DD"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="付款金额" name="pay_amount">
          <a-input-number
            v-model:value="payFormData.pay_amount"
            :min="0.01"
            :step="0.01"
            :precision="2"
            placeholder="请输入付款金额"
            style="width: 100%"
          />
          <div v-if="payAmountError" style="color: #ff4d4f; font-size: 12px; margin-top: 4px">
            {{ payAmountError }}
          </div>
        </a-form-item>
        <a-form-item label="付款方式" name="pay_method">
          <a-select
            v-model:value="payFormData.pay_method"
            placeholder="请选择付款方式"
            style="width: 100%"
            :options="payMethodOptions"
            :not-found-content="'输入新的付款方式后按回车'"
            @search="handlePayMethodSearch"
            @change="handlePayMethodChange"
          />
        </a-form-item>
        <a-form-item label="付款备注" name="remark">
          <a-textarea
            v-model:value="payFormData.remark"
            :rows="4"
            :maxLength="200"
            placeholder="请输入付款备注"
          />
        </a-form-item>
      </a-form>
      <template #footer>
        <div class="modal-footer">
          <a-button @click="payModalVisible = false">取消</a-button>
          <a-button type="primary" @click="handlePaySubmit">确定</a-button>
        </div>
      </template>
    </a-modal>
    
    <!-- 修改开票状态确认弹窗 -->
    <a-modal
      v-model:open="invoiceModalVisible"
      :title="invoiceModalTitle"
      @ok="handleInvoiceStatusUpdate"
      @cancel="invoiceModalVisible = false"
    >
      <p>{{ invoiceModalContent }}</p>
    </a-modal>
    
    <!-- 删除付款记录确认弹窗 -->
    <a-modal
      v-model:open="deleteModalVisible"
      title="删除付款记录"
      @ok="handleDeletePayRecordConfirm"
      @cancel="deleteModalVisible = false"
    >
      <p>{{ deleteModalContent }}</p>
    </a-modal>
    

    
    <!-- 确认对账单弹窗 -->
    <a-modal
      v-model:open="confirmModalVisible"
      title="确认采购对账单"
      width="600px"
      @ok="handleConfirmStatementSubmit"
      @cancel="confirmModalVisible = false"
    >
      <p>确定要确认此对账单吗？结束日期将使用细则中选择的日期。</p>
    </a-modal>
    
    <!-- 删除对账单确认弹窗 -->
    <a-modal
      v-model:open="deleteStatementModalVisible"
      title="删除对账单"
      @ok="handleDeleteStatementConfirm"
      @cancel="deleteStatementModalVisible = false"
    >
      <p>{{ deleteStatementModalContent }}</p>
    </a-modal>
    
    <!-- 取消确认对账单弹窗 -->
    <a-modal
      v-model:open="unconfirmModalVisible"
      title="取消确认采购对账单"
      @ok="handleUnconfirmStatementSubmit"
      @cancel="unconfirmModalVisible = false"
    >
      <p>{{ unconfirmModalContent }}</p>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, h } from 'vue';
import { message, Tag } from 'ant-design-vue';
import dayjs from 'dayjs';
import { getPurchaseBillList, getPurchaseBillDetail, addPurchasePayRecord, updatePurchaseInvoiceStatus, exportPurchaseBill } from '@/api/purchase';
import { getSupplierSelect } from '@/api/basic';
import request from '@/utils/request';

// 搜索相关
const showSearch = ref(true);
const supplierOptions = ref([]);
const searchParams = reactive({
  page_num: 1,
  page_size: 10,
  supplier_name: undefined,
  pay_status: undefined,
  invoice_status: undefined,
  min_amount: undefined,
  max_amount: undefined
});

// 表格相关
const dataSource = ref([]);
const total = ref(0);
const loading = ref(false);

// 查看细则相关
const detailDrawerVisible = ref(false);
const currentBill = ref(null);
const purchaseDetailList = ref([]);
const payRecordList = ref([]);
const detailLoading = ref(false);
const detailPageNum = ref(1);
const detailPageSize = ref(10);

// 录入付款相关
const payModalVisible = ref(false);
const payFormRef = ref(null);
const payFormData = reactive({
  bill_id: undefined,
  pay_date: dayjs(),
  pay_amount: undefined,
  pay_method: undefined,
  remark: ''
});
const payAmountError = ref('');
const payMethodOptions = ref([
  { label: '微信', value: '微信' },
  { label: '支付宝', value: '支付宝' },
  { label: '银行卡', value: '银行卡' },
  { label: '现金', value: '现金' }
]);
const payFormRules = reactive({
  pay_date: [{ required: true, message: '请选择付款日期', trigger: 'change' }],
  pay_amount: [
    { required: true, message: '请输入付款金额', trigger: 'blur', type: 'number' },
    { type: 'number', min: 0.01, message: '付款金额必须为正数', trigger: 'blur' }
  ],
  pay_method: [{ required: true, message: '请选择付款方式', trigger: 'change' }]
});

// 修改开票状态相关
const invoiceModalVisible = ref(false);
const invoiceModalTitle = ref('修改开票状态');
const invoiceModalContent = ref('');
const invoiceStatusUpdateData = reactive({
  bill_id: undefined,
  invoice_status: 0
});

// 删除付款记录相关
const deleteModalVisible = ref(false);
const deleteModalContent = ref('');
const deletePaymentId = ref(undefined);

const confirmModalVisible = ref(false);
const confirmStatementId = ref(undefined);

// 删除对账单相关
const deleteStatementModalVisible = ref(false);
const deleteStatementModalContent = ref('');
const deleteStatementId = ref(undefined);

// 取消确认相关
const unconfirmModalVisible = ref(false);
const unconfirmModalContent = ref('');
const unconfirmStatementId = ref(undefined);

// 临时结束日期和预览数据
const tempEndDate = ref(null);
const previewBillAmount = ref(null);
const previewUnreceivedAmount = ref(null);

// 表格列定义
const columns = [
  {
    title: '供货商名称',
    dataIndex: 'supplier_name',
    key: 'supplier_name',
    sorter: true,
    ellipsis: true
  },
  {
    title: '起始日期',
    dataIndex: 'start_date',
    key: 'start_date',
    sorter: true,
    ellipsis: true,
    customRender: function(opt) {
      return opt.record.start_date || '-';
    }
  },
  {
    title: '结束日期',
    dataIndex: 'end_date',
    key: 'end_date',
    sorter: true,
    ellipsis: true,
    customRender: function(opt) {
      return opt.record.end_date || '未确定';
    }
  },
  {
    title: '对账金额',
    dataIndex: 'bill_amount',
    key: 'bill_amount',
    sorter: true,
    ellipsis: true,
    customRender: function(opt) {
      return opt.record.bill_amount ? opt.record.bill_amount.toFixed(2) : '0.00';
    }
  },
  {
    title: '已付金额',
    dataIndex: 'received_amount',
    key: 'received_amount',
    sorter: true,
    ellipsis: true,
    customRender: function(opt) {
      return opt.record.received_amount ? opt.record.received_amount.toFixed(2) : '0.00';
    }
  },
  {
    title: '未付金额',
    dataIndex: 'unreceived_amount',
    key: 'unreceived_amount',
    sorter: true,
    ellipsis: true,
    customRender: function(opt) {
      return opt.record.unreceived_amount ? opt.record.unreceived_amount.toFixed(2) : '0.00';
    }
  },
  {
    title: '结款状态',
    dataIndex: 'pay_status',
    key: 'pay_status',
    sorter: true,
    ellipsis: true,
    customRender: function(opt) {
      return opt.record.pay_status === 1 ? 
        h(Tag, { color: 'success' }, () => '已结清') : 
        h(Tag, { color: 'error' }, () => '未结清');
    }
  },
  {
    title: '开票状态',
    dataIndex: 'invoice_status',
    key: 'invoice_status',
    sorter: true,
    ellipsis: true,
    customRender: function(opt) {
      return opt.record.invoice_status === 1 ? 
        h(Tag, { color: 'blue' }, () => '已开票') : 
        h(Tag, { color: 'default' }, () => '未开票');
    }
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right',
    width: 250,
    customRender: function(opt) {
      const record = opt.record;
      const isConfirmed = !!record.end_date;
      return h('div', [
        h('span', {
          style: {
            display: 'inline-block',
            marginRight: '8px',
            cursor: 'pointer',
            color: '#1890ff'
          },
          onClick: () => handleViewDetail(record)
        }, '查看细则'),
        h('span', {
          style: {
            display: 'inline-block',
            marginRight: '8px',
            cursor: 'pointer',
            color: '#1890ff',
            opacity: !isConfirmed || record.pay_status === 1 ? 0.5 : 1,
            pointerEvents: !isConfirmed || record.pay_status === 1 ? 'none' : 'auto'
          },
          onClick: () => handleOpenPayModal(record)
        }, '录入付款'),
        h('span', {
          style: {
            display: 'inline-block',
            marginRight: '8px',
            cursor: 'pointer',
            color: '#1890ff',
            opacity: !isConfirmed ? 0.5 : 1,
            pointerEvents: !isConfirmed ? 'none' : 'auto'
          },
          onClick: () => handleOpenInvoiceModal(record)
        }, '修改开票状态')
      ]);
    }
  }
];

// 细则表格列定义
const detailColumns = [
  {
    title: '商品名称',
    dataIndex: 'product_name',
    key: 'product_name',
    ellipsis: true
  },
  {
    title: '采购日期',
    dataIndex: 'purchase_date',
    key: 'purchase_date',
    ellipsis: true
  },
  {
    title: '总公斤数',
    dataIndex: 'total_kg',
    key: 'total_kg',
    ellipsis: true
  },
  {
    title: '单价',
    dataIndex: 'unit_price',
    key: 'unit_price',
    ellipsis: true,
    customRender: function(opt) {
      return opt.record.unit_price ? opt.record.unit_price.toFixed(2) : '0.00';
    }
  },
  {
    title: '采购总价',
    dataIndex: 'total_price',
    key: 'total_price',
    ellipsis: true,
    customRender: function(opt) {
      return opt.record.total_price.toFixed(2);
    }
  },
  {
    title: '备注',
    dataIndex: 'remark',
    key: 'remark',
    ellipsis: true,
    customRender: function(opt) {
      return opt.record.remark || '-';
    }
  }
];

// 付款记录表格列定义
const payRecordColumns = [
  {
    title: '付款日期',
    dataIndex: 'pay_date',
    key: 'pay_date',
    ellipsis: true
  },
  {
    title: '付款金额',
    dataIndex: 'pay_amount',
    key: 'pay_amount',
    ellipsis: true,
    customRender: function(opt) {
      return opt.record.pay_amount.toFixed(2);
    }
  },
  {
    title: '付款方式',
    dataIndex: 'pay_method',
    key: 'pay_method',
    ellipsis: true
  },
  {
    title: '备注',
    dataIndex: 'remark',
    key: 'remark',
    ellipsis: true,
    customRender: function(opt) {
      return opt.record.remark || '-';
    }
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right',
    width: 100,
    customRender: function(opt) {
      const record = opt.record;
      return h('span', {
        style: {
          display: 'inline-block',
          cursor: 'pointer',
          color: '#ff4d4f'
        },
        onClick: () => handleDeletePayRecord(record)
      }, '删除');
    }
  }
];

// 获取采购对账单列表
const fetchData = async () => {
  loading.value = true;
  try {
    const response = await getPurchaseBillList(searchParams);
    dataSource.value = response.data.list;
    total.value = response.data.total;
  } catch (error) {
    console.error('获取采购对账单列表失败:', error);
    message.error('获取数据失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 分页处理
const handlePageChange = (page) => {
  searchParams.page_num = page;
  fetchData();
};

const handlePageSizeChange = (_, pageSize) => {
  searchParams.page_size = pageSize;
  searchParams.page_num = 1;
  fetchData();
};

// 重置搜索
const resetSearch = () => {
  searchParams.page_num = 1;
  searchParams.page_size = 10;
  searchParams.supplier_name = undefined;
  searchParams.pay_status = undefined;
  searchParams.invoice_status = undefined;
  searchParams.min_amount = undefined;
  searchParams.max_amount = undefined;
  fetchData();
};

// 导出功能
const handleExport = () => {
  message.info('请在细则中点击导出按钮');
};

const handleExportSubmit = async () => {
  if (!currentBill.value) {
    message.error('请先选择对账单');
    return;
  }

  try {
    const params = {
      bill_id: currentBill.value.id
    };

    if (tempEndDate.value) {
      params.end_date = tempEndDate.value.format('YYYY-MM-DD');
    }

    const blob = await exportPurchaseBill(params);
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const fileName = `采购对账单_${currentBill.value.supplier_name}_${dayjs().format('YYYYMMDDHHmmss')}.xlsx`;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    message.success('导出成功');
  } catch (error) {
    console.error('导出失败:', error);
    message.error('导出失败，请稍后重试');
  }
};

// 供货商搜索
const handleSupplierSearch = async (value) => {
  if (!value) return;
  try {
    const response = await getSupplierSelect({ keyword: value });
    supplierOptions.value = response.data.map(name => ({
      label: name,
      value: name
    }));
  } catch (error) {
    console.error('获取供货商列表失败:', error);
  }
};

// 查看细则
const handleViewDetail = async (record) => {
  currentBill.value = record;
  detailDrawerVisible.value = true;
  tempEndDate.value = dayjs();
  previewBillAmount.value = null;
  previewUnreceivedAmount.value = null;
  await fetchBillDetail(record.id, record.supplier_id);
};

// 获取对账单细则
const fetchBillDetail = async (billId, supplierId) => {
  detailLoading.value = true;
  try {
    const params = {
      bill_id: billId
    };
    
    // 如果是无对账单的记录，需要传递supplier_id
    if (billId === 0 && supplierId) {
      params.supplier_id = supplierId;
    }
    
    // 如果有临时结束日期，传递end_date参数
    if (tempEndDate.value) {
      params.end_date = tempEndDate.value.format('YYYY-MM-DD');
    }
    
    const response = await getPurchaseBillDetail(params);
    purchaseDetailList.value = response.data.purchase_list.list;
    payRecordList.value = response.data.pay_record_list.list;
    // 更新当前账单信息，确保显示正确
    if (response.data.bill_info) {
      currentBill.value = response.data.bill_info;
      // 更新预览金额
      previewBillAmount.value = response.data.bill_info.bill_amount;
      previewUnreceivedAmount.value = response.data.bill_info.unreceived_amount;
    }
  } catch (error) {
    console.error('获取采购对账单细则失败:', error);
    message.error('获取细则失败，请稍后重试');
    // 发生错误时设置默认值
    purchaseDetailList.value = [];
    payRecordList.value = [];
  } finally {
    detailLoading.value = false;
  }
};

// 细则分页处理
const handleDetailPageChange = (page) => {
  detailPageNum.value = page;
  if (currentBill.value) {
    fetchBillDetail(currentBill.value.id);
  }
};

const handleDetailPageSizeChange = (_, pageSize) => {
  detailPageSize.value = pageSize;
  detailPageNum.value = 1;
  if (currentBill.value) {
    fetchBillDetail(currentBill.value.id);
  }
};

// 打开录入付款弹窗
const handleOpenPayModal = (record) => {
  if (record.pay_status === 1) {
    message.warning('该对账单已全部结清，无需再次付款');
    return;
  }
  
  payFormData.bill_id = record.id;
  payFormData.pay_date = dayjs();
  payFormData.pay_amount = undefined;
  payFormData.pay_method = undefined;
  payFormData.remark = '';
  payAmountError.value = '';
  payModalVisible.value = true;
};

// 付款方式搜索
const handlePayMethodSearch = (value) => {
  if (!value) return;
  // 添加用户输入作为选项
  const exists = payMethodOptions.value.some(option => option.value === value);
  if (!exists) {
    payMethodOptions.value = [
      { label: value, value: value },
      ...payMethodOptions.value
    ];
  }
};

// 付款方式变更
const handlePayMethodChange = (value) => {
  payFormData.pay_method = value;
};

// 提交付款
const handlePaySubmit = async () => {
  if (!payFormRef.value) return;
  
  try {
    await payFormRef.value.validate();
    
    if (currentBill.value && payFormData.pay_amount && payFormData.pay_amount > currentBill.value.unreceived_amount) {
      message.error(`付款金额不可超过未付金额${currentBill.value.unreceived_amount.toFixed(2)}元`);
      return;
    }
    
    const submitData = {
      ...payFormData,
      pay_date: dayjs.isDayjs(payFormData.pay_date) ? payFormData.pay_date.format('YYYY-MM-DD') : payFormData.pay_date
    };
    
    const response = await addPurchasePayRecord(submitData);
    message.success('付款成功！');
    
    if (response.data.pay_status === 1) {
      message.success('该对账单已全部结清');
    }
    
    payModalVisible.value = false;
    fetchData();
    
    if (currentBill.value) {
      fetchBillDetail(currentBill.value.id);
    }
    
    // 重新初始化付款方式选项
    payMethodOptions.value = [
      { label: '微信', value: '微信' },
      { label: '支付宝', value: '支付宝' },
      { label: '银行卡', value: '银行卡' },
      { label: '现金', value: '现金' }
    ];
  } catch (error) {
    console.error('提交付款失败:', error);
    message.error('提交失败，请稍后重试');
  }
};

// 打开修改开票状态弹窗
const handleOpenInvoiceModal = (record) => {
  invoiceStatusUpdateData.bill_id = record.id;
  
  if (record.invoice_status === 0) {
    invoiceModalTitle.value = '标记为已开票';
    invoiceModalContent.value = `确定将${record.supplier_name}的采购对账单标记为已开票吗？`;
    invoiceStatusUpdateData.invoice_status = 1;
  } else {
    invoiceModalTitle.value = '标记为未开票';
    invoiceModalContent.value = `确定将${record.supplier_name}的采购对账单标记为未开票吗？`;
    invoiceStatusUpdateData.invoice_status = 0;
  }
  
  invoiceModalVisible.value = true;
};

// 更新开票状态
const handleInvoiceStatusUpdate = async () => {
  if (!invoiceStatusUpdateData.bill_id) return;
  
  try {
    await updatePurchaseInvoiceStatus(invoiceStatusUpdateData);
    message.success('开票状态更新成功');
    invoiceModalVisible.value = false;
    fetchData();
  } catch (error) {
    console.error('更新开票状态失败:', error);
    message.error('更新失败，请稍后重试');
  }
};

// 打开删除付款记录弹窗
const handleDeletePayRecord = (record) => {
  deletePaymentId.value = record.id;
  deleteModalContent.value = `确定要删除这条付款记录吗？付款金额：${record.pay_amount.toFixed(2)}元，付款日期：${record.pay_date}`;
  deleteModalVisible.value = true;
};

// 确认删除付款记录
const handleDeletePayRecordConfirm = async () => {
  if (!deletePaymentId.value) return;
  
  try {
    await request({
      url: '/purchase/bill/pay/delete',
      method: 'delete',
      params: {
        payment_id: deletePaymentId.value
      }
    });
    message.success('付款记录删除成功');
    deleteModalVisible.value = false;
    
    // 重新获取对账单细则和列表数据
    if (currentBill.value) {
      await fetchBillDetail(currentBill.value.id);
    }
    fetchData();
  } catch (error) {
    console.error('删除付款记录失败:', error);
    message.error('删除失败，请稍后重试');
  }
};



// 打开确认对账单弹窗
const handleConfirmStatement = (bill) => {
  if (!tempEndDate.value) {
    message.warning('请先在细则中选择对账结束日期');
    return;
  }
  confirmStatementId.value = bill.id;
  confirmModalVisible.value = true;
};

// 确认日期范围
const confirmDisabledDate = (current) => {
  if (!currentBill.value || !currentBill.value.start_date) return false;
  const startDate = dayjs(currentBill.value.start_date);
  return current && current < startDate;
};

// 处理结束日期变化
const handleEndDateChange = async (date) => {
  if (!date || !currentBill.value) return;
  
  tempEndDate.value = date;
  
  // 重新获取对账单细则，会自动传递end_date参数
  await fetchBillDetail(currentBill.value.id, currentBill.value.supplier_id);
};

// 提交确认对账单
const handleConfirmStatementSubmit = async () => {
  if (!confirmStatementId.value) return;
  
  try {
    const endDate = dayjs.isDayjs(tempEndDate.value) ? tempEndDate.value.format('YYYY-MM-DD') : tempEndDate.value;
    
    let submitData;
    
    if (confirmStatementId.value === 0) {
      const supplierName = currentBill.value.supplier_name;
      if (!supplierName) {
        message.error('无法获取供货商信息，请稍后重试');
        return;
      }
      
      const lastStatementResponse = await request({
        url: '/purchase/statement/last',
        method: 'get',
        params: {
          supplier_name: supplierName
        }
      });
      
      const startDate = lastStatementResponse.data.next_start_date || endDate;
      
      await request({
        url: '/purchase/statement/create',
        method: 'post',
        data: {
          supplier_name: supplierName,
          start_date: startDate
        }
      });
      
      await fetchData();
      
      const latestBill = dataSource.value.find(item => 
        item.supplier_name === supplierName && !item.end_date
      );
      
      if (!latestBill) {
        message.error('无法找到新创建的对账单，请稍后重试');
        return;
      }
      
      submitData = {
        statement_id: latestBill.id,
        end_date: endDate
      };
    } else {
      submitData = {
        statement_id: confirmStatementId.value,
        end_date: endDate
      };
    }
    
    await request({
      url: '/purchase/statement/confirm',
      method: 'post',
      data: submitData
    });
    
    message.success('对账单确认成功');
    confirmModalVisible.value = false;
    fetchData();
    
    if (currentBill.value) {
      await fetchBillDetail(currentBill.value.id, currentBill.value.supplier_id);
    }
  } catch (error) {
    console.error('确认对账单失败:', error);
    message.error('确认失败，请稍后重试');
  }
};

// 打开删除对账单弹窗
const handleDeleteStatement = async (record) => {
  if (!record.end_date) return;
  
  try {
    // 检查该对账单是否是该供货商的最近一次已确定对账单
    const response = await request({
      url: '/purchase/statement/last',
      method: 'get',
      params: {
        supplier_name: record.supplier_name
      }
    });
    
    if (response.data && response.data.id && response.data.id !== record.id) {
      message.warning('只能删除每个供货商已确定的最近一次对账单');
      return;
    }
    
    deleteStatementId.value = record.id;
    deleteStatementModalContent.value = `确定要删除这个对账单吗？删除后，该对账单下的所有采购记录将需要重新绑定对账单。`;
    deleteStatementModalVisible.value = true;
  } catch (error) {
    console.error('检查对账单状态失败:', error);
    message.error('检查对账单状态失败，请稍后重试');
  }
};

// 确认删除对账单
const handleDeleteStatementConfirm = async () => {
  if (!deleteStatementId.value) return;
  
  try {
    const response = await request({
      url: '/purchase/statement/delete',
      method: 'delete',
      params: {
        statement_id: deleteStatementId.value
      }
    });
    
    message.success('对账单删除成功');
    deleteStatementModalVisible.value = false;
    fetchData();
  } catch (error) {
    console.error('删除对账单失败:', error);
    message.error('删除失败，请稍后重试');
  }
};

// 打开取消确认对账单弹窗
const handleUnconfirmStatement = (record) => {
  if (!record.end_date) return;
  
  unconfirmStatementId.value = record.id;
  unconfirmModalContent.value = `确定要取消确认此对账单吗？取消后，该对账单的结束日期将被设为未确定，对应的采购记录将可以重新编辑。`;
  unconfirmModalVisible.value = true;
};

// 确认取消对账单
const handleUnconfirmStatementSubmit = async () => {
  if (!unconfirmStatementId.value) return;
  
  try {
    const response = await request({
      url: '/purchase/statement/unconfirm',
      method: 'post',
      params: {
        statement_id: unconfirmStatementId.value
      }
    });
    
    message.success('对账单取消确认成功');
    unconfirmModalVisible.value = false;
    fetchData();
    
    if (currentBill.value) {
      await fetchBillDetail(currentBill.value.id, currentBill.value.supplier_id);
    }
  } catch (error) {
    console.error('取消确认对账单失败:', error);
    message.error('取消确认失败，请稍后重试');
  }
};

// 初始化数据
onMounted(async () => {
  try {
    const response = await getSupplierSelect();
    supplierOptions.value = response.data.map(name => ({
      label: name,
      value: name
    }));
  } catch (error) {
    console.error('获取供货商列表失败:', error);
  }
  
  fetchData();
});
</script>

<style scoped>
.page-container {
  padding: 20px;
  height: 100%;
  background-color: #f5f5f5;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>