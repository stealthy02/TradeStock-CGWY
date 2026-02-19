<template>
  <div class="page-container">
    <h1>运营杂费录入/查询</h1>
    
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
      :data-source="tableDataSource"
      :row-key="(record) => record.key || record.id"
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
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'fee_desc'">
          <template v-if="record.key === 'new-row'">
            <a-input
              v-model:value="newRow.fee_desc"
              placeholder="请输入费用描述（≤50字）"
              :maxLength="50"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-input
              v-model:value="editingRows[record.id].fee_desc"
              placeholder="请输入费用描述（≤50字）"
              :maxLength="50"
            />
          </template>
          <template v-else>{{ record.fee_desc }}</template>
        </template>
        <template v-else-if="column.key === 'fee_amount'">
          <template v-if="record.key === 'new-row'">
            <a-input-number
              v-model:value="newRow.fee_amount"
              :min="0.01"
              :step="0.01"
              :precision="2"
              placeholder="请输入费用金额"
              style="width: 100%"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-input-number
              v-model:value="editingRows[record.id].fee_amount"
              :min="0.01"
              :step="0.01"
              :precision="2"
              placeholder="请输入费用金额"
              style="width: 100%"
            />
          </template>
          <template v-else>{{ record.fee_amount?.toFixed(2) }}</template>
        </template>
        <template v-else-if="column.key === 'fee_date'">
          <template v-if="record.key === 'new-row'">
            <a-date-picker
              v-model:value="newRow.fee_date"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </template>
          <template v-else-if="record.isEditing">
            <a-date-picker
              v-model:value="editingRows[record.id].fee_date"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </template>
          <template v-else>{{ record.fee_date }}</template>
        </template>
        <template v-else-if="column.key === 'fee_type_text'">
          <template v-if="record.key === 'new-row'">
            <a-select
              v-model:value="newRow.fee_type"
              placeholder="请选择费用类型"
              style="width: 100%"
            >
              <a-select-option value="房租">房租</a-select-option>
              <a-select-option value="水电">水电</a-select-option>
              <a-select-option value="人工">人工</a-select-option>
              <a-select-option value="物流">物流</a-select-option>
              <a-select-option value="其他">其他</a-select-option>
            </a-select>
          </template>
          <template v-else-if="record.isEditing">
            <a-select
              v-model:value="editingRows[record.id].fee_type"
              placeholder="请选择费用类型"
              style="width: 100%"
            >
              <a-select-option value="房租">房租</a-select-option>
              <a-select-option value="水电">水电</a-select-option>
              <a-select-option value="人工">人工</a-select-option>
              <a-select-option value="物流">物流</a-select-option>
              <a-select-option value="其他">其他</a-select-option>
            </a-select>
          </template>
          <template v-else>{{ record.fee_type_text }}</template>
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
        <template v-else-if="column.key === 'create_time'">
          <template v-if="record.key === 'new-row'">-</template>
          <template v-else-if="record.isEditing">-</template>
          <template v-else>{{ record.create_time }}</template>
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
import { message, Modal } from 'ant-design-vue';
import dayjs from 'dayjs';
import type { CostFeeItem, AddCostFeeReq, UpdateCostFeeReq, CostFeeListQuery } from '@/types';
import {
  addCostFee,
  getCostFeeList,
  updateCostFee,
  deleteCostFee
} from '@/api/cost';

const showSearch = ref(true);
const dateRange = ref<any>([]);
const dataSource = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const editingRows = ref<Record<number, any>>({});

const searchParams = reactive<CostFeeListQuery>({
  page_num: 1,
  page_size: 10
});

const newRow = reactive<any>({
  key: 'new-row',
  fee_desc: '',
  fee_amount: undefined,
  fee_date: dayjs(),
  fee_type: '其他',
  remark: ''
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
    width: 150
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
    width: 100
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
    width: 160
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

const handleAdd = async () => {
  if (!newRow.fee_desc || !newRow.fee_amount || !newRow.fee_date || !newRow.fee_type) {
    message.error('请填写必填项');
    return;
  }

  try {
    const submitData = {
      ...newRow,
      fee_date: typeof newRow.fee_date === 'object' && newRow.fee_date !== null && typeof (newRow.fee_date as any).format === 'function' ? (newRow.fee_date as any).format('YYYY-MM-DD') : undefined
    };
    
    delete submitData.key;
    
    await addCostFee(submitData as AddCostFeeReq);
    message.success('添加成功');
    
    Object.assign(newRow, {
      fee_desc: '',
      fee_amount: undefined,
      fee_date: dayjs(),
      fee_type: '其他',
      remark: ''
    });
    
    fetchData();
  } catch (error: any) {
    console.error('添加失败:', error);
    Modal.error({
      title: '添加失败',
      content: error.message || '服务器错误，请稍后重试'
    });
  }
};

const handleEdit = (record: any) => {
  editingRows.value[record.id] = {
    ...record,
    fee_date: dayjs(record.fee_date)
  };
};

const handleCancelEdit = (id: number) => {
  delete editingRows.value[id];
};

const handleSave = async (id: number) => {
  const row = editingRows.value[id];
  if (!row.fee_desc || !row.fee_amount || !row.fee_date || !row.fee_type) {
    message.error('请填写必填项');
    return;
  }

  try {
    const submitData = {
      id,
      fee_desc: row.fee_desc,
      fee_amount: row.fee_amount as number,
      fee_date: typeof row.fee_date === 'object' && row.fee_date !== null && typeof (row.fee_date as any).format === 'function' ? (row.fee_date as any).format('YYYY-MM-DD') : undefined,
      fee_type: row.fee_type,
      remark: row.remark
    };
    
    await updateCostFee(submitData as UpdateCostFeeReq);
    message.success('保存成功');
    delete editingRows.value[id];
    fetchData();
  } catch (error: any) {
    console.error('保存失败:', error);
    Modal.error({
      title: '保存失败',
      content: error.message || '服务器错误，请稍后重试'
    });
  }
};

const handleDelete = (id: number) => {
  Modal.confirm({
    title: '确认删除',
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
</style>
