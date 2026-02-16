<template>
  <div class="page-container">
    <!-- 供货商页面头部+面包屑 -->
    <a-page-header
      title="供货商信息管理"
      :breadcrumb="{
        routes: [{ path: '', name: '基础信息管理' }, { path: '', name: '供货商信息' }]
      }"
      style="margin-bottom: 20px"
    >
      <template #extra>
        <a-space size="middle">
          <a-input-search
            v-model:value="simpleSearchKey"
            placeholder="请输入供货商名模糊搜索"
            allow-clear
            style="width: 300px"
            @search="handleSearch"
          />
          <a-button type="default" icon="search" @click="openAdvancedSearch">
            高级搜索
          </a-button>
          <a-button type="primary" icon="plus" @click="openAddDrawer">
            新增供货商
          </a-button>
          <a-button
            type="default"
            danger
            icon="delete"
            :disabled="selectedKeys.length === 0"
            @click="handleBatchDelete"
          >
            批量删除
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <div class="supplier-container">
      <a-skeleton v-if="loading" :active="true" style="width: 100%" />

      <a-row :gutter="[24, 24]" v-else>
        <a-col :span="24" v-if="supplierList.length === 0">
          <Empty
            description="暂无供货商信息，点击右上角「新增供货商」添加"
            style="margin: 40px 0"
          >
            <a-button type="primary" icon="plus" @click="openAddDrawer">
              新增供货商
            </a-button>
          </Empty>
        </a-col>

        <a-col :span="8" v-for="item in supplierList" :key="item.id">
          <Card
            class="supplier-card"
            hoverable
            :bordered="false"
            @click="() => openEditDrawer(item)"
          >
            <div class="card-header">
              <a-checkbox
                :checked="selectedKeys.includes(item.id)"
                @change="(e) => e.target.checked ? selectedKeys.push(item.id) : selectedKeys.splice(selectedKeys.indexOf(item.id), 1)"
                style="margin-right: 12px"
              />
              <a-avatar
                :src="item.avatar_url || defaultAvatar"
                :size="64"
                class="supplier-avatar"
              />
            </div>

            <div class="card-body">
              <div class="info-item">
                <span class="label">供货商名：</span>
                <span class="value">{{ item.supplier_name }}</span>
              </div>
              <div class="info-item">
                <span class="label">联系人：</span>
                <span class="value">{{ item.contact_person }}</span>
              </div>
              <div class="info-item">
                <span class="label">联系电话：</span>
                <span class="value">{{ item.contact_phone }}</span>
              </div>
              <div class="info-item ellipsis" :title="item.company_address || '未填写'">
                <span class="label">公司地址：</span>
                <span class="value">{{ item.company_address || '未填写' }}</span>
              </div>
              <div class="info-item ellipsis" :title="item.bank_name || '未填写'">
                <span class="label">开户行：</span>
                <span class="value">{{ item.bank_name || '未填写' }}</span>
              </div>
              <div class="info-item">
                <span class="label">创建时间：</span>
                <span class="value">{{ item.create_time }}</span>
              </div>
              <a-tag color="blue" v-if="item.remark" :title="item.remark">
                有备注
              </a-tag>
            </div>

            <div class="card-actions">
              <a-button type="text" @click.stop="openEditDrawer(item)">
                编辑
              </a-button>
              <a-button type="text" danger @click.stop="handleSingleDelete(item.id)">
                删除
              </a-button>
            </div>
          </Card>
        </a-col>
      </a-row>

      <a-pagination
        v-if="total > 0"
        :current="pageNum"
        :page-size="pageSize"
        :total="total"
        :show-total="(total) => `共 ${total} 条记录`"
        show-size-changer
        style="margin-top: 24px; text-align: right"
        @change="handlePageChange"
        @show-size-change="handleSizeChange"
      />
    </div>

    <!-- 高级搜索抽屉 -->
    <a-drawer
      title="高级搜索"
      :open="advancedSearchVisible"
      width="400px"
      @close="closeAdvancedSearch"
    >
      <a-form
        :model="advancedQuery"
        layout="vertical"
        @finish="handleAdvancedSearch"
      >
        <a-form-item label="税号" name="tax_no">
  <a-input
    v-model:value="formData.tax_no"
    placeholder="请输入税号"
    allow-clear
    :maxlength="50"
    show-word-limit
  />
</a-form-item>
        <a-form-item label="联系电话" name="contact_phone">
          <a-input
            v-model:value="advancedQuery.contact_phone"
            placeholder="请输入联系电话"
            allow-clear
          />
        </a-form-item>
        <div style="text-align: right; margin-top: 16px">
          <a-button type="default" @click="resetAdvancedQuery" style="margin-right: 8px">
            重置
          </a-button>
          <a-button type="primary" html-type="submit">
            查询
          </a-button>
        </div>
      </a-form>
    </a-drawer>

    <!-- 新增/编辑抽屉 -->
    <a-drawer
      :title="isEdit ? '编辑供货商' : '新增供货商'"
      :open="formDrawerVisible"
      width="600px"
      destroy-on-close
      @close="closeFormDrawer"
    >
      <a-form
        ref="supplierFormRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
        @finish="handleFormSubmit"
      >
        <a-form-item label="供货商头像" name="avatar_url">
          <a-upload
            :action="uploadApi"
            list-type="picture-card"
            :file-list="avatarFileList"
            :before-upload="beforeAvatarUpload"
            @change="handleAvatarChange"
            :show-upload-list="false"
          >
            <img v-if="formData.avatar_url" :src="formData.avatar_url" width="100" height="100" />
            <div v-else>
              <a-icon :type="loading ? 'loading' : 'plus'" />
              <div style="margin-top: 8px">上传</div>
            </div>
          </a-upload>
        </a-form-item>

        <a-form-item label="供货商名" name="supplier_name">
          <a-input
            v-model:value="formData.supplier_name"
            placeholder="请输入供货商名"
            allow-clear
            :maxlength="50"
            show-word-limit
          />
        </a-form-item>
        <a-form-item label="联系人" name="contact_person">
          <a-input
            v-model:value="formData.contact_person"
            placeholder="请输入联系人"
            allow-clear
            :maxlength="20"
            show-word-limit
          />
        </a-form-item>
        <a-form-item label="联系电话" name="contact_phone">
          <a-input
            v-model:value="formData.contact_phone"
            placeholder="请输入手机号/固话"
            allow-clear
            :maxlength="20"
          />
        </a-form-item>

        <a-form-item label="公司地址" name="address">
          <a-input
            v-model:value="formData.company_address"
            placeholder="请输入公司地址"
            allow-clear
            :maxlength="200"
            show-word-limit
          />
        </a-form-item>
        <a-form-item label="开户行" name="bank_name">
          <a-input
            v-model:value="formData.bank_name"
            placeholder="请输入开户行"
            allow-clear
            :maxlength="50"
            show-word-limit
          />
        </a-form-item>
        <a-form-item label="银行账号" name="bank_account">
          <a-input
            v-model:value="formData.bank_account"
            placeholder="请输入银行账号"
            allow-clear
            :maxlength="30"
            show-word-limit
          />
        </a-form-item>
        <a-form-item label="备注" name="remark">
          <a-textarea
            v-model:value="formData.remark"
            placeholder="请输入备注"
            allow-clear
            :rows="3"
            :maxlength="200"
            show-word-limit
          />
        </a-form-item>

        <div style="text-align: right; margin-top: 16px">
          <a-button type="default" @click="closeFormDrawer" style="margin-right: 8px">
            取消
          </a-button>
          <a-button type="primary" html-type="submit" :loading="formLoading">
            {{ isEdit ? '保存修改' : '新增' }}
          </a-button>
        </div>
      </a-form>
    </a-drawer>

    <!-- 删除确认弹窗 -->
    <a-modal
      title="确认删除"
      :open="deleteModalVisible"
      @ok="confirmDelete"
      @cancel="closeDeleteModal"
      ok-text="确认删除"
      cancel-text="取消"
      ok-type="danger"
    >
      <p>{{ deleteModalText }}</p>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
// 完全对齐采购商页面的导入风格
import { ref, reactive, onMounted } from 'vue';
import { Card, Empty, message, UploadProps, FormInstance } from 'ant-design-vue';
import type { RuleObject } from 'ant-design-vue/es/form/interface';
// 供货商相关TS类型（和采购商类型结构一致，仅命名替换）
import type {
  AddSupplierReq,
  UpdateSupplierReq,
  SupplierListQuery,
  SupplierItem,
  BaseSuccessResponse,
  AddIdSuccessResponse
} from '@/types';
// 供货商相关API（后续在@/api/basic中新增）
import {
  addSupplier,
  getSupplierList,
  updateSupplier,
  deleteSupplier
} from '@/api/basic';

// 全局常量（和采购商一致）
const defaultAvatar = 'https://gw.alipayobjects.com/zos/rmsportal/BiazfanxmamNRoxxVxka.png';
const uploadApi = '/api/upload/avatar'; // 复用头像上传接口

// 上传响应类型声明（和采购商一致）
interface UploadResponse {
  code: number;
  message: string;
  data: { url: string };
}

// ===================== 响应式数据（采购商→供货商，命名统一替换） =====================
const loading = ref<boolean>(false);
const formLoading = ref<boolean>(false);
const selectedKeys = ref<number[]>([]);
const simpleSearchKey = ref<string>('');

const pageNum = ref<number>(1);
const pageSize = ref<number>(10);
const total = ref<number>(0);

const supplierList = ref<SupplierItem[]>([]);
const advancedSearchVisible = ref<boolean>(false);
const advancedQuery = reactive<SupplierListQuery>({
  page_num: 1,
  page_size: 10,
  supplier_name: '',
  contact_phone: '',
});

const formDrawerVisible = ref<boolean>(false);
const isEdit = ref<boolean>(false);
const supplierFormRef = ref<FormInstance | null>(null);
const formData = reactive<AddSupplierReq & UpdateSupplierReq>({
  id: 0,
  supplier_name: '',
  contact_person: '',
  contact_phone: '',
  company_address: '', // 改：address → company_address
  bank_name: '',
  bank_account: '',
  tax_no: '', // 加：新增税号字段
  remark: '',
  avatar_url: '', // 改：avatar → avatar_url
});
const avatarFileList = ref<UploadProps['fileList']>([]);

const deleteModalVisible = ref<boolean>(false);
const deleteModalText = ref<string>('');
const deleteTargetId = ref<number | number[]>(0);

// ===================== 表单校验规则（仅替换采购商→供货商，规则逻辑一致） =====================
const formRules = reactive<Record<string, RuleObject[]>>({
  supplier_name: [
    { type: 'string', required: true, message: '请输入供货商名', trigger: 'blur' },
    { type: 'string', min: 2, max: 50, message: '名称长度2-50字符', trigger: 'blur' },
  ],
  contact_person: [
    { type: 'string', required: false, message: '请输入联系人', trigger: 'blur' },
    { type: 'string', min: 1, max: 20, message: '联系人长度1-20字符', trigger: 'blur' },
  ],
  contact_phone: [
    { type: 'string', required: false, message: '请输入联系电话', trigger: 'blur' },
    { type: 'string', pattern: /^(1[3-9]\d{9})$|^(\d{3,4}-)?\d{7,8}$/, message: '请输入合法手机号/固话', trigger: 'blur' },
  ],
});

// ===================== 页面初始化 =====================
onMounted(() => {
  getSupplierData();
});

// ===================== 核心方法（仅替换采购商→供货商，逻辑完全一致） =====================
const getSupplierData = async () => {
  loading.value = true;
  try {
    const queryParams: SupplierListQuery = {
      page_num: pageNum.value,
      page_size: pageSize.value,
      supplier_name: simpleSearchKey.value || advancedQuery.supplier_name,
      contact_phone: advancedQuery.contact_phone,
    };
    const res = await getSupplierList(queryParams);
    console.log('原始接口数据：', res.data);
    if (res.code === 200) {
      supplierList.value = res.data.list;
      total.value = res.data.total;
    } else {
      message.error(res.message || '获取列表失败');
    }
  } catch (error) {
    console.error('获取列表异常：', error);
    message.error('网络异常，获取列表失败');
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page: number) => {
  pageNum.value = page;
  getSupplierData();
};
const handleSizeChange = (_: number, size: number) => {
  pageSize.value = size;
  pageNum.value = 1;
  getSupplierData();
};
const handleSearch = () => {
  pageNum.value = 1;
  getSupplierData();
};

const openAdvancedSearch = () => advancedSearchVisible.value = true;
const closeAdvancedSearch = () => advancedSearchVisible.value = false;
const resetAdvancedQuery = () => {
  advancedQuery.supplier_name = '';
  advancedQuery.contact_phone = '';
};
const handleAdvancedSearch = () => {
  closeAdvancedSearch();
  pageNum.value = 1;
  simpleSearchKey.value = '';
  getSupplierData();
};

const openAddDrawer = () => {
  isEdit.value = false;
  formDrawerVisible.value = true;
  resetForm();
};
const openEditDrawer = (item: SupplierItem) => {
  isEdit.value = true;
  formDrawerVisible.value = true;
  resetForm();
  Object.assign(formData, item);
  if (item.avatar_url) {
    avatarFileList.value = [{
      uid: `${item.id}_avatar`,
      name: 'avatar.png',
      url: item.avatar_url
    }];
  }
};
const closeFormDrawer = () => {
  formDrawerVisible.value = false;
  avatarFileList.value = [];
};
const resetForm = () => {
  supplierFormRef.value?.resetFields();
  Object.assign(formData, {
    id: 0,
    supplier_name: '',
    contact_person: '',
    contact_phone: '',
    company_address: '', // 改：address → company_address
    bank_name: '',
    bank_account: '',
    tax_no: '', // 加：税号重置
    remark: '',
    avatar_url: '', // 改：avatar → avatar_url
  });
};

const beforeAvatarUpload: UploadProps['beforeUpload'] = (file) => {
  const isImage = file.type.startsWith('image/');
  const isLt2M = file.size / 1024 / 1024 < 2;
  if (!isImage) message.error('请上传图片格式文件');
  if (!isLt2M) message.error('图片大小不超过2MB');
  return isImage && isLt2M;
};
const handleAvatarChange: UploadProps['onChange'] = (info) => {
  if (info.file.status === 'done') {
    const res = info.file.response as UploadResponse;
    if (res.code === 200) {
  formData.avatar_url = res.data.url; // 改：avatar → avatar_url
  avatarFileList.value = [{
    uid: info.file.uid,
    name: info.file.name || 'avatar.png',
    url: res.data.url
  }];
  message.success('头像上传成功');
}
  } else if (info.file.status === 'error') {
    message.error('头像上传失败');
  }
};

const handleFormSubmit = async () => {
  formLoading.value = true;
  try {
    let res: BaseSuccessResponse | AddIdSuccessResponse;
    if (isEdit.value) {
      res = await updateSupplier(formData);
    } else {
      const { id, ...addData } = formData;
      res = await addSupplier(addData);
    }
    if (res.code === 200) {
      message.success(isEdit.value ? '修改成功' : '新增成功');
      closeFormDrawer();
      getSupplierData();
    } else {
      message.error(res.message || (isEdit.value ? '修改失败' : '新增失败'));
    }
  } catch (error) {
    console.error('提交异常：', error);
    message.error(isEdit.value ? '修改失败' : '新增失败');
  } finally {
    formLoading.value = false;
  }
};

const handleSingleDelete = (id: number) => {
  deleteTargetId.value = id;
  deleteModalText.value = '确定删除该供货商吗？删除后不可恢复！';
  deleteModalVisible.value = true;
};
const handleBatchDelete = () => {
  deleteTargetId.value = selectedKeys.value;
  deleteModalText.value = `确定删除选中的${selectedKeys.value.length}个供货商吗？`;
  deleteModalVisible.value = true;
};
const closeDeleteModal = () => deleteModalVisible.value = false;
const confirmDelete = async () => {
  loading.value = true;
  try {
    const targetIds = Array.isArray(deleteTargetId.value) ? deleteTargetId.value : [deleteTargetId.value];
    await Promise.all(targetIds.map(id => deleteSupplier({ id })));
    message.success('删除成功');
    closeDeleteModal();
    selectedKeys.value = [];
    getSupplierData();
  } catch (error) {
    console.error('删除异常：', error);
    message.error('删除失败');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped lang="less">
.page-container {
  padding: 20px;
  min-height: calc(100vh - 120px);
}

.supplier-container {
  width: 100%;
}

.supplier-card {
  height: 100%;
  cursor: pointer;
  transition: all 0.3s ease;
  &:hover {
    box-shadow: 0 8px 24px rgba(149, 157, 165, 0.15) !important;
  }
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.supplier-avatar {
  border: 1px solid #f0f0f0;
}

.card-body {
  .info-item {
    display: flex;
    margin-bottom: 8px;
    line-height: 1.6;
    .label {
      color: #666;
      width: 80px;
      flex-shrink: 0;
    }
    .value {
      color: #333;
      flex: 1;
    }
    &.ellipsis {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>