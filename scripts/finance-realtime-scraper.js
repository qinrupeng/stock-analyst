/**
 * 财经实时数据抓取脚本
 * 用于盘中扫描获取实时行情数据
 * 支持：东方财富、同花顺等财经网站
 */

const { chromium } = require('playwright');

class FinanceRealtimeScraper {
  constructor() {
    this.browser = null;
    this.context = null;
  }

  /**
   * 初始化浏览器
   */
  async init() {
    console.log('🚀 启动浏览器...');
    this.browser = await chromium.launch({
      headless: true,
      executablePath: process.env.CHROME_PATH || undefined // 使用系统Chrome
    });
    this.context = await this.browser.newContext();
    console.log('✅ 浏览器启动成功');
  }

  /**
   * 关闭浏览器
   */
  async close() {
    if (this.browser) {
      await this.browser.close();
      console.log('🔒 浏览器已关闭');
    }
  }

  /**
   * 获取实时指数数据
   */
  async getRealtimeIndexes() {
    const page = await this.context.newPage();
    try {
      console.log('📊 抓取实时指数...');
      await page.goto('https://quote.eastmoney.com/center/gridlist.html#hs_a_board', {
        waitUntil: 'networkidle',
        timeout: 30000
      });

      // 等待数据加载
      await page.waitForSelector('.quotebody', { timeout: 10000 });

      const indexes = await page.evaluate(() => {
        const data = [];
        const rows = document.querySelectorAll('.quotebody tr');

        rows.forEach(row => {
          const name = row.querySelector('.cell-name')?.innerText || '';
          const price = row.querySelector('.cell-price')?.innerText || '';
          const change = row.querySelector('.cell-change')?.innerText || '';

          if (name && price) {
            data.push({ name, price, change });
          }
        });

        return data.slice(0, 20); // 返回前20个
      });

      console.log(`✅ 获取到 ${indexes.length} 个指数数据`);
      return indexes;
    } catch (error) {
      console.error('❌ 抓取指数失败:', error.message);
      return [];
    } finally {
      await page.close();
    }
  }

  /**
   * 获取板块涨幅榜
   */
  async getSectorRanking() {
    const page = await this.context.newPage();
    try {
      console.log('📈 抓取板块涨幅榜...');
      await page.goto('https://quote.eastmoney.com/center/gridlist.html#hs_a_board', {
        waitUntil: 'networkidle',
        timeout: 30000
      });

      // 切换到板块标签
      await page.click('text=板块');
      await page.waitForTimeout(2000);

      const sectors = await page.evaluate(() => {
        const data = [];
        const rows = document.querySelectorAll('.quotebody tr');

        rows.forEach(row => {
          const name = row.querySelector('.cell-name')?.innerText || '';
          const change = row.querySelector('.cell-change')?.innerText || '';

          if (name && change) {
            data.push({ name, change });
          }
        });

        return data.slice(0, 30);
      });

      console.log(`✅ 获取到 ${sectors.length} 个板块数据`);
      return sectors;
    } catch (error) {
      console.error('❌ 抓取板块失败:', error.message);
      return [];
    } finally {
      await page.close();
    }
  }

  /**
   * 获取涨停板/跌停板
   */
  async getLimitUpDown() {
    const page = await this.context.newPage();
    try {
      console.log('🚀 抓取涨跌停板...');
      await page.goto('https://quote.eastmoney.com/limitup.html', {
        waitUntil: 'networkidle',
        timeout: 30000
      });

      await page.waitForSelector('#limitup', { timeout: 10000 });

      const limitUp = await page.evaluate(() => {
        const data = [];
        const rows = document.querySelectorAll('#limitup tbody tr');

        rows.forEach(row => {
          const name = row.cells[1]?.innerText || '';
          const price = row.cells[2]?.innerText || '';
          const time = row.cells[3]?.innerText || '';

          if (name) {
            data.push({ name, price, time });
          }
        });

        return data;
      });

      console.log(`✅ 获取到 ${limitUp.length} 个涨停板`);
      return limitUp;
    } catch (error) {
      console.error('❌ 抓取涨跌停失败:', error.message);
      return [];
    } finally {
      await page.close();
    }
  }

  /**
   * 获取主力资金流向
   */
  async getCapitalFlow() {
    const page = await this.context.newPage();
    try {
      console.log('💰 抓取资金流向...');
      await page.goto('https://data.eastmoney.com/zjjj.html', {
        waitUntil: 'networkidle',
        timeout: 30000
      });

      await page.waitForSelector('.zjjj-content', { timeout: 10000 });

      const flow = await page.evaluate(() => {
        const sectors = [];
        const rows = document.querySelectorAll('.zjjj-content tbody tr');

        rows.forEach(row => {
          const name = row.cells[0]?.innerText || '';
          const inflow = row.cells[1]?.innerText || '';
          const outflow = row.cells[2]?.innerText || '';
          const net = row.cells[3]?.innerText || '';

          if (name) {
            sectors.push({ name, inflow, outflow, net });
          }
        });

        return sectors.slice(0, 20);
      });

      console.log(`✅ 获取到 ${flow.length} 个板块资金流向`);
      return flow;
    } catch (error) {
      console.error('❌ 抓取资金流向失败:', error.message);
      return [];
    } finally {
      await page.close();
    }
  }

  /**
   * 获取实时热点概念
   */
  async getHotConcepts() {
    const page = await this.context.newPage();
    try {
      console.log('🔥 抓取热点概念...');
      await page.goto('https://quote.eastmoney.com/center/gridlist.html#concept', {
        waitUntil: 'networkidle',
        timeout: 30000
      });

      await page.waitForSelector('.quotebody', { timeout: 10000 });

      const concepts = await page.evaluate(() => {
        const data = [];
        const rows = document.querySelectorAll('.quotebody tr');

        rows.forEach(row => {
          const name = row.querySelector('.cell-name')?.innerText || '';
          const change = row.querySelector('.cell-change')?.innerText || '';
          const stockCount = row.querySelector('.cell-stock')?.innerText || '';

          if (name && change) {
            data.push({ name, change, stockCount });
          }
        });

        return data.slice(0, 20);
      });

      console.log(`✅ 获取到 ${concepts.length} 个热点概念`);
      return concepts;
    } catch (error) {
      console.error('❌ 抓取热点概念失败:', error.message);
      return [];
    } finally {
      await page.close();
    }
  }

  /**
   * 完整盘中扫描（一次性获取所有数据）
   */
  async fullIntradayScan() {
    await this.init();

    try {
      console.log('\n📊 开始盘中实时扫描...\n');

      // 并行抓取多个数据源
      const [indexes, sectors, limitUp, capitalFlow, concepts] = await Promise.all([
        this.getRealtimeIndexes(),
        this.getSectorRanking(),
        this.getLimitUpDown(),
        this.getCapitalFlow(),
        this.getHotConcepts()
      ]);

      console.log('\n✅ 盘中扫描完成！\n');

      return {
        timestamp: new Date().toISOString(),
        indexes,
        sectors,
        limitUp,
        capitalFlow,
        concepts,
        summary: {
          totalLimitUp: limitUp.length,
          hotSector: sectors[0] || null,
          hotConcept: concepts[0] || null,
          topInflow: capitalFlow[0] || null
        }
      };
    } catch (error) {
      console.error('❌ 盘中扫描失败:', error.message);
      throw error;
    } finally {
      await this.close();
    }
  }
}

// 导出类
module.exports = FinanceRealtimeScraper;

// 如果直接运行
if (require.main === module) {
  (async () => {
    const scraper = new FinanceRealtimeScraper();

    try {
      const data = await scraper.fullIntradayScan();
      console.log('\n📊 扫描结果：\n');
      console.log(JSON.stringify(data, null, 2));
    } catch (error) {
      console.error('错误:', error.message);
    }
  })();
}
