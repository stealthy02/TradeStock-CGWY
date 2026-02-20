<template>
  <div class="page-container">
    <h1>销售信息录入/查询</h1>
    
    <a-form
      v-if="showSearch"
      :model="searchParams"
      layout="inline"
      style="margin-bottom: 16px"
    >
      <a-form-item label="客户名称">
        <a-select
          v-model:value="searchParams.purchaser_name"
          placeholder="请选择客户"
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
      :scroll="{ x: 1300 }"
      :loading="loading"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'purchaser_name'">
          <template v-if="record.key === 'new-row'">
            <a-select
              v-model:value="newRow.purchaser_name"
              placeholder="请选择客户"
              show-search
              :filter-option="false"
              :options="purchaserOptions"
              @search="handlePurchaserSearch"
              @change="(val: any) => val && newRow.product_name && fetchNewRowLastPrice(val as string, newRow.product_name)"
              style="width: 100%"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-select
              v-model:value="editingRows[record.id].purchaser_name"
              placeholder="请选择客户"
              show-search
              :filter-option="false"
              :options="purchaserOptions"
              @search="handlePurchaserSearch"
              @change="(val: any) => val && editingRows[record.id].product_name && fetchEditingRowLastPrice(record.id, val as string, editingRows[record.id].product_name)"
              style="width: 100%"
            />
          </template>
          <template v-else>{{ record.purchaser_name }}</template>
        </template>
        <template v-else-if="column.key === 'product_name'">
          <template v-if="record.key === 'new-row'">
            <a-select
              v-model:value="newRow.product_name"
              placeholder="请输入商品名称"
              show-search
              :filter-option="false"
              :options="newRowProductOptions"
              @search="handleNewRowProductSearch"
              @change="(val: any) => val && newRow.purchaser_name && fetchNewRowLastPrice(newRow.purchaser_name, val as string)"
              style="width: 100%"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-select
              v-model:value="editingRows[record.id].product_name"
              placeholder="请输入商品名称"
              show-search
              :filter-option="false"
              :options="editingRowProductOptions[record.id] || []"
              @search="(val: string) => handleEditingRowProductSearch(record.id, val)"
              @change="(val: any) => val && editingRows[record.id].purchaser_name && fetchEditingRowLastPrice(record.id, editingRows[record.id].purchaser_name, val as string)"
              style="width: 100%"
            />
          </template>
          <template v-else>{{ record.product_name }}</template>
        </template>
        <template v-else-if="column.key === 'product_spec'">
          <template v-if="record.key === 'new-row'">
            <a-input
              v-model:value="newRow.product_spec"
              placeholder="请输入商品规格，例如：30"
              @change="calculateNewRowTotalFromPrice"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-input
              v-model:value="editingRows[record.id].product_spec"
              placeholder="请输入商品规格，例如：30"
              @change="() => calculateEditingRowTotalFromPrice(record.id)"
            />
          </template>
          <template v-else>{{ record.product_spec }}</template>
        </template>
        <template v-else-if="column.key === 'customer_product_name'">
          <template v-if="record.key === 'new-row'">
            <a-input
              v-model:value="newRow.customer_product_name"
              placeholder="请输入客户侧商品名"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-input
              v-model:value="editingRows[record.id].customer_product_name"
              placeholder="请输入客户侧商品名"
            />
          </template>
          <template v-else>{{ record.customer_product_name }}</template>
        </template>
        <template v-else-if="column.key === 'sale_num'">
          <template v-if="record.key === 'new-row'">
            <a-input-number
              v-model:value="newRow.sale_num"
              :min="1"
              :step="1"
              :precision="0"
              placeholder="请输入销售数量"
              style="width: 100%"
              @change="calculateNewRowTotalFromPrice"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-input-number
              v-model:value="editingRows[record.id].sale_num"
              :min="1"
              :step="1"
              :precision="0"
              placeholder="请输入销售数量"
              style="width: 100%"
              @change="() => calculateEditingRowTotalFromPrice(record.id)"
            />
          </template>
          <template v-else>{{ record.sale_num }}</template>
        </template>
        <template v-else-if="column.key === 'sale_price'">
          <template v-if="record.key === 'new-row'">
            <a-input-number
              v-model:value="newRow.sale_price"
              :min="0.01"
              :step="0.01"
              :precision="2"
              placeholder="请输入销售单价"
              style="width: 100%"
              @change="calculateNewRowTotalFromPrice"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-input-number
              v-model:value="editingRows[record.id].sale_price"
              :min="0.01"
              :step="0.01"
              :precision="2"
              placeholder="请输入销售单价"
              style="width: 100%"
              @change="() => calculateEditingRowTotalFromPrice(record.id)"
            />
          </template>
          <template v-else>{{ record.sale_price?.toFixed(2) }}</template>
        </template>
        <template v-else-if="column.key === 'total_price'">
          <template v-if="record.key === 'new-row'">
            <a-input-number
              v-model:value="newRow.total_price"
              :min="0.01"
              :step="0.01"
              :precision="2"
              placeholder="请输入销售总价"
              style="width: 100%"
              @change="calculateNewRowPriceFromTotal"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-input-number
              v-model:value="editingRows[record.id].total_price"
              :min="0.01"
              :step="0.01"
              :precision="2"
              placeholder="请输入销售总价"
              style="width: 100%"
              @change="() => calculateEditingRowPriceFromTotal(record.id)"
            />
          </template>
          <template v-else>{{ record.total_price?.toFixed(2) }}</template>
        </template>
        <template v-else-if="column.key === 'total_profit'">
          <template v-if="record.key === 'new-row'">-</template>
          <template v-else-if="record.isEditing">-</template>
          <template v-else>{{ record.total_profit?.toFixed(2) }}</template>
        </template>
        <template v-else-if="column.key === 'sale_date'">
          <template v-if="record.key === 'new-row'">
            <a-date-picker
              v-model:value="newRow.sale_date"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-date-picker
              v-model:value="editingRows[record.id].sale_date"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </template>
          <template v-else>{{ record.sale_date }}</template>
        </template>
        <template v-else-if="column.key === 'remark'">
          <template v-if="record.key === 'new-row'">
            <a-textarea
              v-model:value="newRow.remark"
              :rows="1"
              :maxLength="200"
              placeholder="请输入备注信息"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-textarea
              v-model:value="editingRows[record.id].remark"
              :rows="1"
              :maxLength="200"
              placeholder="请输入备注信息"
            />
          </template>
          <template v-else>
            <a-tooltip :title="record.remark" v-if="record.remark">
              {{ record.remark.length > 4 ? record.remark.substring(0, 4) + '...' : record.remark }}
            </a-tooltip>
            <template v-else>-</template>
          </template>
        </template>
        <template v-else-if="column.key === 'action'">
          <template v-if="record.key === 'new-row'">
            <a-button type="primary" size="small" @click="handleAdd" style="background-color: #52c41a; border-color: #52c41a">添</a-button>
          </template>
          <template v-else-if="record.isEditing">
            <a-button type="primary" size="small" @click="handleSave(record.id)" style="margin-right: 8px">保</a-button>
            <a-button size="small" @click="handleCancelEdit(record.id)">取</a-button>
          </template>
          <template v-else>
            <a-button size="small" @click="handleEdit(record)" style="margin-right: 8px">编</a-button>
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

const showSearch = ref(true);
const purchaserOptions = ref<any[]>([]);
const productOptions = ref<any[]>([]);
const searchProductOptions = ref<any[]>([]);
const newRowProductOptions = ref<any[]>([]);
const editingRowProductOptions = ref<Record<number, any[]>>({});
const dataSource = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const editingRows = ref<Record<number, any>>({});

const route = useRoute();

const searchParams = reactive<SaleInfoListQuery>({
  page_num: 1,
  page_size: 10
});

const newRow = reactive<any>({
  key: 'new-row',
  purchaser_name: '',
  product_name: '',
  product_spec: '',
  customer_product_name: '',
  sale_num: undefined,
  sale_price: undefined,
  total_price: undefined,
  sale_date: dayjs(),
  remark: '',
  purchaser_id: undefined
});

const tableDataSource = computed(() => {
  const result: any[] = [{ ...newRow }];
  dataSource.value.forEach(item => {
    const isEditing = !!editingRows.value[item.id];
    result.push({ ...item, isEditing });
  });
  return result;
});

const columns = computed(() => [
  {
    title: '销售日期',
    dataIndex: 'sale_date',
    key: 'sale_date',
    sorter: true,
    ellipsis: true,
    width: 130
  },
  {
    title: '客户名',
    dataIndex: 'purchaser_name',
    key: 'purchaser_name',
    sorter: true,
    ellipsis: true,
    width: 110
  },
  {
    title: '商品名称',
    dataIndex: 'product_name',
    key: 'product_name',
    sorter: true,
    ellipsis: true,
    width: 110
  },
  {
    title: '规格',
    dataIndex: 'product_spec',
    key: 'product_spec',
    sorter: true,
    ellipsis: true,
    width: 90
  },
  {
    title: '销售名',
    dataIndex: 'customer_product_name',
    key: 'customer_product_name',
    sorter: true,
    ellipsis: true,
    width: 110
  },
  {
    title: '销售数量',
    dataIndex: 'sale_num',
    key: 'sale_num',
    sorter: true,
    ellipsis: true,
    width: 90
  },
  { 
    title: '销售单价', 
    dataIndex: 'sale_price', 
    key: 'sale_price', 
    sorter: true, 
    ellipsis: true, 
    width: 100
  },
  { 
    title: '销售总价', 
    dataIndex: 'total_price', 
    key: 'total_price', 
    sorter: true, 
    ellipsis: true, 
    width: 100
  },
  { 
    title: '商品总利润', 
    dataIndex: 'total_profit', 
    key: 'total_profit', 
    sorter: true, 
    ellipsis: true, 
    width: 110
  },
  {
    title: '备注',
    dataIndex: 'remark',
    key: 'remark',
    ellipsis: true,
    width: 100
  },
  { 
    title: '操作',
    key: 'action',
    fixed: 'right' as const,
    width: 140
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
    console.error('获取客户列表失败:', error);
  }
};

const handleSearchProductSearch = async (value: string) => {
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

const handleNewRowProductSearch = async (value: string) => {
  try {
    const response = await getSaleProductSelect({ keyword: value });
    if (Array.isArray(response.data)) {
      newRowProductOptions.value = response.data.map((name: string) => ({
        label: name,
        value: name
      }));
    } else {
      newRowProductOptions.value = [];
    }
  } catch (error) {
    console.error('获取商品列表失败:', error);
    newRowProductOptions.value = [];
  }
};

const handleEditingRowProductSearch = async (id: number, value: string) => {
  try {
    const response = await getSaleProductSelect({ keyword: value });
    if (Array.isArray(response.data)) {
      editingRowProductOptions.value[id] = response.data.map((name: string) => ({
        label: name,
        value: name
      }));
    } else {
      editingRowProductOptions.value[id] = [];
    }
  } catch (error) {
    console.error('获取商品列表失败:', error);
    editingRowProductOptions.value[id] = [];
  }
};

const fetchNewRowLastPrice = async (purchaserName: string, productName: string) => {
  try {
    const response = await getLastSalePrice({
      purchaser_name: purchaserName,
      product_name: productName
    });
    
    const data = response.data;
    if (data) {
      if (data.sale_price) {
        newRow.sale_price = data.sale_price;
        calculateNewRowTotalFromPrice();
      }
      if (data.customer_product_name) {
        newRow.customer_product_name = data.customer_product_name;
      }
      if (data.product_spec) {
        newRow.product_spec = data.product_spec;
        calculateNewRowTotalFromPrice();
      }
    }
  } catch (error) {
    console.error('获取历史单价失败:', error);
  }
};

const fetchEditingRowLastPrice = async (id: number, purchaserName: string, productName: string) => {
  try {
    const response = await getLastSalePrice({
      purchaser_name: purchaserName,
      product_name: productName
    });
    
    const data = response.data;
    if (data && editingRows.value[id]) {
      if (data.sale_price) {
        editingRows.value[id].sale_price = data.sale_price;
        calculateEditingRowTotalFromPrice(id);
      }
      if (data.customer_product_name) {
        editingRows.value[id].customer_product_name = data.customer_product_name;
      }
      if (data.product_spec) {
        editingRows.value[id].product_spec = data.product_spec;
        calculateEditingRowTotalFromPrice(id);
      }
    }
  } catch (error) {
    console.error('获取历史单价失败:', error);
  }
};

const checkSaleDateInStatementRange = async (purchaserName: string, saleDate: dayjs.Dayjs) => {
  try {
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

const handleAdd = async () => {
  if (!newRow.purchaser_name || !newRow.product_name || !newRow.product_spec || !newRow.sale_num || !newRow.sale_price || !newRow.sale_date) {
    message.error('请填写必填项');
    return;
  }

  try {
    const saleDate = dayjs.isDayjs(newRow.sale_date) ? newRow.sale_date : dayjs(newRow.sale_date);
    
    if (newRow.purchaser_name) {
      const checkResult = await checkSaleDateInStatementRange(newRow.purchaser_name, saleDate);
      if (checkResult.inRange) {
        Modal.confirm({
          title: '日期范围提醒',
          content: `您选择的销售日期(${saleDate.format('YYYY-MM-DD')})在已确定的对账单日期范围内(${checkResult.bill.start_date} 至 ${checkResult.bill.end_date})。继续添加可能会导致对账单发生改变，确定要继续吗？`,
          onOk: async () => {
            await submitAdd();
          }
        });
        return;
      }
    }
    
    await submitAdd();
  } catch (error: any) {
    console.error('添加失败:', error);
    Modal.error({
      title: '添加失败',
      content: error.message || '服务器错误，请稍后重试'
    });
  }
};

const submitAdd = async () => {
  const submitData = {
    ...newRow,
    total_price: newRow.total_price,
    sale_date: typeof newRow.sale_date === 'object' && newRow.sale_date !== null && typeof (newRow.sale_date as any).format === 'function' ? (newRow.sale_date as any).format('YYYY-MM-DD') : undefined
  };
  
  delete submitData.key;
  
  await addSaleInfo(submitData as AddSaleInfoReq);
  message.success('添加成功');
  
  Object.assign(newRow, {
    purchaser_name: '',
    product_name: '',
    product_spec: '',
    customer_product_name: '',
    sale_num: undefined,
    sale_price: undefined,
    total_price: undefined,
    sale_date: dayjs(),
    remark: '',
    purchaser_id: undefined
  });
  
  fetchData();
};

const handleEdit = (record: any) => {
  editingRows.value[record.id] = {
    ...record,
    sale_date: dayjs(record.sale_date),
    total_price: record.total_price
  };
  editingRowProductOptions.value[record.id] = [...productOptions.value];
};

const handleCancelEdit = (id: number) => {
  delete editingRows.value[id];
  delete editingRowProductOptions.value[id];
};

const handleSave = async (id: number) => {
  const row = editingRows.value[id];
  if (!row.purchaser_name || !row.product_name || !row.product_spec || !row.sale_num || !row.sale_price || !row.sale_date) {
    message.error('请填写必填项');
    return;
  }

  try {
    const saleDate = dayjs.isDayjs(row.sale_date) ? row.sale_date : dayjs(row.sale_date);
    
    if (row.purchaser_name) {
      const checkResult = await checkSaleDateInStatementRange(row.purchaser_name, saleDate);
      if (checkResult.inRange) {
        Modal.confirm({
          title: '日期范围提醒',
          content: `您选择的销售日期(${saleDate.format('YYYY-MM-DD')})在已确定的对账单日期范围内(${checkResult.bill.start_date} 至 ${checkResult.bill.end_date})。继续添加可能会导致对账单发生改变，确定要继续吗？`,
          onOk: async () => {
            await submitSave(id);
          }
        });
        return;
      }
    }
    
    await submitSave(id);
  } catch (error: any) {
    console.error('保存失败:', error);
    Modal.error({
      title: '保存失败',
      content: error.message || '服务器错误，请稍后重试'
    });
  }
};

const submitSave = async (id: number) => {
  const row = editingRows.value[id];
  const submitData = {
    id,
    purchaser_name: row.purchaser_name,
    product_name: row.product_name,
    product_spec: row.product_spec,
    customer_product_name: row.customer_product_name,
    sale_num: row.sale_num as number,
    sale_price: row.sale_price as number,
    total_price: row.total_price,
    sale_date: typeof row.sale_date === 'object' && row.sale_date !== null && typeof (row.sale_date as any).format === 'function' ? (row.sale_date as any).format('YYYY-MM-DD') : undefined,
    remark: row.remark
  };
  
  await updateSaleInfo(submitData as UpdateSaleInfoReq);
  message.success('保存成功');
  delete editingRows.value[id];
  delete editingRowProductOptions.value[id];
  fetchData();
};

const handleDelete = (id: number) => {
  Modal.confirm({
    title: '确认删除',
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

const calculateNewRowTotalFromPrice = () => {
  if (newRow.sale_price && newRow.sale_num) {
    const spec = Number(newRow.product_spec) || 1;
    newRow.total_price = newRow.sale_price * newRow.sale_num * spec;
  }
};

const calculateNewRowPriceFromTotal = () => {
  if (newRow.total_price && newRow.sale_num) {
    const spec = Number(newRow.product_spec) || 1;
    newRow.sale_price = newRow.total_price / (newRow.sale_num * spec);
  }
};

const calculateEditingRowTotalFromPrice = (id: number) => {
  const row = editingRows.value[id];
  if (row && row.sale_price && row.sale_num) {
    const spec = Number(row.product_spec) || 1;
    row.total_price = row.sale_price * row.sale_num * spec;
  }
};

const calculateEditingRowPriceFromTotal = (id: number) => {
  const row = editingRows.value[id];
  if (row && row.total_price && row.sale_num) {
    const spec = Number(row.product_spec) || 1;
    row.sale_price = row.total_price / (row.sale_num * spec);
  }
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
        console.error('获取客户列表失败:', error);
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
          newRowProductOptions.value = productOptions.value;
        } else {
          productOptions.value = [];
          searchProductOptions.value = [];
          newRowProductOptions.value = [];
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
</style>
