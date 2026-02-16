<template>
  <div class="page-container">
    <h1>库存报损录入/查询</h1>
    
    <div class="action-bar">
      <a-button type="primary" @click="openAddModal">
        <template #icon><PlusOutlined /></template>
        新建库存报损
      </a-button>
    </div>
    
    <a-form
      v-if="showSearch"
      :model="searchParams"
      layout="inline"
      style="margin-bottom: 16px; padding: 16px; background: #fafafa; border-radius: 8px"
    >
      <a-form-item label="商品名称">
        <a-select
          v-model:value="searchParams.product_name"
          placeholder="请输入商品名称"
          show-search
          :filter-option="false"
          :options="productOptions"
          @search="handleProductSearch"
          style="width: 200px"
        />
      </a-form-item>
      <a-form-item label="报损日期范围">
        <a-range-picker
          v-model:value="dateRange"
          format="YYYY-MM-DD"
          style="width: 300px"
        />
      </a-form-item>
      <a-form-item label="报损原因">
        <a-input
          v-model:value="lossReason"
          placeholder="请输入报损原因"
          style="width: 200px"
        />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" @click="() => fetchData()">查询</a-button>
        <a-button style="margin-left: 8px" @click="resetSearch">重置</a-button>
      </a-form-item>
    </a-form>
    
    <a-checkbox v-model:checked="showSearch" style="margin-bottom: 16px">显示搜索栏</a-checkbox>
    
    <a-table
      :columns="columns"
      :data-source="dataSource"
      :row-key="(record) => record.id"
      :pagination="false"
      :scroll="{ x: 1400 }"
      :loading="loading"
    />
    
    <a-pagination
      v-if="total > 0"
      :current="searchParams.page_num"
      :page-size="searchParams.page_size"
      :total="total"
      show-size-changer
      :show-total="(total) => `共 ${total} 条记录`"
      style="margin-top: 24px; text-align: right"
      @change="handlePageChange"
      @show-size-change="handlePageSizeChange"
    />
    
    <a-modal
      v-model:open="modalVisible"
      :title="modalTitle"
      width="600px"
      destroyOnClose
      :footer="null"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
      >
        <a-form-item label="商品名称" name="product_name">
          <a-select
            v-model:value="formData.product_name"
            placeholder="请选择商品"
            show-search
            :filter-option="false"
            :options="productOptions"
            @search="handleProductSearch"
            @focus="handleProductFocus"
            @change="handleProductChange"
            style="width: 100%"
          />
          <div v-if="currentInventory" style="margin-top: 8px; color: #52c41a; font-size: 12px">
            当前库存：{{ currentInventory.inventory_num }}
          </div>
        </a-form-item>
        <a-form-item label="商品规格" name="product_spec">
          <a-input
            v-model:value="formData.product_spec"
            placeholder="请输入商品规格，例如：30"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="报损数量" name="loss_num">
          <a-input-number
            v-model:value="formData.loss_num"
            :min="1"
            :step="1"
            :precision="0"
            placeholder="请输入报损数量"
            style="width: 100%"
          />
          <div v-if="inventoryError" style="color: #ff4d4f; font-size: 12px; margin-top: 4px">
            {{ inventoryError }}
          </div>
        </a-form-item>
        <a-form-item label="报损日期" name="loss_date">
          <a-date-picker
            v-model:value="formData.loss_date"
            format="YYYY-MM-DD"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="报损原因" name="loss_reason">
          <a-textarea
            v-model:value="formData.loss_reason"
            :rows="4"
            :maxLength="200"
            placeholder="请输入报损原因（如：损坏/过期/丢失）"
            show-word-limit
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
import { useRoute } from 'vue-router';
import { PlusOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue';
import { message, Modal } from 'ant-design-vue';
import dayjs from 'dayjs';
import type { InventoryLossItem, AddInventoryLossReq, InventoryLossListQuery, InventoryItem } from '@/types';
import type { SelectValue } from 'ant-design-vue/es/select';
import {
  addInventoryLoss,
  getInventoryLossList,
  deleteInventoryLoss
} from '@/api/inventory';
import { getInventoryList } from '@/api/inventory';

const modalVisible = ref(false);
const modalTitle = ref('新建库存报损');
const showSearch = ref(true);
const dateRange = ref<any>([]);
const dataSource = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const formRef = ref<any>();
const lossReason = ref('');

// 路由实例
const route = useRoute();

const productOptions = ref<{ label: string; value: string }[]>([]);
const currentInventory = ref<InventoryItem | null>(null);
const inventoryError = ref('');

const searchParams = reactive<InventoryLossListQuery>({
  page_num: 1,
  page_size: 10
});

const formData = reactive<(Omit<AddInventoryLossReq, 'loss_date'> & { loss_date?: any; id?: number })>({
  product_name: '',
  product_spec: '',
  loss_num: 1,
  loss_date: dayjs(),
  loss_reason: ''
});

const formRules = reactive<any>({
  product_name: [
    { required: true, message: '请选择商品', trigger: ['blur', 'change'] },
    {
      validator: (_rule: any, value: string) => {
        if (!value) return Promise.resolve();
        const exists = productOptions.value.some(opt => opt.value === value);
        if (!exists) {
          return Promise.reject('商品不存在，请选择已存在的商品');
        }
        return Promise.resolve();
      },
      trigger: ['blur', 'change']
    }
  ],
  product_spec: [
    { required: true, message: '请输入商品规格', trigger: ['blur', 'change'] }
  ],
  loss_num: [
    { required: true, message: '请输入报损数量', trigger: ['blur', 'change'] },
    { type: 'number', min: 1, message: '报损数量必须为正整数', trigger: ['blur', 'change'] },
    {
      validator: (_rule: any, value: number) => {
        if (!value) return Promise.resolve();
        if (currentInventory.value && value > currentInventory.value.inventory_num) {
          return Promise.reject(`库存不足，当前${formData.product_name}库存为${currentInventory.value.inventory_num}`);
        }
        return Promise.resolve();
      },
      trigger: ['blur', 'change']
    }
  ],
  loss_date: [
    { required: true, message: '请选择报损日期', trigger: ['change'] }
  ]
});



const columns = computed(() => [
  {
    title: '商品名称',
    dataIndex: 'product_name',
    key: 'product_name',
    sorter: true,
    ellipsis: true,
    fixed: 'left' as const,
    width: 200
  },
  {
    title: '商品规格',
    dataIndex: 'product_spec',
    key: 'product_spec',
    sorter: true,
    ellipsis: true,
    width: 120
  },
  {
    title: '报损数量',
    dataIndex: 'loss_num',
    key: 'loss_num',
    sorter: true,
    ellipsis: true,
    width: 120
  },
  { 
    title: '库存单位成本', 
    dataIndex: 'lossUnitCost', 
    key: 'lossUnitCost', 
    sorter: true, 
    ellipsis: true, 
    width: 150,
    customRender: (opt: any) => opt.record.lossUnitCost?.toFixed(2) || '0.00'
  },
  { 
    title: '报损总成本', 
    dataIndex: 'losstotal_cost', 
    key: 'losstotal_cost', 
    sorter: true, 
    ellipsis: true, 
    width: 150,
    customRender: (opt: any) => opt.record.losstotal_cost?.toFixed(2) || '0.00'
  },
  {
    title: '报损日期',
    dataIndex: 'loss_date',
    key: 'loss_date',
    sorter: true,
    ellipsis: true,
    width: 120
  },
  {
    title: '报损原因',
    dataIndex: 'loss_reason',
    key: 'loss_reason',
    ellipsis: true,
    width: 150,
    customRender: (opt: { record: InventoryLossItem }) => {
      const reason = opt.record.loss_reason;
      return reason || '-';
    }
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right' as const,
    width: 120,
    customRender: ({ record }: { record: InventoryLossItem }) => {
      return h('div', [
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

const fetchData = async (id?: number) => {
  loading.value = true;
  try {
    const queryParams: any = {
      ...searchParams,
      start_date: dateRange.value[0] ? (typeof dateRange.value[0]?.format === 'function' ? dateRange.value[0].format('YYYY-MM-DD') : dateRange.value[0]) : undefined,
      end_date: dateRange.value[1] ? (typeof dateRange.value[1]?.format === 'function' ? dateRange.value[1].format('YYYY-MM-DD') : dateRange.value[1]) : undefined,
      ...(id && { id })
    };
    
    const response = await getInventoryLossList(queryParams);
    
    dataSource.value = response.data.list.map((item: any) => ({
      ...item,
      lossUnitCost: item.lossUnitCost || 0,
      losstotal_cost: item.losstotal_cost || 0
    }));
    total.value = response.data.total;
  } catch (error) {
    console.error('获取库存报损列表失败:', error);
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
  searchParams.product_name = '';
  lossReason.value = '';
  dateRange.value = [];
  fetchData();
};

const handleProductSearch = async (value: string) => {
  if (!value) return;
  try {
    const response = await getInventoryList({ product_name: value, page_size: 5 });
    if (Array.isArray(response.data.list)) {
      productOptions.value = response.data.list.map((item: InventoryItem) => ({
        label: item.product_name,
        value: item.product_name
      }));
    } else {
      productOptions.value = [];
    }
  } catch (error) {
    console.error('获取商品列表失败:', error);
    productOptions.value = [];
  }
};

const handleProductFocus = async () => {
  try {
    const response = await getInventoryList({ page_size: 5 });
    if (Array.isArray(response.data.list)) {
      productOptions.value = response.data.list.map((item: InventoryItem) => ({
        label: item.product_name,
        value: item.product_name
      }));
    }
  } catch (error) {
    console.error('获取商品列表失败:', error);
  }
};

const handleProductChange = async (value: SelectValue) => {
  if (!value) {
    currentInventory.value = null;
    inventoryError.value = '';
    return;
  }
  
  try {
    const response = await getInventoryList({ product_name: value as string, page_size: 1 });
    if (Array.isArray(response.data.list) && response.data.list.length > 0) {
      currentInventory.value = response.data.list[0];
      inventoryError.value = '';
      
      if (currentInventory.value && formData.loss_num > currentInventory.value.inventory_num) {
        inventoryError.value = `库存不足，当前${value}库存为${currentInventory.value.inventory_num}`;
      }
    } else {
      currentInventory.value = null;
      inventoryError.value = '商品不存在';
    }
  } catch (error) {
    console.error('获取商品库存失败:', error);
    currentInventory.value = null;
  }
};

const openAddModal = () => {
  Object.assign(formData, {
    id: undefined,
    product_name: '',
    product_spec: '',
    loss_num: 1,
    loss_date: dayjs(),
    loss_reason: ''
  });
  currentInventory.value = null;
  inventoryError.value = '';
  modalTitle.value = '新建库存报损';
  modalVisible.value = true;
};



const handleSubmit = async () => {
  if (!formRef.value) return;
  
  try {
    await formRef.value.validate();
    
    if (currentInventory.value && formData.loss_num > currentInventory.value.inventory_num) {
      message.error(`库存不足，当前${formData.product_name}库存为${currentInventory.value.inventory_num}`);
      return;
    }
    
    const submitData = {
      ...formData,
      loss_date: typeof formData.loss_date === 'object' && formData.loss_date !== null && typeof (formData.loss_date as any).format === 'function' ? (formData.loss_date as any).format('YYYY-MM-DD') : undefined
    };
    
    await addInventoryLoss(submitData as AddInventoryLossReq);
    message.success('报损成功，已自动扣减库存');
    modalVisible.value = false;
    fetchData();
  } catch (error: any) {
    console.error('提交失败:', error);
    if (error.errorFields) {
      message.error('请检查表单填写是否正确');
    } else {
      Modal.error({
        title: '操作失败',
        content: error.message || '服务器错误，请稍后重试'
      });
    }
  }
};

const handleReset = () => {
  if (!formData.id) {
    Object.assign(formData, {
      product_name: '',
      product_spec: '',
      loss_num: 1,
      loss_date: dayjs(),
      loss_reason: ''
    });
    currentInventory.value = null;
    inventoryError.value = '';
  }
};

const handleDelete = (id: number) => {
  Modal.confirm({
    title: '确认删除',
    icon: () => h(ExclamationCircleOutlined),
    content: '删除后将恢复库存，是否确认删除？',
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteInventoryLoss({ id });
        message.success('删除成功，已恢复库存');
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





onMounted(async () => {
  await handleProductFocus();
  
  // 检查路由参数id
  const id = route.query.id;
  if (id) {
    fetchData(Number(id));
  } else {
    fetchData();
  }
});
</script>

<style scoped>
.page-container {
  padding: 20px;
  height: 100%;
  background-color: #f5f5f5;
}

.action-bar {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
}

:deep(.ant-modal-body) {
  padding: 24px;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}
</style>
