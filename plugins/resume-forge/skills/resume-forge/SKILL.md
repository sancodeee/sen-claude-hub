---
name: resume-forge
description: Use when a user asks to write, tailor, review, or revise a truthful Chinese resume from real experience, achievements, existing resume materials, or a target job description.
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash
---

# ResumeForge 简历工坊

## Overview

根据用户提供的真实材料撰写中文简历内容，并可按目标职位 JD 定制；使用既定简历结构组织内容并核查事实一致性。

## Scope

- 只基于用户确认的真实经历、能力与成果写作；信息不足时先请求补充，不编造。
- 不生成 HTML、PDF，不处理照片。
