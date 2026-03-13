#!/usr/bin/env node

/**
 * 从爬取的 JSON 数据生成 INSERT SQL 语句
 *
 * 用法: node scripts/generate_sql.mjs [json文件路径]
 * 默认使用: byd-variant-details-2026-03-05T09-59-30.json
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 配置 - 输出到用户工作目录
const WORK_DIR = process.cwd();
const CONFIG = {
    inputDir: path.join(WORK_DIR, 'byd-output', 'json'),
    outputDir: path.join(WORK_DIR, 'byd-output', 'sql'),
    defaultInputFile: null,  // 移除硬编码默认值，使用命令行参数或查找最新文件
};

/**
 * 生成带车型标识和本地时间戳的输出文件名
 * @param {string} inputFileName - 输入的 JSON 文件名
 * @returns {string} 格式: insert_statements_{车型标识}_YYYY-MM-DD_HH-MM-SS.sql
 */
function generateOutputFileName(inputFileName) {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const timestamp = `${year}-${month}-${day}_${hours}-${minutes}-${seconds}`;

    // 从输入文件名提取车型标识
    // byd-variant-details_atto-3_2026-03-13_*.json → atto-3
    // byd-variant-details_2models_*.json → 2models
    // byd-variant-details_all_*.json → all
    let modelInfo = inputFileName
        .replace('.json', '')
        .replace('byd-variant-details_', '');

    // 移除末尾的时间戳部分（格式：YYYY-MM-DD_HH-MM-SS 或 YYYY-MM-DDTHH-MM-SS）
    modelInfo = modelInfo.replace(/[-_]?\d{4}-\d{2}-\d{2}[_T]\d{2}[-:]\d{2}[-:]\d{2}$/, '');

    return `insert_statements_${modelInfo}_${timestamp}.sql`;
}

/**
 * 从 URL 推断品牌
 */
function inferBrandFromUrl(url) {
    if (!url) return 'Unknown';
    const urlLower = url.toLowerCase();
    if (urlLower.includes('byd')) return 'BYD';
    if (urlLower.includes('tesla')) return 'Tesla';
    if (urlLower.includes('toyota')) return 'Toyota';
    if (urlLower.includes('bmw')) return 'BMW';
    if (urlLower.includes('mercedes') || urlLower.includes('benz')) return 'Mercedes-Benz';
    if (urlLower.includes('audi')) return 'Audi';
    return 'Unknown';
}

/**
 * 转义 SQL 字符串值
 */
function escapeSqlString(str) {
    if (str === null || str === undefined) return 'NULL';
    if (typeof str !== 'string') return str;
    // 先转义反斜杠，再转义单引号（顺序很重要）
    return str.replace(/\\/g, '\\\\').replace(/'/g, "''");
}

/**
 * 将值转换为 SQL 字符串格式
 */
function toSqlValue(value) {
    if (value === null || value === undefined) return 'NULL';
    if (typeof value === 'number') return value.toString();
    if (typeof value === 'boolean') return value ? '1' : '0';
    if (typeof value === 'object') return `'${escapeSqlString(JSON.stringify(value))}'`;
    return `'${escapeSqlString(value)}'`;
}

/**
 * 格式化日期为 MySQL 格式
 */
function formatDateTime(isoDate) {
    if (!isoDate) return 'NULL';
    try {
        const date = new Date(isoDate);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        return `'${year}-${month}-${day} ${hours}:${minutes}:${seconds}'`;
    } catch {
        return 'NULL';
    }
}

/**
 * 生成 loan_vehicle_configs 表的 INSERT 语句
 */
function generateConfigInsert(model, rootData, configId, sourceFileName) {
    const fields = [
        'id',
        'brand', 'model_name', 'model_type', 'body_type', 'seats',
        'build_price_url', 'model_image', 'variants', 'colors', 'wheels',
        'interiors', 'accessories', 'scrape_date',
        'price_combinations_count', 'price_range_min', 'price_range_max',
        'has_campaign_incentive', 'campaign_incentive_count',
        'source_file', 'created_at'
    ];

    const options = model.options || {};
    const pricingMatrix = model.pricingMatrix || {};

    const values = [
        configId,
        toSqlValue(inferBrandFromUrl(rootData.source)),
        toSqlValue(model.modelName),
        toSqlValue(model.modelType),
        toSqlValue(model.bodyType),
        toSqlValue(model.seats),
        toSqlValue(model.buildPriceUrl),
        toSqlValue(null),
        toSqlValue(model.variants),
        toSqlValue(options.exteriorColors),
        toSqlValue(options.wheels),
        toSqlValue(options.interiors),
        toSqlValue(options.accessories),
        formatDateTime(rootData.scrapeDate),
        toSqlValue(pricingMatrix.summary?.totalCombinations ?? 0),
        toSqlValue(pricingMatrix.summary?.priceRange?.min ?? 0),
        toSqlValue(pricingMatrix.summary?.priceRange?.max ?? 0),
        toSqlValue(pricingMatrix.summary?.hasCampaignIncentive ?? false),
        toSqlValue(pricingMatrix.summary?.campaignIncentiveCount ?? 0),
        toSqlValue(sourceFileName),
        'NOW()'
    ];

    return `INSERT INTO loan_vehicle_configs (${fields.join(', ')})\nVALUES (${values.join(', ')});`;
}

/**
 * 生成 loan_vehicle_prices 表的 INSERT 语句
 */
function generatePricesInsert(combinations, configId) {
    if (!combinations || combinations.length === 0) {
        return '-- 无价格组合数据';
    }

    const fields = [
        'config_id', 'variant_data_id', 'variant_name', 'variant_price',
        'color_data_id', 'color_name', 'color_price',
        'wheel_data_id', 'wheel_name', 'wheel_price',
        'interior_data_id', 'interior_name', 'interior_price',
        'vehicle_subtotal', 'stamp_duty', 'registration', 'ctp',
        'dealer_delivery', 'slimline_plate', 'on_road_fees_subtotal',
        'campaign_incentive_name', 'campaign_incentive', 'campaign_incentive_str',
        'drive_away_price',
        'vehicle_subtotal_str', 'stamp_duty_str', 'registration_str',
        'ctp_str', 'dealer_delivery_str', 'slimline_plate_str', 'drive_away_price_str',
        'images', 'created_at'
    ];

    const valuesRows = combinations.map((combo) => {
        const values = [
            configId,
            toSqlValue(combo.variantId),
            toSqlValue(combo.variantName),
            toSqlValue(combo.variantPrice),
            toSqlValue(combo.colorId),
            toSqlValue(combo.colorName),
            toSqlValue(combo.colorPrice),
            toSqlValue(combo.wheelId),
            toSqlValue(combo.wheelName),
            toSqlValue(combo.wheelPrice),
            toSqlValue(combo.interiorId),
            toSqlValue(combo.interiorName),
            toSqlValue(combo.interiorPrice),
            toSqlValue(combo.vehicleSubtotal),
            toSqlValue(combo.stampDuty),
            toSqlValue(combo.registration),
            toSqlValue(combo.ctp),
            toSqlValue(combo.dealerDelivery),
            toSqlValue(combo.slimlinePlate),
            toSqlValue(combo.onRoadFeesSubtotal),
            toSqlValue(combo.campaignIncentiveName || null),
            toSqlValue(combo.campaignIncentive || 0),
            toSqlValue(combo.campaignIncentiveStr || null),
            toSqlValue(combo.driveAwayPrice),
            toSqlValue(combo.vehicleSubtotalStr),
            toSqlValue(combo.stampDutyStr),
            toSqlValue(combo.registrationStr),
            toSqlValue(combo.ctpStr),
            toSqlValue(combo.dealerDeliveryStr),
            toSqlValue(combo.slimlinePlateStr),
            toSqlValue(combo.driveAwayPriceStr),
            toSqlValue(combo.images),
            'NOW()'
        ];
        return `(${values.join(', ')})`;
    });

    return `INSERT INTO loan_vehicle_prices (${fields.join(', ')})\nVALUES\n${valuesRows.join(',\n')};`;
}

/**
 * 主函数
 */
function main() {
    const inputFileName = process.argv[2] || CONFIG.defaultInputFile;
    const inputPath = path.join(CONFIG.inputDir, inputFileName);

    console.log(`读取文件: ${inputPath}`);

    let data;
    try {
        const rawContent = fs.readFileSync(inputPath, 'utf-8');
        data = JSON.parse(rawContent);
    } catch (error) {
        console.error(`读取或解析 JSON 文件失败: ${error.message}`);
        process.exit(1);
    }

    if (!data.models || !Array.isArray(data.models)) {
        console.error('无效的数据结构: 缺少 models 数组');
        process.exit(1);
    }

    console.log(`成功加载 ${data.totalModels} 个模型`);
    console.log(`爬取日期: ${data.scrapeDate}`);
    console.log(`数据源: ${data.source}`);

    const sqlStatements = [];
    let totalCombinations = 0;

    data.models.forEach((model, modelIndex) => {
        const configId = modelIndex + 1;
        const options = model.options || {};
        const pricingMatrix = model.pricingMatrix || {};
        const combinations = pricingMatrix.combinations || [];

        console.log(`\n处理模型: ${model.modelName}`);
        console.log(`   - 变体数量: ${model.variants?.length || 0}`);
        console.log(`   - 颜色数量: ${options.exteriorColors?.length || 0}`);
        console.log(`   - 轮毂数量: ${options.wheels?.length || 0}`);
        console.log(`   - 内饰数量: ${options.interiors?.length || 0}`);
        console.log(`   - 价格组合: ${combinations?.length || 0}`);

        sqlStatements.push(`\n-- ============================================`);
        sqlStatements.push(`-- Model: ${model.modelName} (${inferBrandFromUrl(data.source)})`);
        sqlStatements.push(`-- 爬取日期: ${data.scrapeDate}`);
        sqlStatements.push(`-- ============================================`);

        sqlStatements.push(generateConfigInsert(model, data, configId, inputFileName));

        if (combinations && combinations.length > 0) {
            sqlStatements.push(generatePricesInsert(combinations, configId));
            totalCombinations += combinations.length;
        }
    });

    const header = `-- ================================================
-- 车辆配置与价格 INSERT SQL 语句
-- 生成时间: ${new Date().toISOString()}
-- 数据源: ${data.source}
-- 模型数量: ${data.totalModels}
-- 价格组合总数: ${totalCombinations}
-- ================================================

START TRANSACTION;

`;

    const footer = '\n\nCOMMIT;\n';

    const outputFileName = generateOutputFileName(inputFileName);
    const outputPath = path.join(CONFIG.outputDir, outputFileName);
    const fullContent = header + sqlStatements.join('\n') + footer;

    // 确保输出目录存在
    if (!fs.existsSync(CONFIG.outputDir)) {
        fs.mkdirSync(CONFIG.outputDir, { recursive: true });
    }

    fs.writeFileSync(outputPath, fullContent, 'utf-8');

    console.log(`\nSQL 语句生成完成!`);
    console.log(`输出文件: ${outputPath}`);
    console.log(`统计:`);
    console.log(`   - 配置记录: ${data.totalModels} 条`);
    console.log(`   - 价格记录: ${totalCombinations} 条`);
}

// 执行主函数
main();
