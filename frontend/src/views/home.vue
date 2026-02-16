<template>
  <div class="home-container">
    <div class="home-header">
      <div class="header-left">
        <h2>数据总览</h2>
      </div>
    </div>
    <div class="stat-card-wrap">
      <div class="stat-empty" v-if="Object.keys(statisticCard).length === 0">
        <a-empty description="暂无数字卡片数据" />
      </div>
      <a-card v-else v-for="(item, key) in statisticCard" :key="key" class="stat-card">
        <a-statistic
          :title="item.title"
          :value="item.value"
          :precision="2"
          suffix="元"
        ></a-statistic>
      </a-card>
    </div>
    <div class="chart-card single-chart">
      <div class="chart-header">
        <h3>营收支出趋势</h3>
        <a-radio-group v-model:value="timeType" @change="handleTimeTypeChange">
          <a-radio-button value="year">本年</a-radio-button>
          <a-radio-button value="custom">自定义</a-radio-button>
        </a-radio-group>
        <a-range-picker 
          v-if="timeType === 'custom'" 
          v-model:value="dateRange" 
          @change="handleDateRangeChange"
          style="margin-left: 12px"
          format="YYYY-MM"
          picker="month"
        />
      </div>
      <a-empty v-if="!trendChartData.length" description="暂无营收支出趋势数据" />
      <v-chart v-else :option="lineChartOption" style="width: 100%; height: 400px" />
    </div>
    <div class="pie-chart-wrap">
      <div class="chart-card pie-chart">
        <div class="chart-header">
          <h3>采购商利润分布</h3>
          <a-radio-group v-model:value="pieTimeType" @change="handlePieTimeTypeChange" size="small">
            <a-radio-button value="all">全部</a-radio-button>
            <a-radio-button value="year">本年</a-radio-button>
            <a-radio-button value="month">本月</a-radio-button>
          </a-radio-group>
        </div>
        <a-empty v-if="!purchaserProfitData.length" description="暂无采购商利润数据" />
        <v-chart v-else :option="purchaserPieOption" style="width: 100%; height: 300px" />
      </div>
      <div class="chart-card pie-chart">
        <div class="chart-header">
          <h3>商品利润分布</h3>
          <a-radio-group v-model:value="pieTimeType" @change="handlePieTimeTypeChange" size="small">
            <a-radio-button value="all">全部</a-radio-button>
            <a-radio-button value="year">本年</a-radio-button>
            <a-radio-button value="month">本月</a-radio-button>
          </a-radio-group>
        </div>
        <a-empty v-if="!productProfitData.length" description="暂无商品利润数据" />
        <v-chart v-else :option="productPieOption" style="width: 100%; height: 300px" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import {
  LineChart,
  PieChart
} from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  ToolboxComponent
} from 'echarts/components';
import { LabelLayout, UniversalTransition } from 'echarts/features';
import { CanvasRenderer } from 'echarts/renderers';
import { ref, computed, onMounted } from 'vue';
import { getStatisticCard, getPieChart, getTrendChart } from '@/api/home';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';

// 注册必须的组件
use([
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  ToolboxComponent,
  LabelLayout,
  UniversalTransition,
  CanvasRenderer
]);

// ========== 响应式数据 - 时间选择 ==========
const timeType = ref<'year' | 'custom'>('year');
const pieTimeType = ref<'all' | 'year' | 'month'>('all');
const dateRange = ref<[Dayjs, Dayjs] | undefined>(undefined);

// ========== 响应式数据 - 数据卡片 ==========
const statisticCard = ref<Record<string, { title: string; value: number }>>({});

// ========== 响应式数据 - 营收趋势图 ==========
interface TrendChartItem {
  date: string;
  营收: number;
  支出: number;
}
const trendChartData = ref<TrendChartItem[]>([]);

// ECharts 折线图配置
const lineChartOption = computed(() => {
  return {
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        let result = params[0].name + '<br/>';
        params.forEach((item: any) => {
          result += `${item.marker}${item.seriesName}: ${item.value} 元<br/>`;
        });
        return result;
      }
    },
    legend: {
      data: ['营收', '支出'],
      top: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      outerBounds: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%'
      }
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trendChartData.value.map(item => item.date)
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value} 元'
      }
    },
    series: [
      {
        name: '营收',
        type: 'line',
        smooth: true,
        data: trendChartData.value.map(item => item.营收),
        itemStyle: {
          color: '#1890ff'
        }
      },
      {
        name: '支出',
        type: 'line',
        smooth: true,
        data: trendChartData.value.map(item => item.支出),
        itemStyle: {
          color: '#ff4d4f'
        }
      }
    ]
  };
});

// ========== 响应式数据 - 饼状图 ==========
interface HomePieChartItem {
  name: string;
  value: number;
  proportion: number;
}
const purchaserProfitData = ref<HomePieChartItem[]>([]);
const productProfitData = ref<HomePieChartItem[]>([]);

// ECharts 采购商利润饼图配置
const purchaserPieOption = computed(() => {
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 元 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '采购商利润',
        type: 'pie',
        radius: '70%',
        center: ['50%', '50%'],
        data: purchaserProfitData.value.map(item => ({
          value: item.value,
          name: item.name
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };
});

// ECharts 商品利润饼图配置
const productPieOption = computed(() => {
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 元 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '商品利润',
        type: 'pie',
        radius: '70%',
        center: ['50%', '50%'],
        data: productProfitData.value.map(item => ({
          value: item.value,
          name: item.name
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };
});

// ========== 接口请求参数 ==========
const getQueryParams = (type: 'year' | 'custom') => {
  const params: any = {
    time_type: type
  };
  
  if (type === 'custom' && dateRange.value) {
    params.start_date = dateRange.value[0].format('YYYY-MM-DD');
    params.end_date = dateRange.value[1].format('YYYY-MM-DD');
  }
  
  return params;
};

// ========== 数据类型定义 ==========
interface HomeStatisticCard {
  inventory_value: number;
  purchase_unreceived: number;
  sale_unreceived: number;
  cycle_profit?: number;
  cycle_revenue?: number;
  cycle_expend?: number;
  month_profit?: number;
  year_profit?: number;
  total_profit?: number;
}

interface HomeTrendChart {
  xAxis: string[];
  revenue_data: number[];
  expend_data: number[];
}

interface HomePieChart {
  purchaser_profit: HomePieChartItem[];
  product_profit: HomePieChartItem[];
}

// ========== 数据格式化函数 - 数据卡片 ==========
const formatStatisticCard = (data: HomeStatisticCard) => {
  statisticCard.value = {
    inventory_value: { title: '当前库存总价值', value: data.inventory_value },
    purchase_unreceived: { title: '采购未结清总额', value: data.purchase_unreceived },
    sale_unreceived: { title: '销售未结清总额', value: data.sale_unreceived },
    month_profit: { title: '本月毛利', value: data.month_profit || data.cycle_profit || 0 },
    year_profit: { title: '本年毛利', value: data.year_profit || 0 },
    total_profit: { title: '总毛利', value: data.total_profit || 0 }
  };
};

// ========== 数据格式化函数 - 营收趋势图 ==========
const formatTrendChart = (data: HomeTrendChart) => {
  const { xAxis, revenue_data, expend_data } = data;
  const result: TrendChartItem[] = [];
  xAxis.forEach((date: string, index: number) => {
    result.push({
      date,
      营收: revenue_data[index] || 0,
      支出: expend_data[index] || 0
    });
  });
  trendChartData.value = result;
};

// ========== 数据格式化函数 - 饼状图 ==========
const formatPieChart = (data: HomePieChart) => {
  purchaserProfitData.value = data.purchaser_profit;
  productProfitData.value = data.product_profit;
};

// ========== 核心请求函数 ==========
const fetchStatisticCard = async () => {
  try {
    // 数据总览不传递时间参数
    const statisticRes = await getStatisticCard();
    formatStatisticCard(statisticRes.data);
  } catch (err) {
    statisticCard.value = {};
    console.error('获取数据总览失败：', err);
  }
};

const fetchChartData = async () => {
  try {
    const queryParams = getQueryParams(timeType.value);
    // 并行请求趋势图和饼图接口
    const [pieRes, trendRes] = await Promise.all([
      getPieChart(queryParams),
      getTrendChart(queryParams)
    ]);

    formatPieChart(pieRes.data);
    formatTrendChart(trendRes.data);
  } catch (err) {
    trendChartData.value = [];
    purchaserProfitData.value = [];
    productProfitData.value = [];
    console.error('获取图表数据失败：', err);
  }
};

const fetchHomeData = async () => {
  try {
    // 并行请求所有数据
    await Promise.all([
      fetchStatisticCard(),
      fetchChartData()
    ]);
    message.success('获取首页数据成功');
  } catch (err) {
    console.error('获取首页数据失败：', err);
    message.error('获取首页数据失败，请稍后重试');
  }
};

// ========== 事件处理函数 ==========
const handleTimeTypeChange = () => {
  if (timeType.value === 'custom' && !dateRange.value) {
    const currentYear = dayjs().year();
    dateRange.value = [dayjs().year(currentYear).startOf('year'), dayjs().year(currentYear).endOf('year')];
  }
  fetchChartData();
};

const handleDateRangeChange = () => {
  if (timeType.value === 'custom') {
    // 日期范围变化时只更新图表数据
    fetchChartData();
  }
};

const handlePieTimeTypeChange = () => {
  // 饼图时间类型变化时重新获取图表数据
  fetchChartData();
};

// 页面挂载时请求数据
onMounted(() => {
  fetchHomeData();
});
</script>

<style scoped lang="scss">
.home-container {
  width: 100%;
  padding: 24px;
  box-sizing: border-box;
  background: #f5f7fa;
  min-height: 100vh;
  gap: 24px;
  display: flex;
  flex-direction: column;
}

.home-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  .header-left {
    h2 {
      margin: 0;
      color: #333;
      font-weight: 600;
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
  }
}

.stat-card-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  align-items: center;
  min-height: 120px;
  &.stat-empty {
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .stat-card {
    width: calc(100% / 3 - 16px);
    min-width: 240px;
    flex: 1;
    min-height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.chart-card {
  width: 100%;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  
  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h3 {
      margin: 0;
      color: #333;
      font-size: 16px;
    }
  }
}
.single-chart {
  height: 480px;
}

.pie-chart-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  .pie-chart {
    width: calc(50% - 12px);
    min-width: 300px;
    flex: 1;
    height: 380px;
  }
}
</style>