<template>
  <div class="page-container">
    <h1>运营杂费录入/查询</h1>
    
    <a-button type="primary" style="margin-bottom: 16px" @click="openAddModal">
      <template #icon><PlusOutlined /></template>
      新增运营杂费
    </a-button>
    
    <a-form
      v-if="showSearch"
      :model="searchParams"
      layout="inline"
      style="margin-bottom: 16px"
    >
      <a-form-item label="费用描述">
        <a-input
          v-model:value="searchParams.fee_desc"
          placeholder="请输入费用描述"
          style="width: 200px"
        />
      </a-form-item>
      <a-form-item label="费用类型">
        <a-select
          v-model:value="searchParams.fee_type"
          placeholder="请选择费用类型"
          style="width: 150px"
        >
          <a-select-option value="房租">房租</a-select-option>
          <a-select-option value="水电">水电</a-select-option>
          <a-select-option value="人工">人工</a-select-option>
          <a-select-option value="物流">物流</a-select-option>
          <a-select-option value="其他">其他</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="日期范围">
        <a-range-picker
          v-model:value="dateRange"
          format="YYYY-MM-DD"
          style="width: 300px"
        />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" @click="fetchData">查询</a-button>
        <a-button style="margin-left: 8px" @click="resetSearch">重置</a-button>
      </a-form-item>
    </a-form>
    
    <a-checkbox v-model:checked="showSearch" style="margin-bottom: 16px">显示搜索栏</a-checkbox>
    
    <a-table
      :columns="columns"
      :data-source="dataSource"
      :row-key="(record) => record.id"
      :pagination="{
        showSizeChanger: true,
        pageSizeOptions: [10, 20, 50, 100],
        showTotal: (total) => `共 ${total} 条记录`,
        current: searchParams.page_num,
        pageSize: searchParams.page_size,
        onChange: handlePageChange,
        onShowSizeChange: handlePageSizeChange
      }"
      :scroll="{ x: 1200 }"
      :loading="loading"
    />
    
    <a-modal
      v-model:open="modalVisible"
      :title="modalTitle"
      width="600px"
      destroyOnClose
      :footer="null"
    >
      <a-form
        :model="formData"
        :rules="formRules"
        layout="vertical"
      >
        <a-form-item label="费用描述" name="fee_desc">
          <a-input
            v-model:value="formData.fee_desc"
            placeholder="请输入费用描述（≤50字）"
            :maxLength="50"
            show-word-limit
          />
        </a-form-item>
        <a-form-item label="费用金额" name="fee_amount">
          <a-input-number
            v-model:value="formData.fee_amount"
            :min="0.01"
            :step="0.01"
            :precision="2"
            placeholder="请输入费用金额"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="费用日期" name="fee_date">
          <a-date-picker
            v-model:value="formData.fee_date"
            format="YYYY-MM-DD"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="费用类型" name="fee_type">
          <a-select
            v-model:value="formData.fee_type"
            placeholder="请选择费用类型"
            style="width: 100%"
          >
            <a-select-option value="房租">房租</a-select-option>
            <a-select-option value="水电">水电</a-select-option>
            <a-select-option value="人工">人工</a-select-option>
            <a-select-option value="物流">物流</a-select-option>
            <a-select-option value="其他">其他</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="备注" name="remark">
          <a-textarea
            v-model:value="formData.remark"
            :rows="4"
            :maxLength="200"
            placeholder="请输入备注信息"
          />
        </a-form-item>
        <a-form-item style="margin-top: 24px">
          <a-button type="primary" @click="handleSubmit">提交</a-button>
          <a-button style="margin-left: 8px" @click="handleReset">重置</a-button>
          <a-button style="margin-left: 8px" @click="modalVisible = false">取消</a-button>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue';
import { PlusOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue';
import { message, Modal, Tooltip } from 'ant-design-vue';
import dayjs from 'dayjs';
import type { CostFeeItem, AddCostFeeReq, UpdateCostFeeReq, CostFeeListQuery } from '@/types';
import {
  addCostFee,
  getCostFeeList,
  updateCostFee,
  deleteCostFee
} from '@/api/cost';

const modalVisible = ref(false);
const modalTitle = ref('新增运营杂费');
const showSearch = ref(true);
const dateRange = ref<any>([]);
const dataSource = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);

const searchParams = reactive<CostFeeListQuery>({
  page_num: 1,
  page_size: 10
});

const formData = reactive<AddCostFeeReq & Partial<UpdateCostFeeReq>>(
  {
    fee_desc: '',
    fee_amount: 0,
    fee_date: dayjs(),
    fee_type: '其他',
    remark: ''
  } as any
);

const formRules = reactive<any>({
  fee_desc: [
    { required: true, message: '请输入费用描述', trigger: ['blur', 'change'] },
    { type: 'string', min: 1, max: 50, message: '费用描述长度1-50字符', trigger: ['blur', 'change'] }
  ],
  fee_amount: [
    { required: true, message: '请输入费用金额', trigger: ['blur', 'change'] },
    { type: 'number', min: 0.01, message: '费用金额必须为正数', trigger: ['blur', 'change'] }
  ],
  fee_date: [
    { required: true, message: '请选择费用日期', trigger: ['change'] }
  ],
  fee_type: [
    { required: true, message: '请选择费用类型', trigger: ['change'] }
  ]
});

const columns = computed(() => [
  {
    title: '费用描述',
    dataIndex: 'fee_desc',
    key: 'fee_desc',
    sorter: true,
    ellipsis: true,
    width: 200
  },
  { 
    title: '费用金额', 
    dataIndex: 'fee_amount', 
    key: 'fee_amount', 
    sorter: true, 
    ellipsis: true, 
    width: 150,
    customRender: (opt: any) => opt.record.fee_amount.toFixed(2) 
  },
  {
    title: '费用日期',
    dataIndex: 'fee_date',
    key: 'fee_date',
    sorter: true,
    ellipsis: true,
    width: 120
  },
  {
    title: '费用类型',
    dataIndex: 'fee_type_text',
    key: 'fee_type_text',
    sorter: true,
    ellipsis: true,
    width: 120
  },
  {
    title: '备注',
    dataIndex: 'remark',
    key: 'remark',
    ellipsis: true,
    width: 100,
    customRender: (opt: { record: CostFeeItem }) => {
      const remark = opt.record.remark;
      if (!remark) return '-';
      const shortRemark = remark.length > 4 ? remark.substring(0, 4) + '...' : remark;
      return h(Tooltip, { title: remark }, { default: () => shortRemark });
    }
  },
  {
    title: '创建时间',
    dataIndex: 'create_time',
    key: 'create_time',
    sorter: true,
    ellipsis: true,
    width: 180
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right' as const,
    width: 120,
    customRender: ({ record }: { record: CostFeeItem }) => {
      return h('div', [
        h('span', {
          style: {
            display: 'inline-block',
            padding: '2px 8px',
            backgroundColor: '#1890ff',
            color: '#fff',
            borderRadius: '2px',
            cursor: 'pointer',
            marginRight: '8px',
            fontSize: '12px'
          },
          onClick: () => openEditModal(record)
        }, '改'),
        h('span', {
          style: {
            display: 'inline-block',
            padding: '2px 8px',
            backgroundColor: '#ff4d4f',
            color: '#fff',
            borderRadius: '2px',
            cursor: 'pointer',
            fontSize: '12px'
          },
          onClick: () => handleDelete(record.id)
        }, '删')
      ]);
    }
  }
]) as any;

const fetchData = async () => {
  loading.value = true;
  try {
    const queryParams: CostFeeListQuery = {
      ...searchParams,
      start_date: dateRange.value[0] ? (typeof dateRange.value[0]?.format === 'function' ? dateRange.value[0].format('YYYY-MM-DD') : dateRange.value[0]) : undefined,
      end_date: dateRange.value[1] ? (typeof dateRange.value[1]?.format === 'function' ? dateRange.value[1].format('YYYY-MM-DD') : dateRange.value[1]) : undefined
    };
    
    const response = await getCostFeeList(queryParams);
    
    // 字段映射：将后端返回的expense_*字段映射到前端使用的fee_*字段
    dataSource.value = response.data.list.map((item: any) => ({
      id: item.id,
      fee_desc: item.expense_desc,
      fee_amount: parseFloat(item.expense_amount),
      fee_date: item.expense_date,
      fee_type: item.expense_type,
      fee_type_text: item.expense_type,
      remark: item.remark,
      create_time: item.create_time,
      update_time: item.update_time
    }));
    total.value = response.data.total;
  } catch (error) {
    console.error('获取运营杂费列表失败:', error);
    message.error('获取数据失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page: number) => {
  searchParams.page_num = page;
  fetchData();
};

const handlePageSizeChange = (_: number, pageSize: number) => {
  searchParams.page_size = pageSize;
  searchParams.page_num = 1;
  fetchData();
};

const resetSearch = () => {
  searchParams.page_num = 1;
  searchParams.page_size = 10;
  searchParams.fee_desc = '';
  searchParams.fee_type = undefined;
  dateRange.value = [];
  fetchData();
};

const openAddModal = () => {
  Object.assign(formData, {
    id: undefined,
    fee_desc: '',
    fee_amount: 0,
    fee_date: dayjs(),
    fee_type: '其他',
    remark: ''
  });
  modalTitle.value = '新增运营杂费';
  modalVisible.value = true;
};

const openEditModal = (record: CostFeeItem) => {
  Object.assign(formData, {
    id: record.id,
    fee_desc: record.fee_desc,
    fee_amount: record.fee_amount,
    fee_date: dayjs(record.fee_date),
    fee_type: record.fee_type,
    remark: record.remark || ''
  });
  modalTitle.value = '修改运营杂费';
  modalVisible.value = true;
};

const handleSubmit = async () => {
  try {
    const submitData = {
      ...formData,
      fee_date: typeof formData.fee_date === 'object' && formData.fee_date !== null && typeof (formData.fee_date as any).format === 'function' ? (formData.fee_date as any).format('YYYY-MM-DD') : undefined
    };
    
    if (formData.id) {
      await updateCostFee(submitData as UpdateCostFeeReq);
      message.success('操作成功');
      modalVisible.value = false;
      fetchData();
    } else {
      await addCostFee(submitData as AddCostFeeReq);
      message.success('操作成功');
      modalVisible.value = false;
      fetchData();
    }
  } catch (error: any) {
    console.error('提交失败:', error);
    Modal.error({
      title: '操作失败',
      content: error.message || '服务器错误，请稍后重试'
    });
  }
};

const handleReset = () => {
  if (!formData.id) {
    Object.assign(formData, {
      fee_desc: '',
      fee_amount: 0,
      fee_date: dayjs(),
      fee_type: '其他',
      remark: ''
    });
  }
};

const handleDelete = (id: number) => {
  Modal.confirm({
    title: '确认删除',
    icon: () => h(ExclamationCircleOutlined),
    content: '删除后不可恢复',
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteCostFee({ id });
        message.success('删除成功');
        fetchData();
      } catch (error: any) {
        console.error('删除失败:', error);
        Modal.error({
          title: '删除失败',
          content: error.message || '服务器错误，请稍后重试'
        });
      }
    }
  });
};

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.page-container {
  padding: 20px;
  height: 100%;
  background-color: #f5f5f5;
}

:deep(.ant-modal-body) {
  padding: 24px;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}
</style>
