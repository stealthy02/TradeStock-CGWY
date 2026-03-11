<template>
  <div class="page-container">
    <!-- 商品选择栏 -->
    <div class="product-select-bar">
      <Select
        v-model:value="selectedProduct"
        placeholder="请输入商品名称"
        style="width: 200px"
        show-search
        :filter-option="false"
        @search="handleProductSearch"
        @change="handleProductChange"
      >
        <Option
          v-for="product in productList"
          :key="product"
          :value="product"
          :label="product"
        >
          {{ product }}
        </Option>
      </Select>
      <Select
        v-model:value="selectedSpec"
        placeholder="请选择商品型号"
        style="width: 180px; margin-left: 16px"
        @change="handleSpecChange"
      >
        <Option
          v-for="spec in specList"
          :key="spec"
          :value="spec"
          :label="spec"
        >
          {{ spec }}
        </Option>
      </Select>
    </div>

    <!-- 顶部信息卡片 -->
    <Card class="info-card" v-if="inventoryInfo">
      <Row :gutter="[16, 16]">
        <Col :span="6">
          <div class="info-item">
            <div class="info-label">商品名称</div>
            <div class="info-value">{{ inventoryInfo.product_name }}</div>
          </div>
        </Col>
        <Col :span="6">
          <div class="info-item">
            <div class="info-label">商品规格</div>
            <div class="info-value">{{ inventoryInfo.product_spec }}</div>
          </div>
        </Col>
        <Col :span="6">
          <div class="info-item">
            <div class="info-label">当前库存数量</div>
            <div class="info-value">{{ inventoryInfo.inventory_num }}</div>
          </div>
        </Col>
        <Col :span="6">
          <div class="info-item">
            <div class="info-label">库存单位成本</div>
            <div class="info-value">{{ inventoryInfo.inventory_cost }}</div>
          </div>
        </Col>
        <Col :span="6">
          <div class="info-item">
            <div class="info-label">当前库存价值</div>
            <div class="info-value">{{ inventoryInfo.inventory_value }}</div>
          </div>
        </Col>
      </Row>
    </Card>

    <!-- 核心数据表格 -->
    <Table
      :columns="columns"
      :data-source="dataSource"
      :row-key="(record: any) => record.id"
      :pagination="{
        current: pagination.current,
        pageSize: pagination.pageSize,
        total: pagination.total,
        showSizeChanger: true,
        showQuickJumper: true,
        onChange: handlePaginationChange,
        onShowSizeChange: handlePaginationSizeChange,
      }"
      class="flow-table"
      :loading="loading"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue';
import { useRouter } from 'vue-router';
import { Select, Card, Row, Col, Tag, Button, Table } from 'ant-design-vue';
import type { SelectValue } from 'ant-design-vue/es/select';
import { getInventoryDetail, getInventoryList } from '@/api/inventory';
import { selectPurchaseProduct } from '@/api/purchase';
import { InventoryDetailQuery, InventoryInfo, InventoryChangeRecordItem, InventoryChangeType, InventoryItem } from '@/types';

const { Option } = Select;

// 路由实例
const router = useRouter();

// 商品列表
const productList = ref<any[]>([]);
// 规格列表
const specList = ref<string[]>([]);
// 当前选择的商品
const selectedProduct = ref<string>('');
// 当前选择的商品规格
const selectedSpec = ref<string>('');
// 库存信息
const inventoryInfo = ref<InventoryInfo | null>(null);
// 搜索参数
const searchParams = reactive<InventoryDetailQuery>({
  product_name: '',
  product_spec: '',
  page_num: 1,
  page_size: 10,
});
// 数据源
const dataSource = ref<InventoryChangeRecordItem[]>([]);
// 分页信息
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
});
// 加载状态
const loading = ref<boolean>(false);

// 获取商品列表
const fetchProductList = async () => {
  try {
    const response = await selectPurchaseProduct();
    if (Array.isArray(response.data)) {
      productList.value = response.data;
      // 默认选择第一个商品
      if (productList.value.length > 0) {
        selectedProduct.value = productList.value[0];
        handleProductChange(productList.value[0]);
      }
    }
  } catch (error) {
    console.error('获取商品列表失败:', error);
  }
};

// 获取商品规格列表
const fetchSpecList = async (productName: string) => {
  try {
    // 传入商品名称参数，只获取对应商品的库存列表
    const response = await getInventoryList({ product_name: productName });
    if (response.data.list) {
      // 提取规格列表并去重
      const specs = response.data.list
        .map((item: InventoryItem) => item.product_spec)
        .filter((spec: string, index: number, self: string[]) => self.indexOf(spec) === index); // 去重
      specList.value = specs;
      
      // 如果有规格，默认选择第一个
      if (specs.length > 0) {
        selectedSpec.value = specs[0];
        searchParams.product_spec = specs[0];
        fetchData();
      } else {
        selectedSpec.value = '';
        searchParams.product_spec = '';
      }
    }
  } catch (error) {
    console.error('获取规格列表失败:', error);
    specList.value = [];
  }
};

// 处理商品搜索
const handleProductSearch = async (value: string) => {
  if (!value) return;
  try {
    const response = await selectPurchaseProduct({ keyword: value });
    if (Array.isArray(response.data)) {
      productList.value = response.data;
    }
  } catch (error) {
    console.error('获取商品列表失败:', error);
  }
};

// 处理商品切换
const handleProductChange = (value: SelectValue) => {
  selectedProduct.value = value as string;
  searchParams.product_name = value as string;
  searchParams.page_num = 1;
  pagination.current = 1;
  // 获取该商品的规格列表
  fetchSpecList(value as string);
};

// 处理规格切换
const handleSpecChange = () => {
  searchParams.product_spec = selectedSpec.value;
  searchParams.page_num = 1;
  pagination.current = 1;
  fetchData();
};

// 获取库存详情和变动记录
const fetchData = async () => {
  try {
    loading.value = true;
    // 确保 product_name 和 product_spec 不为空
    if (!searchParams.product_name || !searchParams.product_spec) {
      console.warn('商品名称和规格不能为空');
      return;
    }
    const response = await getInventoryDetail({
      product_name: searchParams.product_name,
      product_spec: searchParams.product_spec,
      start_date: searchParams.start_date,
      end_date: searchParams.end_date,
      page_num: searchParams.page_num,
      page_size: searchParams.page_size,
    });
    inventoryInfo.value = response.data.inventory_info;
    dataSource.value = response.data.change_record.list;
    pagination.total = response.data.change_record.total;
  } catch (error) {
    console.error('获取库存详情失败:', error);
    dataSource.value = [];
    pagination.total = 0;
  } finally {
    loading.value = false;
  }
};

// 处理分页变化
const handlePaginationChange = (current: number) => {
  pagination.current = current;
  searchParams.page_num = current;
  fetchData();
};

// 处理分页大小变化
const handlePaginationSizeChange = (_: number, pageSize: number) => {
  pagination.pageSize = pageSize;
  pagination.current = 1;
  searchParams.page_size = pageSize;
  searchParams.page_num = 1;
  fetchData();
};

// 表格列配置
const columns = [
  {
    title: '操作时间',
    dataIndex: 'change_date',
    key: 'change_date',
    sorter: true,
    customRender: ({ text }: { text: string }) => {
      if (!text) return { children: '' };
      // 只保留日期部分，去掉时间
      const datePart = text.split(' ')[0];
      return {
        children: datePart
      };
    },
  },
  {
    title: '操作类型',
    dataIndex: 'change_type',
    key: 'change_type',
    customRender: ({ text }: { text: InventoryChangeType }) => {
      let color = '';
      switch (text) {
        case InventoryChangeType.PURCHASE_IN:
          color = 'green';
          break;
        case InventoryChangeType.SALE_OUT:
          color = 'blue';
          break;
        case InventoryChangeType.LOSS:
          color = 'red';
          break;
        case InventoryChangeType.INIT:
          color = 'orange';
          break;
        default:
          color = 'default';
      }
      return {
        children: h(Tag, { color }, () => text)
      };
    },
  },
  {
    title: '变动前数量',
    dataIndex: 'stock_before',
    key: 'stock_before',
    customRender: ({ record }: { record: any }) => {
      return {
        children: record.stock_before || 0
      };
    },
  },
  {
    title: '变化量',
    dataIndex: 'change_num',
    key: 'change_num',
    customRender: ({ text }: { text: number }) => {
      const prefix = text > 0 ? '+' : '';
      return {
        children: `${prefix}${text}`
      };
    },
  },
  {
    title: '操作后库存量',
    dataIndex: 'stock_after',
    key: 'stock_after',
    customRender: ({ record }: { record: any }) => {
      return {
        children: record.stock_after || 0
      };
    },
  },
  {
    title: '操作来源',
    dataIndex: 'remark',
    key: 'remark',
    customRender: ({ text }: { text: string }) => {
      return {
        children: text || '-'
      };
    },
  },
  {
    title: '操作跳转',
    dataIndex: 'action',
    key: 'action',
    customRender: ({ record }: { record: InventoryChangeRecordItem }) => {
      const handleJump = () => {
        switch (record.change_type) {
          case InventoryChangeType.PURCHASE_IN:
            router.push({
              path: '/layout/purchase/info',
              query: {
                id: record.related_id,
              },
            });
            break;
          case InventoryChangeType.SALE_OUT:
            router.push({
              path: '/layout/sale/info',
              query: {
                id: record.related_id,
              },
            });
            break;
          case InventoryChangeType.LOSS:
            router.push({
              path: '/layout/inventory/loss',
              query: {
                id: record.related_id,
              },
            });
            break;
          case InventoryChangeType.INIT:
            router.push({
              path: '/layout/inventory/init',
              query: {
                id: record.related_id,
              },
            });
            break;
          default:
            break;
        }
      };
      return {
        children: h(Button, { type: 'link', size: 'small', onClick: handleJump }, () => '跳转')
      };
    },
  },
];

// 组件挂载时获取商品列表
onMounted(() => {
  fetchProductList();
});
</script>

<style scoped>
.page-container {
  padding: 20px;
  height: 100%;
  background-color: #f5f5f5;
}

.product-select-bar {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
}

.info-card {
  margin-bottom: 20px;
}

.info-item {
  text-align: center;
}

.info-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.info-value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.flow-table {
  background-color: #fff;
  border-radius: 8px;
}
</style>