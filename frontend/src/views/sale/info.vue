<template>
  <div class="page-container">
    <h1>销售信息录入/查询</h1>
    
    <a-button type="primary" style="margin-bottom: 16px" @click="openAddModal">
      <template #icon><PlusOutlined /></template>
      新增销售信息
    </a-button>
    
    <a-form
      v-if="showSearch"
      :model="searchParams"
      layout="inline"
      style="margin-bottom: 16px"
    >
      <a-form-item label="采购商名称">
        <a-select
          v-model:value="searchParams.purchaser_name"
          placeholder="请选择采购商"
          show-search
          :filter-option="false"
          :options="purchaserOptions"
          @search="handlePurchaserSearch"
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
      <a-form-item label="客户侧商品名">
        <a-input
          v-model:value="searchParams.customer_product_name"
          placeholder="请输入客户侧商品名"
          style="width: 200px"
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
        pageSizeOptions: ['10', '20', '50', '100'],
        showTotal: (total) => `共 ${total} 条记录`,
        current: searchParams.page_num,
        pageSize: searchParams.page_size,
        onChange: handlePageChange,
        onShowSizeChange: handlePageSizeChange
      }"
      :scroll="{ x: 1600 }"
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
        <a-form-item label="采购商名称" name="purchaser_name">
          <a-select
            v-model:value="formData.purchaser_name"
            placeholder="请选择采购商"
            show-search
            :filter-option="false"
            :options="purchaserOptions"
            @search="handlePurchaserSearch"
            @change="handlePurchaserChange"
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
          />
        </a-form-item>
        <a-form-item label="商品规格" name="product_spec">
          <a-input
            v-model:value="formData.product_spec"
            placeholder="请输入商品规格，例如：30"
          />
        </a-form-item>
        <a-form-item label="客户侧商品名" name="customer_product_name">
          <a-input
            v-model:value="formData.customer_product_name"
            placeholder="请输入客户侧商品名"
          />
        </a-form-item>
        <a-form-item label="销售数量" name="sale_num">
          <a-input-number
            v-model:value="formData.sale_num"
            :min="1"
            :step="1"
            :precision="0"
            placeholder="请输入销售数量"
          />
        </a-form-item>
        <a-form-item label="销售单价" name="sale_price">
          <a-input-number
            v-model:value="formData.sale_price"
            :min="0.01"
            :step="0.01"
            :precision="2"
            placeholder="请输入销售单价"
          />
        </a-form-item>
        <a-form-item label="销售日期" name="sale_date">
          <a-date-picker
            v-model:value="formData.sale_date"
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
import { message, Modal, Tooltip } from 'ant-design-vue';
import dayjs from 'dayjs';
import type { SaleInfoItem, AddSaleInfoReq, UpdateSaleInfoReq, SaleInfoListQuery } from '@/types';
import {
  addSaleInfo,
  getSaleInfoList,
  updateSaleInfo,
  deleteSaleInfo,
  getSaleProductSelect,
  getLastSalePrice
} from '@/api/sale';
import { getPurchaserSelect } from '@/api/basic';
import request from '@/utils/request';

const modalVisible = ref(false);
const modalTitle = ref('新增销售信息');
const showSearch = ref(true);
const purchaserOptions = ref<any[]>([]);
const productOptions = ref<any[]>([]);
const searchProductOptions = ref<any[]>([]);
const dataSource = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);

// 路由实例
const route = useRoute();

const searchParams = reactive<SaleInfoListQuery>({
  page_num: 1,
  page_size: 10
});

const formData = reactive<AddSaleInfoReq & Partial<UpdateSaleInfoReq>>(
  {
    purchaser_name: '',
    product_name: '',
    product_spec: '',
    customer_product_name: '',
    sale_num: 0,
    sale_price: 0,
    sale_date: dayjs(),
    remark: ''
  } as any
);

const formRules = reactive<any>({
  purchaser_name: [
    { required: true, message: '请选择采购商', trigger: ['change'] }
  ],
  product_name: [
    { required: true, message: '请输入商品名称', trigger: ['blur', 'change'] }
  ],
  product_spec: [
    { required: true, message: '请输入商品规格', trigger: ['blur', 'change'] }
  ],
  sale_num: [
    { required: true, message: '请输入销售数量', trigger: ['blur', 'change'] },
    { type: 'number', min: 1, message: '销售数量必须为正整数', trigger: ['blur', 'change'] }
  ],
  sale_price: [
    { required: true, message: '请输入销售单价', trigger: ['blur', 'change'] },
    { type: 'number', min: 0.01, message: '销售单价必须为正数', trigger: ['blur', 'change'] }
  ],
  sale_date: [
    { required: true, message: '请选择销售日期', trigger: ['change'] }
  ]
});

const columns = computed(() => [
  {
    title: '采购商名称',
    dataIndex: 'purchaser_name',
    key: 'purchaser_name',
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
    ellipsis: true
  },
  {
    title: '客户侧商品名',
    dataIndex: 'customer_product_name',
    key: 'customer_product_name',
    sorter: true,
    ellipsis: true
  },
  {
    title: '销售数量',
    dataIndex: 'sale_num',
    key: 'sale_num',
    sorter: true,
    ellipsis: true
  },
  { title: '销售单价', dataIndex: 'sale_price', key: 'sale_price', sorter: true, ellipsis: true, customRender: (opt: any) => opt.record.sale_price.toFixed(2) },
  { title: '销售总价', dataIndex: 'total_price', key: 'total_price', sorter: true, ellipsis: true, customRender: (opt: any) => opt.record.total_price.toFixed(2) },
  { title: '商品单位利润', dataIndex: 'unit_profit', key: 'unit_profit', sorter: true, ellipsis: true, customRender: (opt: any) => opt.record.unit_profit.toFixed(2) },
  { title: '商品总利润', dataIndex: 'total_profit', key: 'total_profit', sorter: true, ellipsis: true, customRender: (opt: any) => opt.record.total_profit.toFixed(2) },
  {
    title: '销售日期',
    dataIndex: 'sale_date',
    key: 'sale_date',
    sorter: true,
    ellipsis: true
  },
  {
    title: '备注',
    dataIndex: 'remark',
    key: 'remark',
    ellipsis: true,
    customRender: (opt: any) => {
      const remark = opt.record.remark;
      if (!remark) return '-';
      const shortRemark = remark.length > 4 ? remark.substring(0, 4) + '...' : remark;
      return h(Tooltip, { title: remark }, { default: () => shortRemark });
    }
  },
  { title: '操作',
    key: 'action',
    fixed: 'right' as const,
    width: 80,
    customRender: ({ record }: { record: SaleInfoItem }) => {
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

const fetchData = async (id?: number | MouseEvent) => {
  loading.value = true;
  try {
    const queryParams: any = {
      ...searchParams,
      ...(typeof id === 'number' && { id })
    };
    
    const response = await getSaleInfoList(queryParams);
    
    dataSource.value = response.data.list;
    total.value = response.data.total;
  } catch (error) {
    console.error('获取销售信息列表失败:', error);
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
  searchParams.purchaser_name = '';
  searchParams.product_name = '';
  searchParams.customer_product_name = '';
  searchProductOptions.value = [];
  fetchData();
};

const handlePurchaserSearch = async (value: string) => {
  if (!value) return;
  
  try {
    const response = await getPurchaserSelect({ keyword: value });
    purchaserOptions.value = response.data.map((name: string) => ({
      label: name,
      value: name
    }));
  } catch (error) {
    console.error('获取采购商列表失败:', error);
  }
};

const handlePurchaserChange = async (value: any) => {
  if (value && formData.product_name) {
    await fetchLastPrice(value, formData.product_name);
  }
};

const handleProductSearch = async (value: string) => {
  if (!value) {
    productOptions.value = [];
    return;
  }
  
  try {
    const response = await getSaleProductSelect({ keyword: value });
    if (Array.isArray(response.data)) {
      productOptions.value = response.data.map((name: string) => ({
        label: name,
        value: name
      }));
    } else {
      productOptions.value = [];
    }
  } catch (error) {
    console.error('获取商品列表失败:', error);
    productOptions.value = [];
  }
};

const handleProductChange = async (value: any) => {
  if (value && formData.purchaser_name) {
    await fetchLastPrice(formData.purchaser_name, value);
  }
};

const handleSearchProductSearch = async (value: string) => {
  if (!value) return;
  try {
    const response = await getSaleProductSelect({ keyword: value });
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

const fetchLastPrice = async (purchaserName: string, productName: string) => {
  try {
    const response = await getLastSalePrice({
      purchaser_name: purchaserName,
      product_name: productName
    });
    
    const data = response.data;
    if (data) {
      if (data.sale_price) {
        formData.sale_price = data.sale_price;
      }
      if (data.customer_product_name) {
        formData.customer_product_name = data.customer_product_name;
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
    purchaser_name: '',
    product_name: '',
    product_spec: '',
    customer_product_name: '',
    sale_num: 0,
    sale_price: 0,
    sale_date: dayjs(),
    remark: ''
  });
  modalTitle.value = '新增销售信息';
  modalVisible.value = true;
};

// 检查销售日期是否在已确定的对账单日期范围内
const checkSaleDateInStatementRange = async (purchaserName: string, saleDate: dayjs.Dayjs) => {
  try {
    // 获取该采购商的所有已确定对账单
    const response = await request({
      url: '/sale/bill/list',
      method: 'get',
      params: {
        purchaser_name: purchaserName,
        page_num: 1,
        page_size: 100
      }
    });
    
    const bills = response.data?.list || [];
    for (const bill of bills) {
      if (bill.end_date) {
        const startDate = dayjs(bill.start_date);
        const endDate = dayjs(bill.end_date);
        if (saleDate.isAfter(startDate.subtract(1, 'day')) && saleDate.isBefore(endDate.add(1, 'day'))) {
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

// 提交销售数据
const submitSaleData = async () => {
  const submitData = {
    ...formData,
    sale_date: typeof formData.sale_date === 'object' && formData.sale_date !== null && typeof (formData.sale_date as any).format === 'function' ? (formData.sale_date as any).format('YYYY-MM-DD') : undefined
  };
  
  if (formData.id) {
    await updateSaleInfo(submitData as UpdateSaleInfoReq);
    message.success('操作成功');
    modalVisible.value = false;
    fetchData();
  } else {
    await addSaleInfo(submitData as AddSaleInfoReq);
    message.success('操作成功');
    modalVisible.value = false;
    fetchData();
  }
};

const handleSubmit = async () => {
  try {
    const saleDate = dayjs.isDayjs(formData.sale_date) ? formData.sale_date : dayjs(formData.sale_date);
    
    // 检查销售日期是否在已确定的对账单日期范围内
    if (formData.purchaser_name) {
      const checkResult = await checkSaleDateInStatementRange(formData.purchaser_name, saleDate);
      if (checkResult.inRange) {
        Modal.confirm({
          title: '日期范围提醒',
          content: `您选择的销售日期(${saleDate.format('YYYY-MM-DD')})在已确定的对账单日期范围内(${checkResult.bill.start_date} 至 ${checkResult.bill.end_date})。继续添加可能会导致对账单发生改变，确定要继续吗？`,
          onOk: async () => {
            await submitSaleData();
          }
        });
        return;
      }
    }
    
    await submitSaleData();
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
      purchaser_name: '',
      product_name: '',
      product_spec: '',
      customer_product_name: '',
      sale_num: 0,
      sale_price: 0,
      sale_date: dayjs(),
      remark: ''
    });
  }
};

const handleDelete = (id: number) => {
  Modal.confirm({
    title: '确认删除',
    icon: () => h(ExclamationCircleOutlined),
    content: '删除后同步更新对账单、库存及利润，不可恢复',
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteSaleInfo({ id });
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
        const response = await getPurchaserSelect();
        purchaserOptions.value = response.data.map((name: string) => ({
          label: name,
          value: name
        }));
      } catch (error) {
        console.error('获取采购商列表失败:', error);
      }
    })(),
    (async () => {
      try {
        const response = await getSaleProductSelect({});
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
