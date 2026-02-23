<template>
  <div class="page-container">
    <h1>采购信息录入/查询</h1>
    
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
          style="width: 150px"
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
          style="width: 150px"
        />
      </a-form-item>
      <a-form-item label="采购日期">
        <a-range-picker
          v-model:value="dateRange"
          format="YYYY-MM-DD"
          style="width: 240px"
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
      :data-source="tableDataSource"
      :row-key="(record) => record.key || record.id"
      :pagination="{
        showSizeChanger: true,
        pageSizeOptions: ['10', '20', '50', '100'],
        showTotal: (total) => `共 ${total} 条记录`,
        total: total,
        current: searchParams.page_num,
        pageSize: searchParams.page_size,
        onChange: handlePageChange,
        onShowSizeChange: handlePageSizeChange
      }"
      :scroll="{ x: 1200 }"
      :loading="loading"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'supplier_name'">
          <template v-if="record.key === 'new-row'">
            <a-select
              v-model:value="newRow.supplier_name"
              placeholder="请选择供货商"
              show-search
              :filter-option="false"
              :options="supplierOptions"
              @search="handleSupplierSearch"
              @change="(val: any) => val && newRow.product_name && fetchNewRowLastPrice(val as string, newRow.product_name)"
              style="width: 100%"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-select
              v-model:value="editingRows[record.id].supplier_name"
              placeholder="请选择供货商"
              show-search
              :filter-option="false"
              :options="supplierOptions"
              @search="handleSupplierSearch"
              style="width: 100%"
            />
          </template>
          <template v-else>
            {{ record.supplier_name }}
          </template>
        </template>

        <template v-if="column.key === 'product_name'">
          <template v-if="record.key === 'new-row'">
            <a-select
              v-model:value="newRow.product_name"
              placeholder="请输入商品名称"
              show-search
              :filter-option="false"
              :options="newRowProductOptions"
              @search="handleNewRowProductSearch"
              @change="(val: any) => val && newRow.supplier_name && fetchNewRowLastPrice(newRow.supplier_name, val as string)"
              style="width: 100%"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-select
              v-model:value="editingRows[record.id].product_name"
              placeholder="请输入商品名称"
              show-search
              :filter-option="false"
              :options="productOptions"
              @search="handleProductSearch"
              style="width: 100%"
            />
          </template>
          <template v-else>
            {{ record.product_name }}
          </template>
        </template>

        <template v-if="column.key === 'product_spec'">
          <template v-if="record.key === 'new-row'">
            <a-input v-model:value="newRow.product_spec" placeholder="请输入规格" />
          </template>
          <template v-else-if="record.isEditing">
            <a-input v-model:value="editingRows[record.id].product_spec" placeholder="请输入规格" />
          </template>
          <template v-else>
            {{ record.product_spec || '-' }}
          </template>
        </template>

        <template v-if="column.key === 'purchase_num'">
          <template v-if="record.key === 'new-row'">
            <a-input-number
              v-model:value="newRow.purchase_num"
              :min="1"
              :step="1"
              :precision="0"
              placeholder="数量"
              style="width: 100%"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-input-number
              v-model:value="editingRows[record.id].purchase_num"
              :min="1"
              :step="1"
              :precision="0"
              placeholder="数量"
              style="width: 100%"
            />
          </template>
          <template v-else>
            {{ record.purchase_num }}
          </template>
        </template>

        <template v-if="column.key === 'purchase_price'">
          <template v-if="record.key === 'new-row'">
            <a-input-number
              v-model:value="newRow.purchase_price"
              :min="0.01"
              :step="0.01"
              :precision="2"
              placeholder="单价"
              style="width: 100%"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-input-number
              v-model:value="editingRows[record.id].purchase_price"
              :min="0.01"
              :step="0.01"
              :precision="2"
              placeholder="单价"
              style="width: 100%"
            />
          </template>
          <template v-else>
            {{ record.purchase_price ? record.purchase_price.toFixed(2) : '-' }}
          </template>
        </template>

        <template v-if="column.key === 'total_price'">
          <template v-if="record.key === 'new-row'">
            {{ ((newRow.purchase_num || 0) * (newRow.purchase_price || 0) * (Number(newRow.product_spec) || 0)).toFixed(2) }}
          </template>
          <template v-else-if="record.isEditing">
            {{ ((editingRows[record.id].purchase_num || 0) * (editingRows[record.id].purchase_price || 0) * (Number(editingRows[record.id].product_spec) || 0)).toFixed(2) }}
          </template>
          <template v-else>
            {{ record.total_price ? record.total_price.toFixed(2) : '-' }}
          </template>
        </template>

        <template v-if="column.key === 'purchase_date'">
          <template v-if="record.key === 'new-row'">
            <a-date-picker
              v-model:value="newRow.purchase_date"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-date-picker
              v-model:value="editingRows[record.id].purchase_date"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </template>
          <template v-else>
            {{ record.purchase_date }}
          </template>
        </template>

        <template v-if="column.key === 'remark'">
          <template v-if="record.key === 'new-row'">
            <a-input v-model:value="newRow.remark" placeholder="备注" />
          </template>
          <template v-else-if="record.isEditing">
            <a-input v-model:value="editingRows[record.id].remark" placeholder="备注" />
          </template>
          <template v-else>
            <a-tooltip v-if="record.remark && record.remark.length > 4" :title="record.remark">
              <span>{{ record.remark.substring(0, 4) }}...</span>
            </a-tooltip>
            <span v-else>{{ record.remark || '-' }}</span>
          </template>
        </template>

        <template v-if="column.key === 'action'">
          <template v-if="record.key === 'new-row'">
            <a-button type="primary" size="small" @click="handleAddNewRow" style="background-color: #52c41a; border-color: #52c41a">添</a-button>
          </template>
          <template v-else-if="record.isEditing">
            <a-button type="primary" size="small" @click="handleUpdateRow(record.id)" style="margin-right: 8px">保</a-button>
            <a-button size="small" @click="cancelEdit(record.id)">取</a-button>
          </template>
          <template v-else>
            <a-button size="small" @click="startEdit(record)" style="margin-right: 8px">编</a-button>
            <a-button size="small" danger @click="handleDelete(record.id)">删</a-button>
          </template>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import dayjs from 'dayjs';
import type { PurchaseInfoItem, AddPurchaseInfoReq, UpdatePurchaseInfoReq, PurchaseInfoListQuery } from '@/types';
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

const showSearch = ref(true);
const supplierOptions = ref<{ label: string; value: string }[]>([]);
const productOptions = ref<{ label: string; value: string }[]>([]); 
const searchProductOptions = ref<{ label: string; value: string }[]>([]);
const newRowProductOptions = ref<{ label: string; value: string }[]>([]);
const dataSource = ref<PurchaseInfoItem[]>([]);
const total = ref(0);
const loading = ref(false);
const dateRange = ref<any>(null);

const route = useRoute();

const searchParams = reactive<PurchaseInfoListQuery>({
  page_num: 1,
  page_size: 10,
  supplier_name: '',
  product_name: ''
});

const newRow = reactive<any>({
  key: 'new-row',
  supplier_name: '',
  product_name: '',
  product_spec: '',
  purchase_num: undefined,
  purchase_price: undefined,
  purchase_date: dayjs(),
  remark: '',
  supplier_id: undefined
});

const editingRows = ref<Record<number, any>>({});

const columns = [
  {
    title: '采购日期',
    dataIndex: 'purchase_date',
    key: 'purchase_date',
    sorter: true,
    ellipsis: true,
    width: 130
  },
  {
    title: '供货商名称',
    dataIndex: 'supplier_name',
    key: 'supplier_name',
    sorter: true,
    ellipsis: true,
    width: 150
  },
  {
    title: '商品名称',
    dataIndex: 'product_name',
    key: 'product_name',
    sorter: true,
    ellipsis: true,
    width: 150
  },
  {
    title: '商品规格',
    dataIndex: 'product_spec',
    key: 'product_spec',
    sorter: true,
    ellipsis: true,
    width: 100
  },
  {
    title: '采购数量',
    dataIndex: 'purchase_num',
    key: 'purchase_num',
    sorter: true,
    ellipsis: true,
    width: 100
  },
  { 
    title: '采购单价', 
    dataIndex: 'purchase_price', 
    key: 'purchase_price', 
    sorter: true, 
    ellipsis: true, 
    width: 100
  },
  { 
    title: '采购总价', 
    dataIndex: 'total_price', 
    key: 'total_price', 
    sorter: true, 
    ellipsis: true, 
    width: 100
  },
  {
    title: '备注',
    dataIndex: 'remark',
    key: 'remark',
    ellipsis: true,
    width: 120
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right' as const,
    width: 140
  }
];

const tableDataSource = computed(() => {
  const result: any[] = [{ ...newRow }];
  dataSource.value.forEach(item => {
    const isEditing = !!editingRows.value[item.id];
    if (isEditing) {
      result.push({
        ...item,
        isEditing: true
      });
    } else {
      result.push({
        ...item,
        isEditing: false
      });
    }
  });
  return result;
});

const fetchData = async (id?: number) => {
  loading.value = true;
  try {
    const queryParams: any = {
      ...searchParams,
      ...(id && { id })
    };
    
    // 添加日期范围参数
    if (dateRange.value && dateRange.value.length === 2) {
      queryParams.start_date = dateRange.value[0].format('YYYY-MM-DD');
      queryParams.end_date = dateRange.value[1].format('YYYY-MM-DD');
    }
    
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
  dateRange.value = null;
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

const handleNewRowProductSearch = async (value: string) => {
  newRow.product_name = value;
  try {
    const response = await selectPurchaseProduct({ keyword: value });
    let options: { label: string; value: string }[] = [];
    if (Array.isArray(response.data)) {
      options = response.data.map((name: string) => ({
        label: name,
        value: name
      }));
    }
    if (value) {
      newRowProductOptions.value = [
        { label: value, value: value },
        ...options.filter(option => option.value !== value)
      ];
    } else {
      newRowProductOptions.value = options;
    }
  } catch (error) {
    console.error('获取商品列表失败:', error);
    if (value) {
      newRowProductOptions.value = [{ label: value, value: value }];
    } else {
      newRowProductOptions.value = [];
    }
  }
};

const handleProductSearch = async (value: string) => {
  try {
    const response = await selectPurchaseProduct({ keyword: value });
    let options: { label: string; value: string }[] = [];
    if (Array.isArray(response.data)) {
      options = response.data.map((name: string) => ({
        label: name,
        value: name
      }));
    }
    if (value) {
      productOptions.value = [
        { label: value, value: value },
        ...options.filter(option => option.value !== value)
      ];
    } else {
      productOptions.value = options;
    }
  } catch (error) {
    console.error('获取商品列表失败:', error);
    if (value) {
      productOptions.value = [{ label: value, value: value }];
    } else {
      productOptions.value = [];
    }
  }
};

const handleSearchProductSearch = async (value: string) => {
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

const fetchNewRowLastPrice = async (supplierName: string, productName: string) => {
  try {
    const response = await getLastPurchasePrice({ supplier_name: supplierName, product_name: productName });
    const data = response.data;
    if (data) {
      if (data.purchase_price) {
        newRow.purchase_price = data.purchase_price;
      }
      if (data.product_spec) {
        newRow.product_spec = data.product_spec;
      }
    }
  } catch (error) {
    console.error('获取历史单价失败:', error);
  }
};

const checkPurchaseDateInStatementRange = async (supplierName: string, purchaseDate: dayjs.Dayjs) => {
  try {
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

const validateNewRow = () => {
  if (!newRow.supplier_name) {
    message.error('请选择供货商');
    return false;
  }
  if (!newRow.product_name) {
    message.error('请输入商品名称');
    return false;
  }
  if (!newRow.product_spec) {
    message.error('请输入商品规格');
    return false;
  }
  if (!newRow.purchase_num || newRow.purchase_num < 1) {
    message.error('请输入采购数量');
    return false;
  }
  if (!newRow.purchase_price || newRow.purchase_price < 0.01) {
    message.error('请输入采购单价');
    return false;
  }
  if (!newRow.purchase_date) {
    message.error('请选择采购日期');
    return false;
  }
  return true;
};

const handleAddNewRow = async () => {
  if (!validateNewRow()) return;

  try {
    const purchaseDate = dayjs.isDayjs(newRow.purchase_date) ? newRow.purchase_date : dayjs(newRow.purchase_date);
    
    if (newRow.supplier_name) {
      const checkResult = await checkPurchaseDateInStatementRange(newRow.supplier_name, purchaseDate);
      if (checkResult.inRange) {
        Modal.confirm({
          title: '日期范围提醒',
          content: `您选择的采购日期(${purchaseDate.format('YYYY-MM-DD')})在已确定的对账单日期范围内(${checkResult.bill.start_date} 至 ${checkResult.bill.end_date})。继续添加可能会导致对账单发生改变，确定要继续吗？`,
          onOk: async () => {
            await submitNewRow();
          }
        });
        return;
      }
    }
    
    await submitNewRow();
  } catch (error: any) {
    console.error('提交失败:', error);
    Modal.error({
      title: '操作失败',
      content: error.message || '服务器错误，请稍后重试'
    });
  }
};

const submitNewRow = async () => {
  const purchaseDate = dayjs.isDayjs(newRow.purchase_date) ? newRow.purchase_date : dayjs(newRow.purchase_date);
  const submitData = {
    supplier_name: newRow.supplier_name,
    product_name: newRow.product_name,
    product_spec: newRow.product_spec,
    purchase_num: newRow.purchase_num as number,
    purchase_price: newRow.purchase_price as number,
    purchase_date: purchaseDate.format('YYYY-MM-DD'),
    remark: newRow.remark,
    supplier_id: newRow.supplier_id
  };

  await addPurchaseInfo(submitData as unknown as AddPurchaseInfoReq);
  message.success('新增成功');
  
  Object.assign(newRow, {
    supplier_name: '',
    product_name: '',
    product_spec: '',
    purchase_num: undefined,
    purchase_price: undefined,
    purchase_date: dayjs(),
    remark: '',
    supplier_id: undefined
  });
  newRowProductOptions.value = [];
  
  fetchData();
};

const startEdit = (record: any) => {
  editingRows.value[record.id] = {
    supplier_name: record.supplier_name,
    product_name: record.product_name,
    product_spec: record.product_spec,
    purchase_num: record.purchase_num,
    purchase_price: record.purchase_price,
    purchase_date: dayjs(record.purchase_date),
    remark: record.remark
  };
};

const cancelEdit = (id: number) => {
  delete editingRows.value[id];
};

const validateEditRow = (id: number) => {
  const data = editingRows.value[id];
  if (!data) {
    message.error('编辑数据不存在');
    return false;
  }
  if (!data.supplier_name) {
    message.error('请选择供货商');
    return false;
  }
  if (!data.product_name) {
    message.error('请输入商品名称');
    return false;
  }
  if (!data.product_spec) {
    message.error('请输入商品规格');
    return false;
  }
  if (!data.purchase_num || data.purchase_num < 1) {
    message.error('请输入采购数量');
    return false;
  }
  if (!data.purchase_price || data.purchase_price < 0.01) {
    message.error('请输入采购单价');
    return false;
  }
  if (!data.purchase_date) {
    message.error('请选择采购日期');
    return false;
  }
  return true;
};

const handleUpdateRow = async (id: number) => {
  if (!validateEditRow(id)) return;

  try {
    const data = editingRows.value[id];
    const purchaseDate = dayjs.isDayjs(data.purchase_date) ? data.purchase_date : dayjs(data.purchase_date);
    
    const submitData = {
      id,
      supplier_name: data.supplier_name,
      product_name: data.product_name,
      product_spec: data.product_spec,
      purchase_num: data.purchase_num,
      purchase_price: data.purchase_price,
      purchase_date: purchaseDate.format('YYYY-MM-DD'),
      remark: data.remark
    };

    await updatePurchaseInfo(submitData as UpdatePurchaseInfoReq);
    message.success('修改成功');
    delete editingRows.value[id];
    fetchData();
  } catch (error: any) {
    console.error('修改失败:', error);
    Modal.error({
      title: '操作失败',
      content: error.message || '服务器错误，请稍后重试'
    });
  }
};

const handleDelete = (id: number) => {
  Modal.confirm({
    title: '确认删除',
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

.action-btn {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 2px;
  cursor: pointer;
  font-size: 12px;
  margin-right: 4px;
}

.action-btn.add {
  background-color: #52c41a;
  color: #fff;
}

.action-btn.edit {
  background-color: #1890ff;
  color: #fff;
}

.action-btn.save {
  background-color: #1890ff;
  color: #fff;
}

.action-btn.cancel {
  background-color: #d9d9d9;
  color: #000;
}

.action-btn.delete {
  background-color: #ff4d4f;
  color: #fff;
}
</style>
