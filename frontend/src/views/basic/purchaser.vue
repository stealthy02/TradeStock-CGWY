<template>
  <div class="page-container">
    <!-- 原生Antd面包屑+页面头部 -->
    <a-page-header
      title="采购商信息管理"
      :breadcrumb="{
        routes: [{ path: '', name: '基础信息管理' }, { path: '', name: '采购商信息' }]
      }"
      style="margin-bottom: 20px"
    >
      <template #extra>
        <a-space size="middle">
          <a-input-search
            v-model:value="simpleSearchKey"
            placeholder="请输入采购商名模糊搜索"
            allow-clear
            style="width: 300px"
            @search="handleSearch"
          />
          <a-button type="default" icon="search" @click="openAdvancedSearch">
            高级搜索
          </a-button>
          <a-button type="primary" icon="plus" @click="openAddDrawer">
            新增采购商
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

    <div class="purchaser-container">
      <a-skeleton v-if="loading" :active="true" style="width: 100%" />

      <a-row :gutter="[24, 24]" v-else>
        <a-col :span="24" v-if="purchaserList.length === 0">
          <Empty
            description="暂无采购商信息，点击右上角「新增采购商」添加"
            style="margin: 40px 0"
          >
            <a-button type="primary" icon="plus" @click="openAddDrawer">
              新增采购商
            </a-button>
          </Empty>
        </a-col>

        <a-col :span="8" v-for="item in purchaserList" :key="item.id">
          <Card
            class="purchaser-card"
            hoverable
            :bordered="false"
            @click="() => openEditDrawer(item)"
          >
            <div class="card-header">
              <a-checkbox
                :value="item.id"
                :checked="selectedKeys.includes(item.id)" @change="(e) => e.target.checked ? selectedKeys.push(item.id) : selectedKeys.splice(selectedKeys.indexOf(item.id), 1)"
                @change.stop
                style="margin-right: 12px"
              />
              <a-avatar
                :src="item.avatar_url || defaultAvatar"
                :size="64"
                class="purchaser-avatar"
              />
            </div>

            <div class="card-body">
              <div class="info-item">
                <span class="label">采购商名：</span>
                <span class="value">{{ item.purchaser_name }}</span>
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
              <div class="info-item ellipsis" :title="item.receive_address || '未填写'">
                <span class="label">收货地址：</span>
                <span class="value">{{ item.receive_address || '未填写' }}</span>
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
        show-size-changer
        :show-total="(total) => `共 ${total} 条记录`"
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
        <a-form-item label="采购商名" name="purchaser_name">
          <a-input
            v-model:value="advancedQuery.purchaser_name"
            placeholder="请输入采购商名"
            allow-clear
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
      :title="isEdit ? '编辑采购商' : '新增采购商'"
      :open="formDrawerVisible"
      width="600px"
      destroy-on-close
      @close="closeFormDrawer"
    >
      <a-form
        ref="purchaserFormRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
        @finish="handleFormSubmit"
      >
        <a-form-item label="采购商头像" name="avatar">
          <a-upload
            :action="uploadApi"
            list-type="picture-card"
            :file-list="avatarFileList"
            :before-upload="beforeAvatarUpload"
            @change="handleAvatarChange"
            :show-upload-list="false"
          >
            <img v-if="formData.avatar" :src="formData.avatar" width="100" height="100" />
            <div v-else>
              <a-icon :type="loading ? 'loading' : 'plus'" />
              <div style="margin-top: 8px">上传</div>
            </div>
          </a-upload>
        </a-form-item>

        <a-form-item label="采购商名" name="purchaser_name">
          <a-input
            v-model:value="formData.purchaser_name"
            placeholder="请输入采购商名"
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
        <a-form-item label="收货地址" name="receive_address">
          <a-input
            v-model:value="formData.receive_address"
            placeholder="请输入收货地址"
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
        <a-form-item label="税号" name="tax_no">
          <a-input
            v-model:value="formData.tax_no"
            placeholder="请输入税号"
            allow-clear
            :maxlength="20"
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
// 完全对齐你的Vue钩子导入
import { ref, reactive, onMounted } from 'vue';
// 导入所有模板中用到的原生Antd组件+方法，无多余
import { Card, Empty, message, UploadProps, FormInstance } from 'ant-design-vue';
import type { RuleObject } from 'ant-design-vue/es/form/interface';
// 仅导入项目实际用到的TS类型，无多余
import type {
  AddPurchaserReq,
  UpdatePurchaserReq,
  PurchaserListQuery,
  PurchaserItem,
  BaseSuccessResponse,
  AddIdSuccessResponse
} from '@/types';
// 对齐你的API目录：@/api/basic
import {
  addPurchaser,
  getPurchaserList,
  updatePurchaser,
  deletePurchaser
} from '@/api/basic';

// ===================== 全局常量 =====================
const defaultAvatar = 'https://gw.alipayobjects.com/zos/rmsportal/BiazfanxmamNRoxxVxka.png';
const uploadApi = '/api/upload/avatar'; // 按你后端实际地址修改

// ===================== 声明上传响应类型：解决info.file.response类型未知 =====================
interface UploadResponse {
  code: number;
  message: string;
  data: { url: string };
}

// ===================== 响应式数据 =====================
// 页面状态
const loading = ref<boolean>(false);
const formLoading = ref<boolean>(false);
const selectedKeys = ref<number[]>([]);
const simpleSearchKey = ref<string>('');

// 分页参数
const pageNum = ref<number>(1);
const pageSize = ref<number>(9);
const total = ref<number>(0);

// 列表数据
const purchaserList = ref<PurchaserItem[]>([]);

// 高级搜索
const advancedSearchVisible = ref<boolean>(false);
const advancedQuery = reactive<PurchaserListQuery>({
  page_num: 1,
  page_size: 10,
  purchaser_name: '',
  contact_phone: '',
});

// 表单抽屉：修复FormRef类型 - 改为Form+null，移除Nullable
const formDrawerVisible = ref<boolean>(false);
const isEdit = ref<boolean>(false);
const purchaserFormRef = ref<FormInstance | null>(null);
// 表单数据：完美匹配Add/UpdatePurchaserReq
const formData = reactive<AddPurchaserReq & UpdatePurchaserReq>({
  id: 0,
  purchaser_name: '',
  contact_person: '',
  contact_phone: '',
  company_address: '',
  receive_address: '',
  bank_name: '',
  bank_account: '',
  tax_no: '',
  remark: '',
  avatar: '',
});
// Upload文件列表：用Antd原生类型
const avatarFileList = ref<UploadProps['fileList']>([]);

// 删除弹窗
const deleteModalVisible = ref<boolean>(false);
const deleteModalText = ref<string>('');
const deleteTargetId = ref<number | number[]>(0);

// ===================== 表单校验规则 =====================
const formRules = reactive<Record<string, RuleObject[]>>({
  purchaser_name: [
    { type: 'string', required: true, message: '请输入采购商名', trigger: 'blur' },
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
  getPurchaserData();
});

// ===================== 核心方法 =====================
// 获取采购商列表：对齐你的api调用风格，直接取res.data
const getPurchaserData = async () => {
  loading.value = true;
  try {
    const queryParams: PurchaserListQuery = {
      page_num: pageNum.value,
      page_size: pageSize.value,
      purchaser_name: simpleSearchKey.value || advancedQuery.purchaser_name,
      contact_phone: advancedQuery.contact_phone,
    };
    // 接口返回值直接是后端响应体，含code/message/data
    const res = await getPurchaserList(queryParams);
    if (res.code === 200) {
      purchaserList.value = res.data.list;
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

// 分页/搜索方法
const handlePageChange = (page: number) => {
  pageNum.value = page;
  getPurchaserData();
};
const handleSizeChange = (_: number, size: number) => {
  pageSize.value = size;
  pageNum.value = 1;
  getPurchaserData();
};
const handleSearch = () => {
  pageNum.value = 1;
  getPurchaserData();
};

// 高级搜索方法
const openAdvancedSearch = () => advancedSearchVisible.value = true;
const closeAdvancedSearch = () => advancedSearchVisible.value = false;
const resetAdvancedQuery = () => {
  advancedQuery.purchaser_name = '';
  advancedQuery.contact_phone = '';
};
const handleAdvancedSearch = () => {
  closeAdvancedSearch();
  pageNum.value = 1;
  simpleSearchKey.value = '';
  getPurchaserData();
};

// 表单抽屉方法
const openAddDrawer = () => {
  isEdit.value = false;
  formDrawerVisible.value = true;
  resetForm();
};
const openEditDrawer = (item: PurchaserItem) => {
  isEdit.value = true;
  formDrawerVisible.value = true;
  resetForm();
  Object.assign(formData, item);
  // 头像回显：用采购商ID做唯一uid，无额外依赖
  if (item.avatar_url) {
    avatarFileList.value = [{
      uid: `${item.id}_avatar`,
      name: 'avatar.png',
      url: item.avatar_url || defaultAvatar,
    }];
  }
};
const closeFormDrawer = () => {
  formDrawerVisible.value = false;
  avatarFileList.value = [];
};
const resetForm = () => {
  purchaserFormRef.value?.resetFields();
  Object.assign(formData, {
    id: 0,
    purchaser_name: '',
    contact_person: '',
    contact_phone: '',
    address: '',
    receive_address: '',
    bank_name: '',
    bank_account: '',
    tax_no: '',
    remark: '',
    avatar: '',
  });
};

// 头像上传方法：加类型断言，解决info.file.response类型未知
const beforeAvatarUpload: UploadProps['beforeUpload'] = (file) => {
  const isImage = file.type.startsWith('image/');
  const isLt2M = file.size / 1024 / 1024 < 2;
  if (!isImage) message.error('请上传图片格式文件');
  if (!isLt2M) message.error('图片大小不超过2MB');
  return isImage && isLt2M;
};
const handleAvatarChange: UploadProps['onChange'] = (info) => {
  if (info.file.status === 'done') {
    // 核心：给response加类型断言为UploadResponse
    const res = info.file.response as UploadResponse;
    if (res.code === 200) {
      formData.avatar = res.data.url;
      avatarFileList.value = [{
        uid: info.file.uid,
        name: info.file.name || 'avatar.png',
        url: res.data.url
      }];
      message.success('头像上传成功');
    } else {
      message.error(res.message || '头像上传失败');
    }
  } else if (info.file.status === 'error') {
    message.error('头像上传失败');
  }
};

// 表单提交：新增/编辑，res直接有code/message
const handleFormSubmit = async () => {
  formLoading.value = true;
  try {
    let res: BaseSuccessResponse | AddIdSuccessResponse;
    if (isEdit.value) {
      // 编辑：调用更新接口，返回BaseSuccessResponse
      res = await updatePurchaser(formData);
    } else {
      // 新增：删除id，调用新增接口，返回AddIdSuccessResponse
      const { id, ...addData } = formData;
      res = await addPurchaser(addData);
    }
    // 直接判断res.code，无AxiosResponse包裹
    if (res.code === 200) {
      message.success(isEdit.value ? '修改成功' : '新增成功');
      closeFormDrawer();
      getPurchaserData(); // 刷新列表
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

// 删除方法：单条/批量
const handleSingleDelete = (id: number) => {
  deleteTargetId.value = id;
  deleteModalText.value = '确定删除该采购商吗？删除后不可恢复！';
  deleteModalVisible.value = true;
};
const handleBatchDelete = () => {
  deleteTargetId.value = selectedKeys.value;
  deleteModalText.value = `确定删除选中的${selectedKeys.value.length}个采购商吗？`;
  deleteModalVisible.value = true;
};
const closeDeleteModal = () => deleteModalVisible.value = false;
const confirmDelete = async () => {
  loading.value = true;
  try {
    const targetIds = Array.isArray(deleteTargetId.value) ? deleteTargetId.value : [deleteTargetId.value];
    // 批量删除：循环调用删除接口
    await Promise.all(targetIds.map(id => deletePurchaser({ id })));
    message.success('删除成功');
    closeDeleteModal();
    selectedKeys.value = [];
    getPurchaserData();
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

.purchaser-container {
  width: 100%;
}

.purchaser-card {
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

.purchaser-avatar {
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