<template>
  <div class="page-container">
    <h1>库存报损录入/查询</h1>
    
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
      :data-source="tableDataSource"
      :row-key="(record) => record.key || record.id"
      :pagination="false"
      :scroll="{ x: 1400 }"
      :loading="loading"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'product_name'">
          <template v-if="record.key === 'new-row'">
            <a-select
              v-model:value="newRow.product_name"
              placeholder="请选择商品"
              show-search
              :filter-option="false"
              :options="productOptions"
              @search="handleProductSearch"
              @focus="handleProductFocus"
              @change="handleNewRowProductChange"
              style="width: 100%"
            />
            <div v-if="newRowCurrentInventory" style="margin-top: 8px; color: #52c41a; font-size: 12px">
              当前库存：{{ newRowCurrentInventory.inventory_num }}
            </div>
          </template>
          <template v-else-if="record.isEditing">
            <a-select
              v-model:value="editingRows[record.id].product_name"
              placeholder="请选择商品"
              show-search
              :filter-option="false"
              :options="productOptions"
              @search="handleProductSearch"
              @change="(val: any) => handleEditingRowProductChange(record.id, val)"
              style="width: 100%"
            />
            <div v-if="editingRowCurrentInventory[record.id]" style="margin-top: 8px; color: #52c41a; font-size: 12px">
              当前库存：{{ editingRowCurrentInventory[record.id]?.inventory_num }}
            </div>
          </template>
          <template v-else>{{ record.product_name }}</template>
        </template>
        <template v-else-if="column.key === 'product_spec'">
          <template v-if="record.key === 'new-row'">
            <a-input
              v-model:value="newRow.product_spec"
              placeholder="请输入商品规格，例如：30"
              style="width: 100%"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-input
              v-model:value="editingRows[record.id].product_spec"
              placeholder="请输入商品规格，例如：30"
              style="width: 100%"
            />
          </template>
          <template v-else>{{ record.product_spec }}</template>
        </template>
        <template v-else-if="column.key === 'loss_num'">
          <template v-if="record.key === 'new-row'">
            <a-input-number
              v-model:value="newRow.loss_num"
              :min="1"
              :step="1"
              :precision="0"
              placeholder="请输入报损数量"
              style="width: 100%"
            />
            <div v-if="newRowInventoryError" style="color: #ff4d4f; font-size: 12px; margin-top: 4px">
              {{ newRowInventoryError }}
            </div>
          </template>
          <template v-else-if="record.isEditing">
            <a-input-number
              v-model:value="editingRows[record.id].loss_num"
              :min="1"
              :step="1"
              :precision="0"
              placeholder="请输入报损数量"
              style="width: 100%"
            />
            <div v-if="editingRowInventoryError[record.id]" style="color: #ff4d4f; font-size: 12px; margin-top: 4px">
              {{ editingRowInventoryError[record.id] }}
            </div>
          </template>
          <template v-else>{{ record.loss_num }}</template>
        </template>
        <template v-else-if="column.key === 'lossUnitCost'">
          <template v-if="record.key === 'new-row'">-</template>
          <template v-else-if="record.isEditing">-</template>
          <template v-else>{{ record.lossUnitCost?.toFixed(2) || '0.00' }}</template>
        </template>
        <template v-else-if="column.key === 'losstotal_cost'">
          <template v-if="record.key === 'new-row'">-</template>
          <template v-else-if="record.isEditing">-</template>
          <template v-else>{{ record.losstotal_cost?.toFixed(2) || '0.00' }}</template>
        </template>
        <template v-else-if="column.key === 'loss_date'">
          <template v-if="record.key === 'new-row'">
            <a-date-picker
              v-model:value="newRow.loss_date"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-date-picker
              v-model:value="editingRows[record.id].loss_date"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </template>
          <template v-else>{{ record.loss_date }}</template>
        </template>
        <template v-else-if="column.key === 'loss_reason'">
          <template v-if="record.key === 'new-row'">
            <a-textarea
              v-model:value="newRow.loss_reason"
              :rows="1"
              :maxLength="200"
              placeholder="请输入报损原因（如：损坏/过期/丢失）"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-textarea
              v-model:value="editingRows[record.id].loss_reason"
              :rows="1"
              :maxLength="200"
              placeholder="请输入报损原因（如：损坏/过期/丢失）"
            />
          </template>
          <template v-else>{{ record.loss_reason || '-' }}</template>
        </template>
        <template v-else-if="column.key === 'action'">
          <template v-if="record.key === 'new-row'">
            <a-button type="primary" size="small" @click="handleAdd" style="background-color: #52c41a; border-color: #52c41a">添</a-button>
          </template>
          <template v-else-if="record.isEditing">
            <a-button type="primary" size="small" @click="handleSave" style="margin-right: 8px">保</a-button>
            <a-button size="small" @click="handleCancelEdit(record.id)">取</a-button>
          </template>
          <template v-else>
            <a-button size="small" danger @click="handleDelete(record.id)">删</a-button>
          </template>
        </template>
      </template>
    </a-table>
    
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
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

const showSearch = ref(true);
const dateRange = ref<any>([]);
const dataSource = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const lossReason = ref('');
const editingRows = ref<Record<number, any>>({});
const newRowCurrentInventory = ref<InventoryItem | null>(null);
const newRowInventoryError = ref('');
const editingRowCurrentInventory = ref<Record<number, InventoryItem | null>>({});
const editingRowInventoryError = ref<Record<number, string>>({});

const route = useRoute();

const productOptions = ref<{ label: string; value: string }[]>([]);

const searchParams = reactive<InventoryLossListQuery>({
  page_num: 1,
  page_size: 10
});

const newRow = reactive<any>({
  key: 'new-row',
  product_name: '',
  product_spec: '',
  loss_num: 1,
  loss_date: dayjs(),
  loss_reason: ''
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
    width: 150
  },
  { 
    title: '报损总成本', 
    dataIndex: 'losstotal_cost', 
    key: 'losstotal_cost', 
    sorter: true, 
    ellipsis: true, 
    width: 150
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
    width: 150
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right' as const,
    width: 160
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

const getInventoryByProductName = async (productName: string): Promise<InventoryItem | null> => {
  try {
    const response = await getInventoryList({ product_name: productName, page_size: 1 });
    if (Array.isArray(response.data.list) && response.data.list.length > 0) {
      return response.data.list[0];
    }
    return null;
  } catch (error) {
    console.error('获取商品库存失败:', error);
    return null;
  }
};

const handleNewRowProductChange = async (value: SelectValue) => {
  if (!value) {
    newRowCurrentInventory.value = null;
    newRowInventoryError.value = '';
    return;
  }
  
  const inventory = await getInventoryByProductName(value as string);
  if (inventory) {
    newRowCurrentInventory.value = inventory;
    newRowInventoryError.value = '';
    newRow.product_spec = inventory.product_spec;
    
    if (newRow.loss_num > inventory.inventory_num) {
      newRowInventoryError.value = `库存不足，当前${value}库存为${inventory.inventory_num}`;
    }
  } else {
    newRowCurrentInventory.value = null;
    newRowInventoryError.value = '商品不存在';
  }
};

const handleEditingRowProductChange = async (id: number, value: SelectValue) => {
  if (!value) {
    editingRowCurrentInventory.value[id] = null;
    editingRowInventoryError.value[id] = '';
    return;
  }
  
  const inventory = await getInventoryByProductName(value as string);
  if (inventory) {
    editingRowCurrentInventory.value[id] = inventory;
    editingRowInventoryError.value[id] = '';
    if (editingRows.value[id]) {
      editingRows.value[id].product_spec = inventory.product_spec;
      
      if (editingRows.value[id].loss_num > inventory.inventory_num) {
        editingRowInventoryError.value[id] = `库存不足，当前${value}库存为${inventory.inventory_num}`;
      }
    }
  } else {
    editingRowCurrentInventory.value[id] = null;
    editingRowInventoryError.value[id] = '商品不存在';
  }
};

const handleAdd = async () => {
  if (!newRow.product_name || !newRow.product_spec || !newRow.loss_num || !newRow.loss_date) {
    message.error('请填写必填项');
    return;
  }

  if (newRowCurrentInventory.value && newRow.loss_num > newRowCurrentInventory.value.inventory_num) {
    message.error(`库存不足，当前${newRow.product_name}库存为${newRowCurrentInventory.value.inventory_num}`);
    return;
  }

  try {
    const submitData = {
      ...newRow,
      loss_date: typeof newRow.loss_date === 'object' && newRow.loss_date !== null && typeof (newRow.loss_date as any).format === 'function' ? (newRow.loss_date as any).format('YYYY-MM-DD') : undefined
    };
    
    delete submitData.key;
    
    await addInventoryLoss(submitData as AddInventoryLossReq);
    message.success('报损成功，已自动扣减库存');
    
    Object.assign(newRow, {
      product_name: '',
      product_spec: '',
      loss_num: 1,
      loss_date: dayjs(),
      loss_reason: ''
    });
    newRowCurrentInventory.value = null;
    newRowInventoryError.value = '';
    
    fetchData();
  } catch (error: any) {
    console.error('添加失败:', error);
    Modal.error({
      title: '添加失败',
      content: error.message || '服务器错误，请稍后重试'
    });
  }
};

const handleCancelEdit = (id: number) => {
  delete editingRows.value[id];
  delete editingRowCurrentInventory.value[id];
  delete editingRowInventoryError.value[id];
};

const handleSave = async () => {
  message.warning('库存报损不支持编辑');
};

const handleDelete = (id: number) => {
  Modal.confirm({
    title: '确认删除',
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
</style>
