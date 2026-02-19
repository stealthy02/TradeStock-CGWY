<template>
  <div class="page-container">
    <h1>当前库存查询</h1>
    
    <a-form
      v-if="showSearch"
      :model="searchParams"
      layout="inline"
      style="margin-bottom: 16px"
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
      <a-form-item label="库存数量范围">
        <a-input-number
          v-model:value="searchParams.min_num"
          :min="0"
          placeholder="最小数量"
          style="width: 100px"
        />
        <span style="margin: 0 8px">-</span>
        <a-input-number
          v-model:value="searchParams.max_num"
          :min="0"
          placeholder="最大数量"
          style="width: 100px"
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
      :row-key="(record) => `${record.product_name}-${record.product_spec}`"
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import type { InventoryListQuery } from '@/types';
import { getInventoryList } from '@/api/inventory';
import { selectPurchaseProduct } from '@/api/purchase';

const showSearch = ref(true);
const dataSource = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const productOptions = ref<{ label: string; value: string }[]>([]);

const searchParams = reactive<InventoryListQuery>({
  page_num: 1,
  page_size: 10
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
    title: '当前库存数量',
    dataIndex: 'inventory_num',
    key: 'inventory_num',
    sorter: true,
    ellipsis: true,
    width: 120
  },
  { 
    title: '库存单位成本', 
    dataIndex: 'inventory_cost', 
    key: 'inventory_cost', 
    sorter: true, 
    ellipsis: true, 
    width: 150,
    customRender: (opt: any) => opt.record.inventory_cost.toFixed(2) 
  },
  { 
    title: '库存总价值', 
    dataIndex: 'inventory_value', 
    key: 'inventory_value', 
    sorter: true, 
    ellipsis: true, 
    width: 150,
    customRender: (opt: any) => opt.record.inventory_value.toFixed(2) 
  },
  {
    title: '最后采购日期',
    dataIndex: 'last_purchase_date',
    key: 'last_purchase_date',
    sorter: true,
    ellipsis: true,
    width: 150
  },
  {
    title: '最后销售日期',
    dataIndex: 'last_sale_date',
    key: 'last_sale_date',
    sorter: true,
    ellipsis: true,
    width: 150,
    customRender: (opt: any) => opt.record.last_sale_date || '-'
  }
]) as any;

const fetchData = async () => {
  loading.value = true;
  try {
    const response = await getInventoryList(searchParams);
    
    dataSource.value = response.data.list;
    total.value = response.data.total;
  } catch (error) {
    console.error('获取库存列表失败:', error);
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

const handleProductSearch = async (value: string) => {
  if (!value) return;
  try {
    const response = await selectPurchaseProduct({ keyword: value });
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

const resetSearch = () => {
  searchParams.page_num = 1;
  searchParams.page_size = 10;
  searchParams.product_name = '';
  searchParams.min_num = undefined;
  searchParams.max_num = undefined;
  productOptions.value = [];
  fetchData();
};



onMounted(async () => {
  try {
    const response = await selectPurchaseProduct({});
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
</style>
