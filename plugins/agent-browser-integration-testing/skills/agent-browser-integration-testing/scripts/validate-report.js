#!/usr/bin/env node

const fs = require("fs");

const reportPath = process.argv[2];
if (!reportPath) {
    console.error("Usage: node scripts/validate-report.js <report-path>");
    process.exit(2);
}

let content;
try {
    content = fs.readFileSync(reportPath, "utf8");
} catch (err) {
    console.error(`Failed to read report: ${err.message}`);
    process.exit(2);
}

const errors = [];

function requireMatch(pattern, message) {
    if (!pattern.test(content)) {
        errors.push(message);
    }
}

function requireInOrder(headers) {
    let idx = -1;
    for (const h of headers) {
        const next = content.indexOf(h);
        if (next === -1) {
            errors.push(`Missing section: ${h}`);
            return;
        }
        if (next <= idx) {
            errors.push(`Section order incorrect: ${h}`);
            return;
        }
        idx = next;
    }
}

function getSection(startHeader, endHeader) {
    const start = content.indexOf(startHeader);
    if (start === -1) {
        return null;
    }
    const end = endHeader ? content.indexOf(endHeader, start + startHeader.length) : -1;
    if (end === -1) {
        return content.slice(start);
    }
    return content.slice(start, end);
}

// Header fields
requireMatch(/^\*\*用户原始需求\*\*：\S/m, "Missing or empty: 用户原始需求");
requireMatch(/^\*\*目标 URL\*\*：\S/m, "Missing or empty: 目标 URL");
requireMatch(/^\*\*日期与时间\*\*：\S/m, "Missing or empty: 日期与时间");
requireMatch(/^\*\*总体状态\*\*：\s*(PASS|FAIL|WARN)\b/m, "Missing or invalid: 总体状态");
requireMatch(/^\*\*总耗时\*\*：\S/m, "Missing or empty: 总耗时");

// Section order
requireInOrder([
    "### 1. 测试摘要",
    "### 2. 关键发现",
    "### 3. 执行日志",
    "### 4. 网络交互审计",
    "#### 4.1 后端API接口调用概览",
    "#### 4.2 异常/关键接口详情",
    "#### 4.3 前端资源加载记录",
    "### 5. 举证",
    "### 6. 建议",
]);

// Execution log table must include open and a last step
requireMatch(/\|\s*步骤\s*\|\s*命令\s*\|\s*目标 \/ Ref\s*\|\s*状态\s*\|\s*耗时 \(秒\)\s*\|\s*详情 \/ 错误信息\s*\|/m, "Missing Execution Log table header");
requireMatch(/\|\s*\d+\s*\|\s*open\s*\|/m, "Execution Log must include open step");
const executionSection = getSection("### 3. 执行日志", "### 4. 网络交互审计");
if (executionSection) {
    const rowRegex = /^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|/gm;
    const rows = [];
    let match;
    while ((match = rowRegex.exec(executionSection)) !== null) {
        const step = match[1].trim();
        const command = match[2].trim();
        if (step !== "步骤") {
            rows.push({step, command});
        }
    }
    if (rows.length < 2) {
        errors.push("Execution Log must include at least two steps");
    } else {
        const last = rows[rows.length - 1];
        if (!last.command || last.command.includes("<<FILL")) {
            errors.push("Execution Log last step must be filled with a real command");
        }
    }
}

// Final page title and URL must be filled
requireMatch(/^- \*\*最终页面标题\*\*：\S/m, "Missing or empty: 最终页面标题");
requireMatch(/^- \*\*最终 URL\*\*：\S/m, "Missing or empty: 最终 URL");

// Placeholder check
if (content.includes("<<FILL:")) {
    errors.push("Report still contains <<FILL: ...>> placeholders");
}

// Evidence images and captions
const evidenceSection = getSection("### 5. 举证", "### 6. 建议");
if (!evidenceSection) {
    errors.push("Missing Evidence section");
} else {
    const imageMatches = evidenceSection.match(/!\[[^\]]*\]\([^\)]+\)/g);
    if (!imageMatches || imageMatches.length === 0) {
        errors.push("Evidence section must include at least one embedded image via ![alt](path)");
    } else {
        const captionMatches = evidenceSection.match(/\*图\d+：.+\*/g);
        if (!captionMatches || captionMatches.length < imageMatches.length) {
            errors.push("Each evidence image must have a caption like *图X：...*");
        }
    }
}

// Network section validations
const networkOverview = getSection("#### 4.1 后端API接口调用概览", "#### 4.2 异常/关键接口详情");
const networkDetails = getSection("#### 4.2 异常/关键接口详情", "#### 4.3 前端资源加载记录");
if (networkOverview) {
    const rowRegex = /^\|\s*([A-Z]+)\s*\|\s*([^|]+?)\s*\|\s*([0-9]{3})\s*\|/gm;
    const non2xx = [];
    let match;
    while ((match = rowRegex.exec(networkOverview)) !== null) {
        const method = match[1].trim();
        const path = match[2].trim();
        const status = match[3].trim();
        if (!/^2\d\d$/.test(status)) {
            non2xx.push({method, path, status});
        }
    }

    if (non2xx.length > 0) {
        if (!networkDetails) {
            errors.push("Missing 4.2 details section for non-2xx APIs");
        } else {
            for (const item of non2xx) {
                const methodPath = `${item.method} ${item.path}`;
                if (!networkDetails.includes(methodPath) || !networkDetails.includes(item.status)) {
                    errors.push(`4.2 must include details for non-2xx API: ${methodPath} (${item.status})`);
                }
            }
        }
    }

}

// Final output
if (errors.length > 0) {
    console.error("REPORT VALIDATION FAILED");
    for (const err of errors) {
        console.error(`- ${err}`);
    }
    process.exit(1);
}

console.log("REPORT VALIDATION PASSED");
