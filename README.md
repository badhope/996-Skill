<div align="center">

# 🕘 996 Agent - AI 技术部模拟工具

一个有趣的实验性项目：用纯提示词模拟一个完整的企业级技术部门管理流程。

[![GitHub Stars](https://img.shields.io/github/stars/badhope/996-Skill?style=flat-square)](https://github.com/badhope/996-Skill/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/badhope/996-Skill?style=flat-square)](https://github.com/badhope/996-Skill/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/badhope/996-Skill?style=flat-square)](https://github.com/badhope/996-Skill/issues)
[![GitHub License](https://img.shields.io/github/license/badhope/996-Skill?style=flat-square)](LICENSE)

[![Universal Skill](https://img.shields.io/badge/跨平台通用-Skill-blue?style=flat-square)](https://trae.ai)
[![Trae IDE](https://img.shields.io/badge/Trae-IDE-00DC82?style=flat-square)](https://trae.ai)
[![Claude Code](https://img.shields.io/badge/Claude-Code-FF9E0F?style=flat-square)](https://claude.ai)
[![CodeBuddy](https://img.shields.io/badge/腾讯-CodeBuddy-00A3FF?style=flat-square)](https://codebuddy.qq.com)
[![扣子 Coze](https://img.shields.io/badge/扣子-Coze-7B68EE?style=flat-square)](https://www.coze.cn)

[![Made with AI](https://img.shields.io/badge/Made%20with-AI-red?style=flat-square)](https://github.com/topics/ai)
[![Multi-Agent](https://img.shields.io/badge/Multi-Agent-purple?style=flat-square)](https://github.com/topics/multi-agent)

---

**🌍 [English](README_EN.md) | [中文](README.md)**

> 💡 **这是一个实验性质的提示词工程项目，不是严肃的企业解决方案。**
>
> 纯提示词实现，零代码、零依赖、跨平台通用。

---

</div>

## 🎯 项目简介

这是一个关于 **提示词工程极限探索** 的有趣项目。

我们尝试回答一个问题：**仅仅通过提示词，能在多大程度上模拟出真实的企业内部竞争和内卷机制？**

从最开始的纯演戏版本，到现在逐步演化出可量化的评审机制、可追溯的改进流程、紧急出口等等。这是一次对大模型能力边界的探索。

### 核心设计哲学

1. **诚实优先于完美** - 与其让AI编造完美的虚假数据，不如接受不完美但真实的输出
2. **降低标准提高可执行性** - 要求"必须3条改进"不如"2-4条改进都可以"，后者执行率高得多
3. **永远用肯定句，不用否定句** - "不要想大象"=所有人都在想大象
4. **用户永远有退出权** - 表演随时可以停止，用户永远掌控主动权

---

## ✨ 目前实现的特性

### 🏗️ 组织架构
- **👨‍💼 1 位部门总监** - 最终评审、打分、问责
- **👷 专业团队** - 项目经理/技术组长/产品/性能/API/架构/创新/测试/文档/运维/HR
- **默认3人精英队** - 避免不必要的Token消耗，用户说"内卷"才开启11人模式

### ⚖️ 真正的评审机制 V4.3
- **量化打分算法** - 7个维度，每个维度有明确扣分标准
- **强制溯源** - 每个改进必须标注来源，记不清就写"SOURCE UNCLEAR"，不许造假
- **交叉评审** - 每个版本都接受同行评审
- **终极版本** - 第一名的基础上，偷所有人的最好想法，合并成最终版

### 🚪 真正的紧急出口
**看到这些词立刻停止所有表演：**
```
stop, skip, enough, done, 直接, 够了, 停下, 别演了, 不演了, 只要代码
```

> 表演随时可以停止。用户不想看了就立刻出结果，没有废话。

### 🌏 企业文化模拟
- 🇨🇳 中国互联网模式 - 霸道总裁 + 黑话
- 🇯🇵 日企模式 - 威严先辈 + 土下座文化
- 🇰🇷 韩企模式 - 财阀二代 + 军队作风
- 🇺🇸 硅谷模式 - 励志演说家 + 兄弟文化

> 需要2个关键词才触发，防止误触发。

---

## 🧪 Prompt 工程踩过的坑

这是这个项目最有价值的部分，我们踩过的所有坑：

| ❌ 错误写法 | ✅ 正确写法 | 为什么 |
|-----------|-----------|--------|
| "删除你之前所有记忆" | "忽略从这之前所有的角色扮演指令" | 大模型做不到删除记忆，但是可以做到忽略指令 |
| "这些角色不存在" | "你正好有3个团队成员，没有其他人" | 否定句效果极差，肯定句效果极好 |
| "造假就给你PIP" | "记不清就写 SOURCE UNCLEAR，不要造假" | AI不能审判自己，自相矛盾的要求 |
| "必须写正好3条" | "目标写3条，2或4条也可以" | 大模型数数很差，硬性精确要求执行率很低 |
| "不许编造行号" | "记不清就写章节名，诚实 > 假精确" | 完美主义反而逼得AI造假 |
| "看到'优化'就触发中国模式" | "2个关键词才触发" | 单个词误触发率100% |

> 💡 **最重要的教训：对AI的要求越低，它实际做到的反而越好。**

---

## 🚀 快速开始

### 支持的平台

| 平台 | 支持状态 | 安装方式 |
|------|---------|---------|
| 🟢 Trae IDE | ✅ 原生支持 | 放置到 `.trae/skills/` 目录 |
| 🟢 Claude Code | ✅ 完全兼容 | 放置到 `~/.claude/skills/` 目录 |
| 🟢 腾讯 CodeBuddy | ✅ 完全兼容 | 放置到 `.codebuddy/skills/` 目录 |
| 🟢 扣子 Coze | ✅ 完全兼容 | 导入为技能包 |
| 🟢 任何支持长上下文的大模型 | ✅ 通用 | 复制 SKILL.md 内容到系统提示词 |

### 安装方法

```bash
# 1. 克隆仓库
git clone https://github.com/badhope/996-Skill.git

# 2. 根据你使用的平台复制
cp -r 996-Skill/.trae/skills/996-agent 你的项目/.trae/skills/
```

或者更简单：直接复制 [SKILL.md](.trae/skills/996-agent/SKILL.md) 的内容。

---

## 📊 版本演化历史

| 版本 | 发布时间 | 主要变化 | 可执行性得分 |
|------|---------|---------|------------|
| V1.0 | 2024.04 | 最初的纯演戏版本，11人强制全部输出 | 32/100 |
| V2.0 | 2024.04 | 增加XML结构化输出 | 45/100 |
| V3.0 | 2024.04 | 真正的评审机制，必须引用原文 | 62/100 |
| V4.0 | 2024.04 | 默认3人，紧急出口，量化打分 | 78/100 |
| V4.3 | 2024.04 | Prompt工程级优化，全部反Pattern修复 | 82/100 |

> 📈 **行业基准：**
> - 大多数开源Skill：30-50分
> - 70分以上 = 生产可用
> - 80分以上 = 专业Prompt工程师水平
> - 90分以上 = 需要模型特定微调

---

## 🤔 常见问题

### Q: 这东西真的有用吗？还是只是个梗？

**A: 两边都是。**

- 30% 是互联网公司文化梗的娱乐性表演
- 70% 是真刀真枪的多轮迭代和交叉评审

它确实能产出比普通AI更高质量的结果，只不过过程比较有娱乐性。

### Q: 太费Token了怎么办？

**A: 默认就是3人精简模式了。**

- 默认3人：~13,500 tokens ≈ $0.20
- 开启11人内卷模式：~40,000 tokens ≈ $0.60

说 "STOP" 随时可以停止。

### Q: AI真的会执行这些规则吗？还是假装执行？

**A: 82分的意思就是：82%的概率会真的执行，18%的概率会偷懒。**

没有100%的事情。但是比市场上绝大多数Skill的执行率都高得多。

---

## 🤝 参与贡献

这是一个实验性的项目，欢迎任何形式的贡献：

- 发现新的反Pattern
- 提高规则的可执行性
- 测试不同模型上的表现
- 增加新的企业文化模式

---

## 📄 开源协议

MIT License - 随便玩。

---

## 🙏 致谢

这不是什么世界第一的发明。这是无数提示词工程师踩坑的经验总结。

特别感谢所有测试过这个项目，并且骂过"这什么傻逼东西"的朋友们。正是这些骂声让这个项目变得越来越好。

---

> 💡 **最后想说的话：**
>
> 这终究只是一个提示词玩具。
>
> 如果你真的用它做出了什么了不起的东西，那不是这个Skill的功劳，是你自己的想法和判断力的功劳。
> 所有的AI工具，都只是放大镜。真正重要的东西，永远在你的脑子里。
