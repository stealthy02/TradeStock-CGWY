<template>
  <div class="page-container">
    <h1>采购信息录入/查询</h1>
    
    <a-button type="primary" style="margin-bottom: 16px" @click="openAddModal">
      <template #icon><PlusOutlined /></template>
      新增采购信息
    </a-button>
    
    <a-form
      v-if="showSearch"
      :model="searchParams"
      layout="inline"
      style="margin-bottom: 16px"
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
      <a-form-item label="商品名称">
        <a-select
          v-model:value="searchParams.product_name"
          placeholder="请输入商品名称"
          show-search
          :filter-option="false"
          :options="searchProductOptions"
          @search="handleSearchProductSearch"
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
      :pagination="{
        showSizeChanger: true,
        pageSizeOptions: ['10', '20', '50', '100'],
        showTotal: (total) => `共 ${total} 条记录`,
        current: searchParams.page_num,
        pageSize: searchParams.page_size,
        onChange: handlePageChange,
        onShowSizeChange: handlePageSizeChange
      }"
      :scroll="{ x: 1400 }"
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
        ref="formRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
      >
        <a-form-item label="供货商名称" name="supplier_name">
          <a-select
            v-model:value="formData.supplier_name"
            placeholder="请选择供货商"
            show-search
            :filter-option="false"
            :options="supplierOptions"
            @search="handleSupplierSearch"
            @change="handleSupplierChange"
          />
        </a-form-item>
        <a-form-item label="商品名称" name="product_name">
          <a-select
            v-model:value="formData.product_name"
            :options="productOptions"
            placeholder="请输入商品名称"
            show-search
            :filter-option="false"
            @search="handleProductSearch"
            @change="handleProductChange"
            style="width: 100%"
            :not-found-content="productOptions.length === 0 ? '输入商品名称后按回车' : undefined"
          />
        </a-form-item>
        <a-form-item label="商品规格" name="product_spec">
          <a-input
            v-model:value="formData.product_spec"
            placeholder="请输入商品规格，例如：30"
          />
        </a-form-item>
        <a-form-item label="采购数量" name="purchase_num">
          <a-input-number
            v-model:value="formData.purchase_num"
            :min="1"
            :step="1"
            :precision="0"
            placeholder="请输入采购数量"
          />
        </a-form-item>
        <a-form-item label="采购单价" name="purchase_price">
          <a-input-number
            v-model:value="formData.purchase_price"
            :min="0.01"
            :step="0.01"
            :precision="2"
            placeholder="请输入采购单价"
          />
        </a-form-item>
        <a-form-item label="采购日期" name="purchase_date">
          <a-date-picker
            v-model:value="formData.purchase_date"
            format="YYYY-MM-DD"
            style="width: 100%"
          />
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
import { useRoute } from 'vue-router';
import { PlusOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue';
// 修复1：AntD Vue4 无AButton，仅导出Button；删除未使用的Button声明提示
import { message, Modal, Tooltip } from 'ant-design-vue';
import dayjs from 'dayjs';
import type { PurchaseInfoItem, AddPurchaseInfoReq, UpdatePurchaseInfoReq, PurchaseInfoListQuery } from '@/types';
import type { FormInstance, RuleObject } from 'ant-design-vue/es/form';
import {
  addPurchaseInfo,
  getPurchaseInfoList,
  updatePurchaseInfo,
  deletePurchaseInfo,
  selectPurchaseProduct,
  getLastPurchasePrice
} from '@/api/purchase';
import { getSupplierSelect } from '@/api/basic';
import request from '@/utils/request';

const modalVisible = ref(false);
const modalTitle = ref('新增采购信息');
const showSearch = ref(true);
const supplierOptions = ref<{ label: string; value: string }[]>([]);
const productOptions = ref<{ label: string; value: string }[]>([]); 
const searchProductOptions = ref<{ label: string; value: string }[]>([]);
const dataSource = ref<PurchaseInfoItem[]>([]);
const total = ref(0);
const loading = ref(false);
const formRef = ref<FormInstance>();

// 路由实例
const route = useRoute();

const searchParams = reactive<PurchaseInfoListQuery>({
  page_num: 1,
  page_size: 10,
  supplier_name: '',
  product_name: ''
});

// 修复：初始化值为undefined，避免默认为0的问题
const formData = reactive<AddPurchaseInfoReq & Partial<UpdatePurchaseInfoReq>>({
  id: undefined,
  supplier_name: '',
  product_name: '',
  product_spec: '',
  purchase_num: undefined,
  purchase_price: undefined,
  purchase_date: dayjs(),
  remark: '',
  supplier_id: undefined
} as unknown as AddPurchaseInfoReq & Partial<UpdatePurchaseInfoReq>);

const formRules = reactive<Record<string, RuleObject[]>>({
  supplier_name: [{ required: true, message: '请选择供货商', trigger: 'change' }],
  product_name: [{ required: true, message: '请输入商品名称', trigger: 'blur', type: 'string' }],
  product_spec: [{ required: true, message: '请输入商品规格', trigger: 'blur', type: 'string' }],
  purchase_num: [
    { required: true, message: '请输入采购数量', trigger: 'blur', type: 'number' },
    { type: 'number', min: 1, message: '采购数量必须为正整数', trigger: 'blur' }
  ],
  purchase_price: [
    { required: true, message: '请输入采购单价', trigger: 'blur', type: 'number' },
    { type: 'number', min: 0.01, message: '采购单价必须为正数', trigger: 'blur' }
  ],
  purchase_date: [{ required: true, message: '请选择采购日期', trigger: 'change', type: 'date' }]
});

const columns = computed(() => [
  {
    title: '供货商名称',
    dataIndex: 'supplier_name',
    key: 'supplier_name',
    sorter: true,
    ellipsis: true
  },
  {
    title: '商品名称',
    dataIndex: 'product_name',
    key: 'product_name',
    sorter: true,
    ellipsis: true
  },
  {
      title: '商品规格',
      dataIndex: 'product_spec',
      key: 'product_spec',
      sorter: true,
      ellipsis: true,
      customRender: (opt: { record: any }) => opt.record.product_spec || '-'
    },
  {
    title: '采购数量',
    dataIndex: 'purchase_num',
    key: 'purchase_num',
    sorter: true,
    ellipsis: true
  },
  { 
    title: '采购单价', 
    dataIndex: 'purchase_price', 
    key: 'purchase_price', 
    sorter: true, 
    ellipsis: true, 
    customRender: (opt: { record: PurchaseInfoItem }) => opt.record.purchase_price.toFixed(2) 
  },
  { 
    title: '采购总价', 
    dataIndex: 'total_price', 
    key: 'total_price', 
    sorter: true, 
    ellipsis: true, 
    customRender: (opt: { record: PurchaseInfoItem }) => opt.record.total_price.toFixed(2) 
  },
  {
    title: '采购日期',
    dataIndex: 'purchase_date',
    key: 'purchase_date',
    sorter: true,
    ellipsis: true
  },
  {
    title: '备注',
    dataIndex: 'remark',
    key: 'remark',
    ellipsis: true,
    customRender: (opt: { record: PurchaseInfoItem }) => {
      const remark = opt.record.remark;
      if (!remark) return '-';
      const shortRemark = remark.length > 4 ? remark.substring(0, 4) + '...' : remark;
      return h(Tooltip, { title: remark }, { default: () => shortRemark });
    }
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right' as const,
    width: 80,
    customRender: ({ record }: { record: PurchaseInfoItem }) => {
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
]);

const fetchData = async (id?: number) => {
  loading.value = true;
  try {
    const queryParams: any = {
      ...searchParams,
      ...(id && { id })
    };
    
    const response = await getPurchaseInfoList(queryParams);
    dataSource.value = response.data.list;
    total.value = response.data.total;
  } catch (error) {
    console.error('获取采购信息列表失败:', error);
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
  searchParams.supplier_name = '';
  searchParams.product_name = '';
  searchProductOptions.value = [];
  fetchData();
};

const handleSupplierSearch = async (value: string) => {
  if (!value) return;
  try {
    const response = await getSupplierSelect({ keyword: value });
    supplierOptions.value = response.data.map((name: string) => ({
      label: name,
      value: name
    }));
  } catch (error) {
    console.error('获取供货商列表失败:', error);
  }
};

const handleSupplierChange = async (value: unknown) => {
  if (typeof value === 'string' && formData.product_name) {
    await fetchLastPrice(value, formData.product_name);
  }
};

// 保留：无联想时可手动输入的核心逻辑
const handleProductSearch = async (value: string) => {
  formData.product_name = value;
  if (!value) {
    productOptions.value = [];
    return;
  }
  try {
    const response = await selectPurchaseProduct({ keyword: value });
    let options: { label: string; value: string }[] = [];
    if (Array.isArray(response.data)) {
      options = response.data.map((name: string) => ({
        label: name,
        value: name
      }));
    }
    productOptions.value = [
      { label: value, value: value },
      ...options.filter(option => option.value !== value)
    ];
  } catch (error) {
    console.error('获取商品列表失败:', error);
    productOptions.value = [{ label: value, value: value }];
  }
};

const handleProductChange = async (value: unknown) => {
  if (typeof value === 'string' && formData.supplier_name) {
    await fetchLastPrice(formData.supplier_name, value);
  }
};

const handleSearchProductSearch = async (value: string) => {
  if (!value) return;
  try {
    const response = await selectPurchaseProduct({ keyword: value });
    if (Array.isArray(response.data)) {
      searchProductOptions.value = response.data.map((name: string) => ({
        label: name,
        value: name
      }));
    } else {
      searchProductOptions.value = [];
    }
  } catch (error) {
    console.error('获取商品列表失败:', error);
    searchProductOptions.value = [];
  }
};

const fetchLastPrice = async (supplierName: string, productName: string) => {
  try {
    const response = await getLastPurchasePrice({ supplier_name: supplierName, product_name: productName });
    const data = response.data;
    if (data) {
      if (data.purchase_price) {
        formData.purchase_price = data.purchase_price;
      }
      if (data.product_spec) {
        formData.product_spec = data.product_spec;
      }
    }
  } catch (error) {
    console.error('获取历史单价失败:', error);
  }
};

const openAddModal = () => {
  Object.assign(formData, {
    id: undefined,
    supplier_id: undefined,
    supplier_name: '',
    product_name: '',
    product_spec: '',
    purchase_num: undefined,
    purchase_price: undefined,
    purchase_date: dayjs(),
    remark: ''
  });
  modalTitle.value = '新增采购信息';
  modalVisible.value = true;
};

// 检查采购日期是否在已确定的对账单日期范围内
const checkPurchaseDateInStatementRange = async (supplierName: string, purchaseDate: dayjs.Dayjs) => {
  try {
    // 获取该供货商的所有已确定对账单
    const response = await request({
      url: '/purchase/bill/list',
      method: 'get',
      params: {
        supplier_name: supplierName,
        page_num: 1,
        page_size: 100
      }
    });
    
    const bills = response.data?.list || [];
    for (const bill of bills) {
      if (bill.end_date) {
        const startDate = dayjs(bill.start_date);
        const endDate = dayjs(bill.end_date);
        if (purchaseDate.isAfter(startDate.subtract(1, 'day')) && purchaseDate.isBefore(endDate.add(1, 'day'))) {
          return {
            inRange: true,
            bill: bill
          };
        }
      }
    }
    return { inRange: false };
  } catch (error) {
    console.error('检查对账单日期范围失败:', error);
    return { inRange: false };
  }
};

// 保留：表单前置校验核心逻辑
const handleSubmit = async () => {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
  } catch (error) {
    message.error('请完善表单信息后再提交');
    return;
  }

  try {
    const purchaseDate = dayjs.isDayjs(formData.purchase_date) ? formData.purchase_date : dayjs(formData.purchase_date);
    
    // 检查采购日期是否在已确定的对账单日期范围内
    if (formData.supplier_name) {
      const checkResult = await checkPurchaseDateInStatementRange(formData.supplier_name, purchaseDate);
      if (checkResult.inRange) {
        Modal.confirm({
          title: '日期范围提醒',
          content: `您选择的采购日期(${purchaseDate.format('YYYY-MM-DD')})在已确定的对账单日期范围内(${checkResult.bill.start_date} 至 ${checkResult.bill.end_date})。继续添加可能会导致对账单发生改变，确定要继续吗？`,
          onOk: async () => {
            await submitPurchaseData();
          }
        });
        return;
      }
    }
    
    await submitPurchaseData();
  } catch (error: any) {
    console.error('提交失败:', error);
    Modal.error({
      title: '操作失败',
      content: error.message || '服务器错误，请稍后重试'
    });
  }
};

// 提交采购数据
const submitPurchaseData = async () => {
  const purchaseDate = dayjs.isDayjs(formData.purchase_date) ? formData.purchase_date : dayjs(formData.purchase_date);
  const submitData = {
    ...formData,
    purchase_date: purchaseDate.format('YYYY-MM-DD')
  };

  if (formData.id) {
    await updatePurchaseInfo(submitData as UpdatePurchaseInfoReq);
    message.success('修改成功');
  } else {
    await addPurchaseInfo(submitData as AddPurchaseInfoReq);
    message.success('新增成功');
  }
  modalVisible.value = false;
  fetchData();
};

const handleReset = () => {
  if (!formRef.value) return;
  formRef.value.resetFields();
  if (!formData.id) {
    Object.assign(formData, {
      supplier_id: 0,
      product_name: '',
      product_spec: '',
      purchase_num: undefined,
      purchase_price: undefined,
      purchase_date: dayjs(),
      remark: '',
      supplier_name: ''
    });
  }
};

const handleDelete = (id: number) => {
  Modal.confirm({
    title: '确认删除',
    icon: () => h(ExclamationCircleOutlined),
    content: '删除后同步更新对账单、库存，不可恢复',
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deletePurchaseInfo({ id });
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

onMounted(async () => {
  await Promise.all([
    (async () => {
      try {
        const response = await getSupplierSelect();
        supplierOptions.value = response.data.map((name: string) => ({
          label: name,
          value: name
        }));
      } catch (error) {
        console.error('获取供货商列表失败:', error);
      }
    })(),
    (async () => {
      try {
        const response = await selectPurchaseProduct({});
        if (Array.isArray(response.data)) {
          productOptions.value = response.data.map((name: string) => ({
            label: name,
            value: name
          }));
          searchProductOptions.value = productOptions.value;
        } else {
          productOptions.value = [];
          searchProductOptions.value = [];
        }
      } catch (error) {
        console.error('获取商品列表失败:', error);
      }
    })()
  ]);
  
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

:deep(.ant-modal-body) {
  padding: 24px;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}
</style>