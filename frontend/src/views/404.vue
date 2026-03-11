<template>
  <div class="not-found-page">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <h1 class="error-title">页面不存在</h1>
      <p class="error-description">抱歉，您访问的页面不存在或已被移除</p>
      <div class="action-buttons">
        <router-link to="/" class="btn btn-primary">返回首页</router-link>
        <button @click="goBack" class="btn btn-secondary">返回上一页</button>
      </div>
      <div class="quick-links">
        <h3>快速导航</h3>
        <ul>
          <li><router-link to="/">首页</router-link></li>
          <li><router-link to="/goods/list">商品管理</router-link></li>
          <li><router-link to="/inventory/list">库存管理</router-link></li>
          <li><router-link to="/purchase/bill">采购管理</router-link></li>
          <li><router-link to="/sale/bill">销售管理</router-link></li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup name="NotFoundPage">
import { useRouter } from 'vue-router';

const router = useRouter();

const goBack = () => {
  window.history.back();
};
</script>

<style scoped lang="scss">
.not-found-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  font-family: 'Arial', sans-serif;
}

.not-found-content {
  text-align: center;
  background: white;
  padding: 60px 40px;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  max-width: 500px;
  width: 90%;
  animation: fadeIn 0.5s ease-in-out;

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  color: #3498db;
  margin: 0 0 20px 0;
  line-height: 1;
  text-shadow: 3px 3px 0 rgba(0, 0, 0, 0.1);
}

.error-title {
  font-size: 32px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 16px 0;
}

.error-description {
  font-size: 16px;
  color: #7f8c8d;
  margin: 0 0 32px 0;
  line-height: 1.5;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin: 0 0 40px 0;

  .btn {
    padding: 12px 24px;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    text-decoration: none;
    display: inline-block;

    &.btn-primary {
      background-color: #3498db;
      color: white;

      &:hover {
        background-color: #2980b9;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
      }
    }

    &.btn-secondary {
      background-color: #ecf0f1;
      color: #2c3e50;

      &:hover {
        background-color: #d5dbdb;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(236, 240, 241, 0.5);
      }
    }
  }
}

.quick-links {
  border-top: 1px solid #ecf0f1;
  padding-top: 30px;

  h3 {
    font-size: 18px;
    font-weight: 600;
    color: #2c3e50;
    margin: 0 0 16px 0;
  }

  ul {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;

    li {
      a {
        color: #3498db;
        text-decoration: none;
        font-size: 14px;
        transition: color 0.3s ease;

        &:hover {
          color: #2980b9;
          text-decoration: underline;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .not-found-content {
    padding: 40px 30px;
  }

  .error-code {
    font-size: 90px;
  }

  .error-title {
    font-size: 24px;
  }

  .error-description {
    font-size: 14px;
  }

  .action-buttons {
    flex-direction: column;
    align-items: center;

    .btn {
      width: 100%;
      max-width: 200px;
    }
  }

  .quick-links ul {
    flex-direction: column;
    gap: 8px;
  }
}
</style>