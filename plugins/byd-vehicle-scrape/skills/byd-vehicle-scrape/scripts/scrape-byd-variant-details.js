const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// 命令行参数解析
const args = process.argv.slice(2);
const CLI_OPTIONS = {
  model: null,      // 指定车型名称
  delay: 500,       // 请求间延迟(ms)
  retries: 3,       // 重试次数
  timeout: 60000    // 页面超时(ms)
};

// 解析命令行参数
args.forEach(arg => {
  if (arg.startsWith('--model=')) {
    CLI_OPTIONS.model = arg.split('=')[1];
  } else if (arg.startsWith('--delay=')) {
    CLI_OPTIONS.delay = parseInt(arg.split('=')[1]);
  } else if (arg.startsWith('--retries=')) {
    CLI_OPTIONS.retries = parseInt(arg.split('=')[1]);
  } else if (arg.startsWith('--timeout=')) {
    CLI_OPTIONS.timeout = parseInt(arg.split('=')[1]);
  } else if (arg === '--help') {
    console.log(`
用法: node js/scrape-byd-variant-details.js [选项]

选项:
  --model=<名称>    只爬取指定车型 (如: --model="Atto 1")
  --delay=<毫秒>    请求间延迟 (默认: 500)
  --retries=<次数>  失败重试次数 (默认: 3)
  --timeout=<毫秒>  页面加载超时 (默认: 60000)
  --help            显示帮助信息
`);
    process.exit(0);
  }
});

// 所有车型的配置 URL
const VEHICLE_URLS = [
  { name: 'Atto 1', type: 'Electric', bodyType: 'Hatchback', seats: '5', url: 'https://bydhaberfield.com.au/configurator/byd-atto-1' },
  { name: 'Atto 2', type: 'Electric', bodyType: 'SUV', seats: '5', url: 'https://bydhaberfield.com.au/configurator/byd-atto-2' },
  { name: 'Atto 3', type: 'Electric', bodyType: 'SUV', seats: '5', url: 'https://bydhaberfield.com.au/configurator/byd-atto-3' },
  { name: 'Dolphin', type: 'Electric', bodyType: 'Hatchback', seats: '5', url: 'https://bydhaberfield.com.au/configurator/byd-dolphin' },
  { name: 'Seal', type: 'Electric', bodyType: 'Sedan', seats: '5', url: 'https://bydhaberfield.com.au/configurator/byd-seal' },
  { name: 'Sealion 5', type: 'Hybrid', bodyType: 'SUV', seats: '5', url: 'https://bydhaberfield.com.au/configurator/byd-sealion-5' },
  { name: 'Sealion 6', type: 'Hybrid', bodyType: 'SUV', seats: '5', url: 'https://bydhaberfield.com.au/configurator/byd-sealion-6' },
  { name: 'Sealion 7', type: 'Electric', bodyType: 'SUV', seats: '5', url: 'https://bydhaberfield.com.au/configurator/byd-sealion-7' },
  { name: 'Sealion 8', type: 'Hybrid', bodyType: 'SUV', seats: '7', url: 'https://bydhaberfield.com.au/configurator/byd-sealion-8' },
  { name: 'Shark 6', type: 'Hybrid', bodyType: 'Utility', seats: '5', url: 'https://bydhaberfield.com.au/configurator/byd-shark-6' }
];

/**
 * 从 learnMoreModal 文本中提取完整规格参数
 * @param {string} modalText - learnMoreModal 内容
 * @returns {Object} 分类组织的规格数据
 */
function extractFullSpecs(modalText) {
  const specs = {
    powertrain: {},
    battery: {},
    dimensions: {},
    weight: {},
    chassis: {},
    performance: {}
  };

  if (!modalText) return specs;

  // 动力系统
  specs.powertrain = {
    maxPower: extractValue(modalText, /Maximum\s*Power\s*[-–:]\s*([\d.]+\s*kW)/i),
    maxTorque: extractValue(modalText, /Maximum\s*Torque\s*[-–:]\s*([\d.]+\s*Nm)/i),
    motorType: extractValue(modalText, /Motor\s*Type\s*[-–:]\s*([^-–\n]+)/i),
    driveType: extractValue(modalText, /Drive\s*(?:Type\s*)?[-–:]\s*([^-–\n]+)/i)
  };

  // 电池和续航
  specs.battery = {
    capacity: extractValue(modalText, /Battery\s*(?:Capacity\s*)?[-–:]\s*([\d.]+\s*kWh)/i),
    type: extractValue(modalText, /Battery\s*Type\s*[-–:]\s*([^-–\n]+)/i),
    range: extractValue(modalText, /(?:Range|Driving\s*Range)\s*[-–:]\s*(?:Up\s*to\s*)?([\d,]+\s*km)/i),
    fastChargeTime: extractValue(modalText, /Fast\s*Charg(?:e|ing)\s*(?:Time\s*)?[-–:]\s*([\d.]+\s*h(?:ours?)?)/i),
    slowChargeTime: extractValue(modalText, /(?:Slow|AC)\s*Charg(?:e|ing)\s*(?:Time\s*)?[-–:]\s*([\d.]+\s*h(?:ours?)?)/i)
  };

  // 性能
  specs.performance = {
    acceleration: extractValue(modalText, /0-100\s*km\/h\s*(?:in\s*)?[-–:]\s*([\d.]+\s*s)/i),
    topSpeed: extractValue(modalText, /Top\s*Speed\s*[-–:]\s*([\d]+\s*km\/h)/i)
  };

  // 尺寸
  specs.dimensions = {
    length: extractValue(modalText, /Length\s*[-–:]\s*([\d,]+\s*mm)/i),
    width: extractValue(modalText, /Width\s*[-–:]\s*([\d,]+\s*mm)/i),
    height: extractValue(modalText, /Height\s*[-–:]\s*([\d,]+\s*mm)/i),
    wheelbase: extractValue(modalText, /Wheelbase\s*[-–:]\s*([\d,]+\s*mm)/i),
    groundClearance: extractValue(modalText, /Ground\s*Clearance\s*[-–:]\s*([\d,]+\s*mm)/i)
  };

  // 重量
  specs.weight = {
    curbWeight: extractValue(modalText, /(?:Curb|Kerb)\s*Weight\s*[-–:]\s*([\d,]+\s*kg)/i),
    grossWeight: extractValue(modalText, /Gross\s*(?:Vehicle\s*)?Weight\s*[-–:]\s*([\d,]+\s*kg)/i)
  };

  // 底盘
  specs.chassis = {
    frontSuspension: extractValue(modalText, /Front\s*Suspension\s*[-–:]\s*([^-–\n]+)/i),
    rearSuspension: extractValue(modalText, /Rear\s*Suspension\s*[-–:]\s*([^-–\n]+)/i),
    tireSpec: extractValue(modalText, /Tire\s*(?:Specification\s*)?[-–:]\s*([^-–\n]+)/i),
    brakeSystem: extractValue(modalText, /Brake\s*(?:System\s*)?[-–:]\s*([^-–\n]+)/i)
  };

  // 清理空值
  Object.keys(specs).forEach(category => {
    specs[category] = Object.fromEntries(
      Object.entries(specs[category]).filter(([_, v]) => v !== null)
    );
    if (Object.keys(specs[category]).length === 0) {
      delete specs[category];
    }
  });

  return specs;
}

/**
 * 提取单个值的辅助函数
 */
function extractValue(text, regex) {
  const match = text.match(regex);
  return match ? match[1].trim() : null;
}

/**
 * 清理文本中的 HTML 标签
 * @param {string} text - 包含 HTML 的文本
 * @returns {string} 纯文本
 */
function cleanHtml(text) {
  if (!text) return '';
  return text
    .replace(/<[^>]+>/g, ' ')           // 移除 HTML 标签
    .replace(/&nbsp;/g, ' ')            // 替换 HTML 实体
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/\s+/g, ' ')               // 合并空白字符
    .trim();
}

/**
 * 规范化图片 URL，将相对路径转换为完整 URL
 * @param {string} url - 原始 URL
 * @returns {string} 完整 URL
 */
function normalizeImageUrl(url) {
  if (!url) return null;
  // 如果已经是完整 URL，直接返回
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  // 相对路径补全域名
  if (url.startsWith('/')) {
    return 'https://virtualyard.com.au' + url;
  }
  return url;
}

/**
 * 从 data-option JSON 和 DOM 元素中提取图片链接
 * 主要从 <img> 标签的 src 属性提取
 * @param {Object} option - data-option 解析后的 JSON 对象
 * @param {Element} el - DOM 元素
 * @returns {Object} { thumbnail, preview }
 */
function extractOptionImages(option, el) {
  const images = { thumbnail: null, preview: null };

  if (!el) return images;

  // 1. 从子 <img> 元素提取（主要方式）
  const imgs = el.querySelectorAll('img');
  const imgUrls = [];

  imgs.forEach(img => {
    // 收集所有有效图片 URL
    if (img.src && !img.src.includes('data:image') && !img.src.includes('placeholder')) {
      imgUrls.push({
        url: img.src,
        width: img.naturalWidth || img.width || 0,
        height: img.naturalHeight || img.height || 0
      });
    }
  });

  // 2. 根据数量和尺寸分配大小图
  if (imgUrls.length === 1) {
    // 只有一张图，作为大图
    images.preview = imgUrls[0].url;
  } else if (imgUrls.length >= 2) {
    // 多张图：按尺寸排序，最大的作为大图，最小的作为小图
    imgUrls.sort((a, b) => (b.width * b.height) - (a.width * a.height));
    images.preview = imgUrls[0].url;    // 最大图
    images.thumbnail = imgUrls[imgUrls.length - 1].url;  // 最小图
  }

  // 3. 尝试从 CSS background-image 提取（备选）
  if (!images.thumbnail && !images.preview) {
    const bgEl = el.querySelector('[style*="background"], [style*="url"]');
    if (bgEl) {
      const style = bgEl.getAttribute('style') || '';
      const urlMatch = style.match(/url\(['"]?([^'")]+)['"]?\)/i);
      if (urlMatch) {
        images.thumbnail = urlMatch[1];
      }
    }
  }

  // 4. 从 data-option JSON 字段提取（备选）
  const jsonFields = ['image', 'imageUrl', 'thumbnail', 'previewImage', 'swatch'];
  for (const field of jsonFields) {
    if (option[field] && typeof option[field] === 'string') {
      if (!images.preview) {
        images.preview = option[field];
      } else if (!images.thumbnail) {
        images.thumbnail = option[field];
      }
      break;
    }
  }

  // 规范化 URL（将相对路径转换为完整 URL）
  return {
    thumbnail: normalizeImageUrl(images.thumbnail),
    preview: normalizeImageUrl(images.preview)
  };
}

/**
 * 解析价格字符串为数字
 * @param {string} priceStr - 价格字符串（如 "$46,990"）
 * @returns {number} 价格数值
 */
function parsePrice(priceStr) {
  if (!priceStr) return 0;
  const value = parseFloat(priceStr.replace(/[$,]/g, ''));
  return Math.round(value * 100) / 100;  // 保留两位小数，避免浮点精度问题
}

/**
 * 格式化本地时区时间戳
 * @returns {string} 格式: _yyyy-MM-dd_HH-mm-ss
 */
function formatLocalTimestamp() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  return `_${year}-${month}-${day}_${hours}-${minutes}-${seconds}`;
}

/**
 * 从 onRoadFees 中提取 Stamp Duty
 * @param {Array} onRoadFees - On-Road Fees 数组
 * @returns {number} Stamp Duty 金额
 */
function extractStampDuty(onRoadFees) {
  if (!onRoadFees || !Array.isArray(onRoadFees)) return 0;
  const fee = onRoadFees.find(f => f.item && f.item.includes('Stamp Duty'));
  return fee ? parsePrice(fee.amount) : 0;
}

/**
 * 提取基础 On-Road Fees（不随车价变化的部分）
 * @param {Page} page - Playwright 页面对象
 * @returns {Object} 基础费用对象
 */
async function extractBaseOnRoadFees(page) {
  const pricing = await extractPricingData(page);
  const fixedFees = { registration: 0, ctp: 0, dealerDelivery: 0, slimlinePlate: 0, subtotal: 0 };

  for (const fee of pricing.onRoadFees) {
    // 保留原始金额字符串（含小数）
    const amountStr = fee.amount;  // 如 "$463.52"
    const amountFloat = parseFloat(amountStr.replace(/[$,]/g, ''));

    if (fee.item.includes('Registration') && !fee.item.includes('State')) {
      fixedFees.registration = amountFloat;
      fixedFees.registrationStr = amountStr;
      fixedFees.subtotal += amountFloat;
    } else if (fee.item.includes('CTP')) {
      fixedFees.ctp = amountFloat;
      fixedFees.ctpStr = amountStr;
      fixedFees.subtotal += amountFloat;
    } else if (fee.item.includes('Dealer Delivery')) {
      fixedFees.dealerDelivery = amountFloat;
      fixedFees.dealerDeliveryStr = amountStr;
      fixedFees.subtotal += amountFloat;
    } else if (fee.item.includes('Slimline') || fee.item.includes('Plate')) {
      fixedFees.slimlinePlate = amountFloat;
      fixedFees.slimlinePlateStr = amountStr;
      fixedFees.subtotal += amountFloat;
    }
    // Stamp Duty 不计入 subtotal，因为它是随车价变化的
  }
  return fixedFees;
}

/**
 * 通用选项选择函数
 * @param {Page} page - Playwright 页面对象
 * @param {string} type - 选项类型（variant, colour, wheels, interior）
 * @param {string} id - 选项 ID
 * @returns {Promise<boolean>} 是否成功选择
 */
async function selectOption(page, type, id) {
  // 方案1: 通过 radio input 选择（点击关联的 label）
  const radio = page.locator(`input[value="${id}"]`);
  if (await radio.count().catch(() => 0) > 0) {
    const isChecked = await radio.isChecked().catch(() => false);
    if (!isChecked) {
      // 尝试通过 label 点击
      const radioId = await radio.getAttribute('id').catch(() => null);
      if (radioId) {
        const label = page.locator(`label[for="${radioId}"]`);
        if (await label.isVisible({ timeout: 1000 }).catch(() => false)) {
          await label.click({ force: true });
          await page.waitForTimeout(800);
          return true;
        }
      }
      // 直接点击 radio
      await radio.click({ force: true });
      await page.waitForTimeout(800);
    }
    return true;
  }

  // 方案2: 通过 data-option 属性选择
  const optionEl = page.locator(`[data-option*='"id":"${id}"']`);
  if (await optionEl.isVisible({ timeout: 1000 }).catch(() => false)) {
    await optionEl.click();
    await page.waitForTimeout(800);
    return true;
  }

  return false;
}

/**
 * 爬取版本、颜色和轮毂的所有价格组合
 * @param {Page} page - Playwright 页面对象
 * @param {Array} variants - 版本列表
 * @param {Array} colors - 颜色列表
 * @param {Array} wheels - 轮毂列表
 * @returns {Object} 价格矩阵数据
 */
async function scrapePricingMatrix(page, variants, colors, wheels, interiors) {
  const combinations = [];
  const POST_CODE = '2000';

  // 确保 Post Code 已填写
  await fillPostCode(page, POST_CODE);
  await page.waitForTimeout(1000);

  for (const variant of variants) {
    console.log(`    处理版本: ${variant.name}`);

    // 根据版本的 availableConfig 过滤配置项
    let availableWheels = wheels;
    let availableColors = colors;
    let availableInteriors = interiors;

    if (variant.availableConfig) {
      if (variant.availableConfig.wheels) {
        const allowedWheelIds = variant.availableConfig.wheels;
        availableWheels = wheels.filter(w => allowedWheelIds.includes(w.id));
      }
      if (variant.availableConfig.colour) {
        const allowedColorIds = variant.availableConfig.colour;
        availableColors = colors.filter(c => allowedColorIds.includes(c.id));
      }
      if (variant.availableConfig.interior) {
        const allowedInteriorIds = variant.availableConfig.interior;
        availableInteriors = interiors.filter(i => allowedInteriorIds.includes(i.id));
      }
    }

    // 使用过滤后的配置列表
    const wheelsList = availableWheels && availableWheels.length > 0
      ? availableWheels
      : [{ id: null, name: 'Default', price: 0 }];
    const interiorsList = availableInteriors && availableInteriors.length > 0
      ? availableInteriors
      : [{ id: null, name: 'Default', price: 0 }];
    const colorsList = availableColors && availableColors.length > 0
      ? availableColors
      : colors;

    // 选择版本
    await selectOption(page, 'variant', variant.id);
    await page.waitForTimeout(1000);

    for (const color of colorsList) {
      console.log(`      颜色: ${color.name} (+$${color.price || 0})`);

      // 选择颜色
      await selectOption(page, 'colour', color.id);
      await page.waitForTimeout(800);

      for (const wheel of wheelsList) {
        // 如果有轮毂选项且不是默认值,则选择
        if (wheel.id) {
          console.log(`        轮毂: ${wheel.name} (+$${wheel.price || 0})`);
          await selectOption(page, 'wheel', wheel.id);
          await page.waitForTimeout(500);
        }

        for (const interior of interiorsList) {
          // 如果有内饰选项且不是默认值,则选择
          if (interior.id) {
            console.log(`          内饰: ${interior.name} (+$${interior.price || 0})`);
            await selectOption(page, 'interior', interior.id);
            await page.waitForTimeout(500);
          }

          // 等待价格更新并提取（带重试）
          let pricing = null;
          let retries = 3;
          while (retries > 0) {
            pricing = await extractPricingData(page);
            if (pricing.driveAwayPrice && parsePrice(pricing.driveAwayPrice) > 0) {
              break;
            }
            await page.waitForTimeout(500);
            retries--;
          }

          // 从 pricing.onRoadFees 提取所有费用项
          let stampDutyStr = '', ctpStr = '', registrationStr = '',
              dealerDeliveryStr = '', slimlinePlateStr = '';
          let stampDuty = 0, ctp = 0, registration = 0,
              dealerDelivery = 0, slimlinePlate = 0;

          for (const fee of pricing.onRoadFees) {
            const amountFloat = parseFloat(fee.amount.replace(/[$,]/g, ''));
            if (fee.item.includes('Stamp Duty')) {
              stampDutyStr = fee.amount;
              stampDuty = amountFloat;
            } else if (fee.item.includes('CTP')) {
              ctpStr = fee.amount;
              ctp = amountFloat;
            } else if (fee.item.includes('Registration') && !fee.item.includes('State')) {
              registrationStr = fee.amount;
              registration = amountFloat;
            } else if (fee.item.includes('Dealer Delivery')) {
              dealerDeliveryStr = fee.amount;
              dealerDelivery = amountFloat;
            } else if (fee.item.includes('Slimline') || fee.item.includes('Plate Fee')) {
              slimlinePlateStr = fee.amount;
              slimlinePlate = amountFloat;
            }
          }

          // 从 pricing.campaignIncentives 提取促销信息
          let campaignIncentiveName = '';
          let campaignIncentiveStr = '';
          let campaignIncentive = 0;

          if (pricing.campaignIncentives && pricing.campaignIncentives.length > 0) {
            const ci = pricing.campaignIncentives[0];  // 通常只有一个促销
            campaignIncentiveName = ci.name;
            campaignIncentiveStr = ci.amount;
            // 解析金额（负数折扣）
            campaignIncentive = parseFloat(ci.amount.replace(/[$,]/g, ''));
          }

          // 提取左侧轮播区的组合预览图
          const carouselImages = await page.evaluate(() => {
            const carousel = document.querySelector('#design-carousel');
            if (!carousel) return null;

            const images = {
              colour: null,
              wheels: null,
              interior: null
            };

            // 查找轮播项中的图片
            const items = carousel.querySelectorAll('.carousel-item');
            items.forEach(item => {
              const img = item.querySelector('img');
              if (img && img.src) {
                // 从 class 中提取类型: "img-fluid dynamic-option-image colour 1475 1"
                const classMatch = img.className.match(/dynamic-option-image\s+(\w+)/);
                if (classMatch) {
                  const type = classMatch[1].toLowerCase();
                  if (type === 'colour' || type === 'wheels' || type === 'interior') {
                    images[type] = img.src;
                  }
                }
              }
            });

            // 如果没有从轮播项中找到，尝试直接查找动态图片
            if (!images.colour && !images.wheels && !images.interior) {
              const dynamicImages = carousel.querySelectorAll('img.dynamic-option-image, img[src*="composit.php"]');
              dynamicImages.forEach(img => {
                if (img.src) {
                  const classMatch = img.className.match(/dynamic-option-image\s+(\w+)/);
                  if (classMatch) {
                    const type = classMatch[1].toLowerCase();
                    if (type === 'colour' || type === 'wheels' || type === 'interior') {
                      images[type] = img.src;
                    }
                  } else if (img.src.includes('t=colour')) {
                    images.colour = img.src;
                  } else if (img.src.includes('t=wheels')) {
                    images.wheels = img.src;
                  } else if (img.src.includes('t=interior')) {
                    images.interior = img.src;
                  }
                }
              });
            }

            // 检查是否有有效的图片
            const hasImages = Object.values(images).some(v => v !== null);
            return hasImages ? images : null;
          });

          combinations.push({
            // Order Details - 版本
            variantId: variant.id,
            variantName: variant.name,
            variantPrice: variant.price,
            // Order Details - 颜色
            colorId: color.id,
            colorName: color.name,
            colorPrice: color.price || 0,
            // Order Details - 轮毂
            wheelId: wheel.id,
            wheelName: wheel.name,
            wheelPrice: wheel.price || 0,
            // Order Details - 内饰
            interiorId: interior.id,
            interiorName: interior.name,
            interiorPrice: interior.price || 0,
            // Order Details - Vehicle Subtotal
            vehicleSubtotal: parsePrice(pricing.vehicleSubtotal),
            vehicleSubtotalStr: pricing.vehicleSubtotal,
            // Order Details - On Road Fees（实时提取）
            stampDuty: stampDuty,
            stampDutyStr: stampDutyStr,
            registration: registration,
            registrationStr: registrationStr,
            ctp: ctp,
            ctpStr: ctpStr,
            dealerDelivery: dealerDelivery,
            dealerDeliveryStr: dealerDeliveryStr,
            slimlinePlate: slimlinePlate,
            slimlinePlateStr: slimlinePlateStr,
            onRoadFeesSubtotal: registration + ctp + dealerDelivery + slimlinePlate + stampDuty,
            // Campaign Incentive（促销激励）
            campaignIncentiveName: campaignIncentiveName,
            campaignIncentive: campaignIncentive,
            campaignIncentiveStr: campaignIncentiveStr,
            // Drive Away Price
            driveAwayPrice: parsePrice(pricing.driveAwayPrice),
            driveAwayPriceStr: pricing.driveAwayPrice,
            // 组合预览图（轮播区图片）
            images: carouselImages
          });
        }
      }
    }
  }

  // 计算价格范围（过滤掉 0 值）
  const prices = combinations.map(c => c.driveAwayPrice).filter(p => p > 0);

  return {
    postCode: POST_CODE,
    registrationState: 'NSW',
    registrationType: 'Personal',
    combinations: combinations,
    summary: {
      totalCombinations: combinations.length,
      priceRange: {
        min: prices.length > 0 ? Math.min(...prices) : 0,
        max: prices.length > 0 ? Math.max(...prices) : 0
      },
      // Campaign Incentive 统计
      hasCampaignIncentive: combinations.some(c => c.campaignIncentive !== 0),
      campaignIncentiveCount: combinations.filter(c => c.campaignIncentive !== 0).length
    }
  };
}

/**
 * 从配置文本中提取并分类标准配置
 * @param {string} featuresText - 配置文本
 * @returns {Object} 分类的配置项
 */
function extractStandardFeatures(featuresText) {
  const features = {
    safety: [],
    comfort: [],
    technology: [],
    exterior: [],
    interior: [],
    other: []
  };

  if (!featuresText) return features;

  // 先清理 HTML
  const cleanText = cleanHtml(featuresText);

  // 关键词分类
  const keywords = {
    safety: [
      'AEB', 'Autonomous Emergency Braking', 'Lane Keep', 'Lane Departure', 'Blind Spot',
      'Adaptive Cruise', 'ACC', 'Airbag', 'ABS', 'ESP', 'Traction Control', 'Collision',
      'Safety', 'Rear Cross Traffic', 'Forward Collision', 'Driver Monitoring',
      'Emergency', 'Isofix', 'Child Seat', 'Seatbelt', 'Pretensioner', 'Pedestrian',
      'Tire Pressure', 'TPMS', 'Anti-lock', 'Brake Assist', 'Hill Start', 'Hill Descent'
    ],
    comfort: [
      'Seat', 'Heated', 'Ventilated', 'Climate', 'Air Conditioning', 'Sunroof', 'Panoramic',
      'Leather', 'Memory', 'Massage', 'Lumbar', 'Power Adjust', 'Keyless', 'Push Start',
      'Remote Start', 'Wireless Charging', 'Ambient Light', 'Privacy Glass', 'Tinted',
      'Rain Sensing', 'Auto Wiper', 'Auto Headlight', 'Power Tailgate', 'Hands-free',
      'Cruise Control', 'Steering Wheel', 'Electric Adjust', 'Foldable'
    ],
    technology: [
      'Touchscreen', 'Display', 'Navigation', 'GPS', 'CarPlay', 'Android Auto',
      'Bluetooth', 'USB', 'HDMI', 'Wi-Fi', 'Hotspot', 'OTA', 'Over-the-Air',
      'Infotainment', 'Audio', 'Speaker', 'Sound System', 'Instrument Cluster',
      'HUD', 'Head-up Display', 'Digital Key', 'App', 'Voice Control', 'Wireless'
    ],
    exterior: [
      'LED', 'Headlight', 'Taillight', 'Fog Light', 'Daytime Running', 'DRL',
      'Alloy Wheel', 'Wheel', 'Tire', 'Mirror', 'Door Handle', 'Grille',
      'Spoiler', 'Roof Rack', 'Tow Bar', 'Skid Plate', 'Mud Flap', 'Wiper'
    ],
    interior: [
      'Upholstery', 'Trim', 'Dashboard', 'Console', 'Storage', 'Cup Holder',
      'Glove Box', 'Armrest', 'Floor Mat', 'Cargo', 'Boot', 'Trunk'
    ]
  };

  // 分割文本为单独的配置项（使用 <li> 标签或换行分割）
  let items = [];
  if (featuresText.includes('<li>')) {
    // 从 <li> 标签提取
    const liMatches = featuresText.matchAll(/<li>([^<]+)<\/li>/gi);
    for (const match of liMatches) {
      items.push(cleanHtml(match[1]));
    }
  }
  // 额外用换行和符号分割
  const extraItems = cleanText.split(/[,•·\n]+/).map(item => item.trim()).filter(item => item.length > 3);
  items = [...new Set([...items, ...extraItems])];

  items.forEach(item => {
    let categorized = false;

    for (const [category, categoryKeywords] of Object.entries(keywords)) {
      if (category === 'other') continue;

      for (const keyword of categoryKeywords) {
        if (item.toLowerCase().includes(keyword.toLowerCase())) {
          if (!features[category].includes(item)) {
            features[category].push(item);
          }
          categorized = true;
          break;
        }
      }
      if (categorized) break;
    }

    if (!categorized && item.length > 5) {
      features.other.push(item);
    }
  });

  // 清理空数组
  Object.keys(features).forEach(key => {
    if (features[key].length === 0) {
      delete features[key];
    }
  });

  return features;
}

/**
 * 带重试的页面访问
 * @param {Page} page - Playwright 页面对象
 * @param {string} url - 目标 URL
 * @param {number} retries - 重试次数
 * @returns {Promise<boolean>} 是否成功
 */
async function gotoWithRetry(page, url, retries = 3) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      console.log(`  尝试访问 (第 ${attempt}/${retries} 次)...`);
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: CLI_OPTIONS.timeout });
      await page.waitForTimeout(2000);
      return true;
    } catch (e) {
      console.log(`  访问失败: ${e.message}`);
      if (attempt < retries) {
        console.log(`  等待 ${attempt * 2000}ms 后重试...`);
        await page.waitForTimeout(attempt * 2000);
      }
    }
  }
  return false;
}

/**
 * 主爬取函数
 */
async function scrapeVariantDetails() {
  console.log('启动浏览器...');
  console.log(`配置: 延迟=${CLI_OPTIONS.delay}ms, 重试=${CLI_OPTIONS.retries}次, 超时=${CLI_OPTIONS.timeout}ms`);

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // 根据命令行参数过滤车型（精确匹配）
  const vehiclesToProcess = CLI_OPTIONS.model
    ? VEHICLE_URLS.filter(v => v.name.toLowerCase() === CLI_OPTIONS.model.toLowerCase())
    : VEHICLE_URLS;

  if (vehiclesToProcess.length === 0) {
    console.log(`未找到匹配的车型: ${CLI_OPTIONS.model}`);
    await browser.close();
    return [];
  }

  console.log(`将处理 ${vehiclesToProcess.length} 款车型`);

  const allModels = [];
  const failedModels = [];

  try {
    for (const vehicle of vehiclesToProcess) {
      console.log(`\n========================================`);
      console.log(`处理车型: ${vehicle.name} (${vehicle.type})`);
      console.log(`URL: ${vehicle.url}`);

      const modelData = {
        modelName: vehicle.name,
        modelType: vehicle.type,
        bodyType: vehicle.bodyType,
        seats: vehicle.seats,
        buildPriceUrl: vehicle.url,
        variants: [],
        options: {
          exteriorColors: [],
          wheels: [],
          interiors: [],
          accessories: []
        },
        pricingMatrix: null
      };

      // 使用带重试的页面访问
      const success = await gotoWithRetry(page, vehicle.url, CLI_OPTIONS.retries);

      if (!success) {
        console.error(`  车型 ${vehicle.name} 访问失败，跳过`);
        failedModels.push(vehicle.name);
        allModels.push(modelData);
        continue;
      }

      try {
        // 处理位置选择弹窗
        await handleLocationPopup(page);

        // 等待颜色选项加载（data-option 中包含 type="colour" 的元素）
        await page.waitForSelector('[data-option*="type"][data-option*="colour"]', { timeout: 10000 }).catch(() => {
          console.log('  警告: 未找到颜色选项，可能页面结构有变化');
        });
        await page.waitForTimeout(1000); // 额外等待确保所有选项加载完成

        // 使用 data-option 属性提取所有配置数据（增强版）
        const configData = await page.evaluate(() => {
          // 在浏览器环境中定义 URL 规范化函数
          function normalizeImageUrl(url) {
            if (!url) return null;
            if (url.startsWith('http://') || url.startsWith('https://')) {
              return url;
            }
            if (url.startsWith('/')) {
              return 'https://virtualyard.com.au' + url;
            }
            return url;
          }

          const data = {
            variants: [],
            colors: [],
            wheels: [],
            interiors: [],
            accessories: []
          };

          document.querySelectorAll('[data-option]').forEach(el => {
            try {
              const option = JSON.parse(el.getAttribute('data-option'));

              if (option.type === 'variant' && option.name && option.price) {
                // 提取 learnMoreModal 完整文本用于后续解析
                const learnMoreText = option.learnMoreModal || '';

                // 提取 description 中的配置项
                const description = option.description || '';

                // 从页面元素中提取额外的规格信息
                const additionalSpecs = {};
                if (option.specs) {
                  Object.assign(additionalSpecs, option.specs);
                }

                // 解析 data 字段获取可用配置映射
                let availableConfig = null;
                if (option.data) {
                  try {
                    const variantData = JSON.parse(option.data);
                    if (variantData.available && variantData.available[0]) {
                      availableConfig = variantData.available[0];
                    }
                  } catch (e) {
                    // data 字段解析失败，忽略
                  }
                }

                data.variants.push({
                  id: option.id,
                  name: option.name.replace(/^BYD\s+/i, ''),
                  price: parseInt(option.price),
                  description: description,
                  learnMoreModal: learnMoreText,
                  additionalSpecs: additionalSpecs,
                  // 保存可用配置映射
                  availableConfig: availableConfig
                });
              } else if (option.type === 'colour' && option.name) {
                if (!data.colors.find(c => c.id === option.id)) {
                  // 使用增强的图片提取逻辑
                  const images = { thumbnail: null, preview: null };
                  const imgs = el.querySelectorAll('img');
                  const imgUrls = [];

                  imgs.forEach(img => {
                    if (img.src && !img.src.includes('data:image') && !img.src.includes('placeholder')) {
                      imgUrls.push({
                        url: img.src,
                        width: img.naturalWidth || img.width || 0,
                        height: img.naturalHeight || img.height || 0
                      });
                    }
                  });

                  if (imgUrls.length === 1) {
                    images.preview = imgUrls[0].url;
                  } else if (imgUrls.length >= 2) {
                    imgUrls.sort((a, b) => (b.width * b.height) - (a.width * a.height));
                    images.preview = imgUrls[0].url;
                    images.thumbnail = imgUrls[imgUrls.length - 1].url;
                  }

                  // 备选：从 CSS background-image 提取
                  if (!images.thumbnail && !images.preview) {
                    const bgEl = el.querySelector('[style*="background"], [style*="url"]');
                    if (bgEl) {
                      const style = bgEl.getAttribute('style') || '';
                      const urlMatch = style.match(/url\(['"]?([^'")]+)['"]?\)/i);
                      if (urlMatch) {
                        images.thumbnail = urlMatch[1];
                      }
                    }
                  }

                  // 备选：从 JSON 字段提取
                  const jsonFields = ['image', 'imageUrl', 'thumbnail', 'previewImage', 'swatch'];
                  for (const field of jsonFields) {
                    if (option[field] && typeof option[field] === 'string') {
                      if (!images.preview) {
                        images.preview = option[field];
                      } else if (!images.thumbnail) {
                        images.thumbnail = option[field];
                      }
                      break;
                    }
                  }

                  data.colors.push({
                    id: option.id,
                    name: option.name,
                    price: parseInt(option.price) || 0,
                    images: {
                      thumbnail: normalizeImageUrl(images.thumbnail),
                      preview: normalizeImageUrl(images.preview)
                    }
                  });
                }
              } else if (option.type === 'wheels' && option.name) {
                if (!data.wheels.find(w => w.id === option.id)) {
                  // 提取轮毂图片
                  const images = { thumbnail: null, preview: null };
                  const imgs = el.querySelectorAll('img');
                  const imgUrls = [];

                  imgs.forEach(img => {
                    if (img.src && !img.src.includes('data:image') && !img.src.includes('placeholder')) {
                      imgUrls.push({
                        url: img.src,
                        width: img.naturalWidth || img.width || 0,
                        height: img.naturalHeight || img.height || 0
                      });
                    }
                  });

                  if (imgUrls.length === 1) {
                    images.preview = imgUrls[0].url;
                  } else if (imgUrls.length >= 2) {
                    imgUrls.sort((a, b) => (b.width * b.height) - (a.width * a.height));
                    images.preview = imgUrls[0].url;
                    images.thumbnail = imgUrls[imgUrls.length - 1].url;
                  }

                  // 备选：从 JSON 字段提取
                  const jsonFields = ['image', 'imageUrl', 'thumbnail', 'previewImage'];
                  for (const field of jsonFields) {
                    if (option[field] && typeof option[field] === 'string') {
                      if (!images.preview) {
                        images.preview = option[field];
                      } else if (!images.thumbnail) {
                        images.thumbnail = option[field];
                      }
                      break;
                    }
                  }

                  data.wheels.push({
                    id: option.id,
                    name: option.name,
                    subname: option.subname || '',
                    price: parseInt(option.price) || 0,
                    images: {
                      thumbnail: normalizeImageUrl(images.thumbnail),
                      preview: normalizeImageUrl(images.preview)
                    }
                  });
                }
              } else if (option.type === 'interior' && option.name) {
                if (!data.interiors.find(i => i.id === option.id)) {
                  // 提取内饰图片
                  const images = { thumbnail: null, preview: null };
                  const imgs = el.querySelectorAll('img');
                  const imgUrls = [];

                  imgs.forEach(img => {
                    if (img.src && !img.src.includes('data:image') && !img.src.includes('placeholder')) {
                      imgUrls.push({
                        url: img.src,
                        width: img.naturalWidth || img.width || 0,
                        height: img.naturalHeight || img.height || 0
                      });
                    }
                  });

                  if (imgUrls.length === 1) {
                    images.preview = imgUrls[0].url;
                  } else if (imgUrls.length >= 2) {
                    imgUrls.sort((a, b) => (b.width * b.height) - (a.width * a.height));
                    images.preview = imgUrls[0].url;
                    images.thumbnail = imgUrls[imgUrls.length - 1].url;
                  }

                  // 备选：从 JSON 字段提取
                  const jsonFields = ['image', 'imageUrl', 'thumbnail', 'previewImage'];
                  for (const field of jsonFields) {
                    if (option[field] && typeof option[field] === 'string') {
                      if (!images.preview) {
                        images.preview = option[field];
                      } else if (!images.thumbnail) {
                        images.thumbnail = option[field];
                      }
                      break;
                    }
                  }

                  data.interiors.push({
                    id: option.id,
                    name: option.name,
                    price: parseInt(option.price) || 0,
                    images: {
                      thumbnail: normalizeImageUrl(images.thumbnail),
                      preview: normalizeImageUrl(images.preview)
                    }
                  });
                }
              } else if (option.type === 'accessories' && option.name) {
                if (!data.accessories.find(a => a.id === option.id)) {
                  data.accessories.push({
                    id: option.id,
                    name: option.name,
                    subname: option.subname || '',
                    price: parseInt(option.price) || 0,
                    category: option.data ? JSON.parse(option.data).subType : ''
                  });
                }
              }
            } catch (e) {
              // 忽略解析错误
            }
          });

          return data;
        });

        // 提取媒体资源（配置器预览图等）
        const mediaData = await page.evaluate(() => {
          const media = {
            configuratorImages: [],
            heroImages: []
          };

          // 提取配置器主预览图
          document.querySelectorAll('.configurator-preview img, .vehicle-preview img, .hero-image img').forEach(img => {
            if (img.src && !img.src.includes('data:image')) {
              media.configuratorImages.push({
                url: img.src,
                alt: img.alt || ''
              });
            }
          });

          // 提取背景图（通常是车辆展示图）
          document.querySelectorAll('[style*="background-image"]').forEach(el => {
            const style = el.getAttribute('style') || '';
            const urlMatch = style.match(/url\(['"]?([^'")]+)['"]?\)/i);
            if (urlMatch && !urlMatch[1].includes('data:image')) {
              media.heroImages.push({
                url: urlMatch[1],
                description: el.getAttribute('aria-label') || el.getAttribute('title') || ''
              });
            }
          });

          return media;
        });

        // 处理每个版本的详细数据
        console.log(`  版本数量: ${configData.variants.length}`);

        // 先填写 Post Code（一次性操作）
        console.log('  填写 Post Code...');
        await fillPostCode(page, '2000');

        for (const variant of configData.variants) {
          console.log(`    处理版本: ${variant.name}`);

          // 解析完整规格
          const fullSpecs = extractFullSpecs(variant.learnMoreModal);

          // 解析标准配置
          const standardFeatures = extractStandardFeatures(variant.description + ' ' + variant.learnMoreModal);

          // 组装完整版本数据
          const variantData = {
            id: variant.id,
            name: variant.name,
            basePrice: variant.price,  // 基础价格（不含颜色等额外配置）
            description: variant.description,
            fullSpecs: fullSpecs,
            standardFeatures: standardFeatures,
            // 可用配置映射（从官网 data 字段提取）
            availableConfig: variant.availableConfig,
            media: {
              images: {
                configurator: mediaData.configuratorImages.slice(0, 3),
                hero: mediaData.heroImages.slice(0, 2)
              }
            }
          };

          // 输出规格摘要
          const specSummary = [];
          if (fullSpecs.battery?.capacity) specSummary.push(`电池: ${fullSpecs.battery.capacity}`);
          if (fullSpecs.battery?.range) specSummary.push(`续航: ${fullSpecs.battery.range}`);
          if (fullSpecs.powertrain?.maxPower) specSummary.push(`功率: ${fullSpecs.powertrain.maxPower}`);
          if (fullSpecs.performance?.acceleration) specSummary.push(`加速: ${fullSpecs.performance.acceleration}`);
          if (specSummary.length > 0) {
            console.log(`      规格: ${specSummary.join(', ')}`);
          }

          // 输出配置摘要
          const featureCount = Object.values(standardFeatures).reduce((sum, arr) => sum + arr.length, 0);
          if (featureCount > 0) {
            console.log(`      配置项: ${featureCount} 项`);
          }

          modelData.variants.push(variantData);
        }

        // 爬取完整价格矩阵（版本 x 颜色 x 轮毂）
        console.log(`  爬取价格矩阵...`);
        const pricingMatrix = await scrapePricingMatrix(page, configData.variants, configData.colors, configData.wheels, configData.interiors);
        modelData.pricingMatrix = pricingMatrix;

        console.log(`  价格组合: ${pricingMatrix.summary.totalCombinations} 种`);
        console.log(`  价格范围: $${pricingMatrix.summary.priceRange.min.toLocaleString()} - $${pricingMatrix.summary.priceRange.max.toLocaleString()}`);

        // 处理颜色选项（添加图片）
        modelData.options.exteriorColors = configData.colors.map(color => ({
          id: color.id,
          name: color.name,
          price: color.price,
          images: color.images
        }));

        modelData.options.wheels = configData.wheels;
        modelData.options.interiors = configData.interiors;
        modelData.options.accessories = configData.accessories;

        // 输出摘要
        console.log(`  外观颜色: ${modelData.options.exteriorColors.length} 种`);
        console.log(`  轮毂选项: ${modelData.options.wheels.length} 种`);
        console.log(`  内饰选项: ${modelData.options.interiors.length} 种`);
        console.log(`  配件选项: ${modelData.options.accessories.length} 种`);

      } catch (e) {
        console.error(`  处理车型 ${vehicle.name} 数据失败: ${e.message}`);
        failedModels.push(vehicle.name);
      }

      allModels.push(modelData);
      await page.waitForTimeout(CLI_OPTIONS.delay);
    }

    // 保存结果
    const outputData = {
      scrapeDate: new Date().toISOString(),
      source: 'https://bydhaberfield.com.au/',
      totalModels: allModels.length,
      successCount: allModels.filter(m => m.variants.length > 0).length,
      failedModels: failedModels,
      models: allModels
    };

    const timestamp = formatLocalTimestamp();
    let modelSlug;
    if (vehiclesToProcess.length === 1) {
      // 单个车型：使用车型名称（小写、连字符）
      modelSlug = vehiclesToProcess[0].name.toLowerCase().replace(/\s+/g, '-');
    } else if (vehiclesToProcess.length === VEHICLE_URLS.length) {
      // 全部车型
      modelSlug = 'all';
    } else {
      // 部分车型
      modelSlug = `${vehiclesToProcess.length}models`;
    }
    const outputDir = path.join(process.cwd(), 'byd-output', 'json');
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    const filename = path.join(outputDir, `byd-variant-details_${modelSlug}${timestamp}.json`);
    fs.writeFileSync(filename, JSON.stringify(outputData, null, 2));
    console.log(`\n========================================`);
    console.log(`数据已保存到 ${filename}`);
    console.log(`  - 成功: ${outputData.successCount} 款`);
    console.log(`  - 失败: ${failedModels.length} 款`);

    if (failedModels.length > 0) {
      console.log(`\n失败车型列表:`);
      failedModels.forEach(name => console.log(`  - ${name}`));
      console.log(`\n重试命令: node js/scrape-byd-variant-details.js --model="<车型名>" --retries=5`);
    }

    // 输出统计信息
    let totalVariants = 0;
    let totalSpecs = 0;
    let totalFeatures = 0;
    allModels.forEach(model => {
      totalVariants += model.variants.length;
      model.variants.forEach(v => {
        if (v.fullSpecs && Object.keys(v.fullSpecs).length > 0) totalSpecs++;
        const featureCount = Object.values(v.standardFeatures || {}).reduce((sum, arr) => sum + arr.length, 0);
        if (featureCount > 0) totalFeatures++;
      });
    });
    console.log(`\n统计信息:`);
    console.log(`  - 总版本数: ${totalVariants}`);
    console.log(`  - 包含规格的版本: ${totalSpecs}`);
    console.log(`  - 包含配置的版本: ${totalFeatures}`);

    return allModels;

  } catch (error) {
    console.error('爬取失败:', error.message);
    await page.screenshot({ path: 'byd-variant-details-error.png' });
    throw error;
  } finally {
    await browser.close();
  }
}

/**
 * 处理位置选择弹窗
 */
async function handleLocationPopup(page) {
  const confirmBtn = page.locator('button:has-text("Continue")').first();
  if (await confirmBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    console.log('  处理位置选择弹窗...');
    await confirmBtn.click();
    await page.waitForTimeout(1000);
  }
}

/**
 * 填写 Post Code
 * @param {Page} page - Playwright 页面对象
 * @param {string} postCode - 邮编，默认 2000
 */
async function fillPostCode(page, postCode = '2000') {
  const postCodeInput = page.locator('input[type="number"]').first();
  if (await postCodeInput.isVisible({ timeout: 2000 }).catch(() => false)) {
    await postCodeInput.fill(postCode);
    await page.waitForTimeout(1500); // 等待 Experience Centre 加载
    return true;
  }
  return false;
}

/**
 * 选择 Experience Centre
 * @param {Page} page - Playwright 页面对象
 * @param {string} centreId - 中心 ID (如 delivery00, delivery01)
 */
async function selectExperienceCentre(page, centreId) {
  const radio = page.locator(`#${centreId}`);
  if (await radio.isVisible({ timeout: 2000 }).catch(() => false)) {
    await radio.click();
    await page.waitForTimeout(500);
    return true;
  }
  return false;
}

/**
 * 从配置器页面提取价格明细数据
 * @param {Page} page - Playwright 页面对象
 * @returns {Object} 价格明细数据
 */
async function extractPricingData(page) {
  return await page.evaluate(() => {
    const result = {
      postCode: '2000',
      registrationState: null,
      registrationType: null,
      vehicleItems: [],
      campaignIncentives: [],  // 新增：促销激励列表
      vehicleSubtotal: null,
      onRoadFees: [],
      onRoadFeesSubtotal: null,
      driveAwayPrice: null,
      dueToday: null
    };

    // 获取页面所有文本行
    const allText = document.body.innerText;
    const lines = allText.split('\n').map(l => l.trim()).filter(l => l);

    // 遍历所有行，查找价格行模式
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // 匹配价格格式 ($46,990) 或 (-$4,072.61) 或 Included
      if (line.match(/^-?\$[\d,.]+$/) || line === 'Included') {
        const prevLine = lines[i - 1];
        if (prevLine && !prevLine.match(/^-?\$[\d,.]+$/) && prevLine !== 'Included') {

          // 分类处理
          if (prevLine === 'Vehicle Subtotal') {
            result.vehicleSubtotal = line;
          } else if (prevLine === 'On Road Fees Subtotal') {
            result.onRoadFeesSubtotal = line;
          } else if (prevLine.includes('Stamp Duty')) {
            result.onRoadFees.push({ item: 'Local Stamp Duty', amount: line });
          } else if (prevLine.includes('Registration') && !prevLine.includes('State')) {
            result.onRoadFees.push({ item: 'Local Registration', amount: line });
          } else if (prevLine.includes('CTP')) {
            result.onRoadFees.push({ item: 'Local CTP', amount: line });
          } else if (prevLine.includes('Dealer Delivery')) {
            result.onRoadFees.push({ item: 'Dealer Delivery Fee', amount: line });
          } else if (prevLine.includes('Slimline') || prevLine.includes('Plate Fee')) {
            result.onRoadFees.push({ item: 'Local Slimline Plate Fee', amount: line });
          } else if (prevLine.toLowerCase().includes('campaign') ||
                     prevLine.toLowerCase().includes('incentive')) {
            // 新增：识别促销激励（Campaign Incentive）
            result.campaignIncentives.push({
              name: prevLine,
              amount: line,
              isDiscount: line.startsWith('-')
            });
          } else if (prevLine.includes('SEAL') || prevLine.includes('ATTO') ||
                     prevLine.includes('DOLPHIN') || prevLine.includes('SEALION') ||
                     prevLine.includes('SHARK') || prevLine.includes('Paint') ||
                     prevLine.includes('Wheels') || prevLine.includes('Interior')) {
            result.vehicleItems.push({ item: prevLine, amount: line });
          }
        }
      }

      // 提取 Drive Away Price
      if (i > 0 && lines[i - 1] === 'Drive Away Price' && line.match(/^\$[\d,.]+$/)) {
        result.driveAwayPrice = line;
      }

      // 提取 Due Today
      if (line.includes('Due Today') && line.match(/\$[\d,.]+/)) {
        result.dueToday = line.match(/\$[\d,.]+/)[0];
      }
    }

    // 提取 Registration State
    const stateSelect = document.querySelector('select[id*="state"], [aria-label*="State"]');
    if (stateSelect) {
      result.registrationState = stateSelect.value;
    }

    // 提取 Registration Type
    const personalRadio = document.querySelector('input[value="personal"]');
    if (personalRadio?.checked) {
      result.registrationType = 'Personal';
    } else {
      const businessRadio = document.querySelector('input[value="business"]');
      if (businessRadio?.checked) {
        result.registrationType = 'Business';
      }
    }

    return result;
  });
}

/**
 * 爬取单个版本的价格明细
 * @param {Page} page - Playwright 页面对象
 * @param {string} variantId - 版本 ID
 * @param {string} variantName - 版本名称
 */
async function scrapeVariantPricing(page, variantId, variantName) {
  console.log(`      提取价格: ${variantName}`);

  // 1. 选择该版本（如果还没选中）
  const variantRadio = page.locator(`input[value="${variantId}"]`);
  const isChecked = await variantRadio.isChecked().catch(() => false);

  if (!isChecked) {
    // 点击 label 而不是 radio，避免被拦截
    const variantLabel = page.locator(`label[for="${await variantRadio.getAttribute('id')}"]`);
    if (await variantLabel.isVisible({ timeout: 2000 }).catch(() => false)) {
      await variantLabel.click({ force: true });
      await page.waitForTimeout(1000);
    }
  } else {
    // 已选中，只需等待价格更新
    await page.waitForTimeout(500);
  }

  // 2. 填写 Post Code（如果还没填写）
  await fillPostCode(page, '2000');
  await page.waitForTimeout(1000);

  // 3. 提取价格数据
  const pricing = await extractPricingData(page);

  return pricing;
}

/**
 * 遍历所有版本提取价格明细
 * @param {Page} page - Playwright 页面对象
 * @param {Array} variants - 版本列表
 */
async function scrapeAllVariantPrices(page, variants) {
  const allPricing = [];

  for (const variant of variants) {
    const pricing = await scrapeVariantPricing(page, variant.id, variant.name);
    allPricing.push({
      variantId: variant.id,
      variantName: variant.name,
      pricing: pricing
    });
  }

  return allPricing;
}

// 执行爬取
scrapeVariantDetails()
  .then(models => {
    console.log(`\n爬取完成! 共获取 ${models.length} 款车型详细信息`);
  })
  .catch(err => {
    console.error('错误:', err);
    process.exit(1);
  });
