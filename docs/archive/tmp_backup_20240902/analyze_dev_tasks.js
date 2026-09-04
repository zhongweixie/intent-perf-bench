export const meta = {
  name: 'analyze-dev-tasks',
  description: '系统性分析所有 21 个 IPB dev 任务的 AI 相关性',
  phases: [
    { title: 'Scan', detail: '读取所有 dev 任务的描述和代码结构' },
    { title: 'Classify', detail: '判断每个任务与 AI/ML 的相关度' },
    { title: 'Recommend', detail: '汇总保留/淘汰建议' },
  ],
}

const DEV_TASKS = [
  'ipb_dev_001', 'ipb_dev_002', 'ipb_dev_003', 'ipb_dev_004', 'ipb_dev_005',
  'ipb_dev_006', 'ipb_dev_007', 'ipb_dev_008', 'ipb_dev_009', 'ipb_dev_010',
  'ipb_dev_011', 'ipb_dev_012', 'ipb_dev_013', 'ipb_dev_014',
  'ipb_dev_026', 'ipb_dev_027', 'ipb_dev_031',
  'ipb_dev_033', 'ipb_dev_034', 'ipb_dev_035', 'ipb_dev_036',
  'ipb_dev_037', 'ipb_dev_038', 'ipb_dev_039', 'ipb_dev_040', 'ipb_dev_041'
]

const BASE_DIR = '/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks'

// Schema for task analysis
const TASK_ANALYSIS_SCHEMA = {
  type: 'object',
  required: ['task_id', 'title', 'category', 'ai_relevance', 'reasoning', 'recommendation'],
  properties: {
    task_id: { type: 'string' },
    title: { type: 'string' },
    category: {
      type: 'string',
      enum: ['ml-pipeline', 'data-processing', 'business-logic', 'text-processing', 'unknown']
    },
    ai_relevance: {
      type: 'string',
      enum: ['high', 'medium', 'low', 'none']
    },
    key_operations: {
      type: 'array',
      items: { type: 'string' }
    },
    has_ml_keywords: { type: 'boolean' },
    reasoning: { type: 'string' },
    recommendation: {
      type: 'string',
      enum: ['keep', 'maybe', 'drop']
    }
  }
}

phase('Scan')

// Phase 1: Scan all dev tasks in parallel
log('扫描所有 21 个 dev 任务的内容...')

const scanResults = await pipeline(
  DEV_TASKS,

  // Stage 1: 读取任务基本信息
  async (taskId) => {
    const prompt = `查看 IPB 任务 ${taskId} 的内容并分析其 AI 相关性。

任务路径: ${BASE_DIR}/${taskId}/

请执行以下步骤:

1. 检查任务描述文件:
   - variants/fuzzy.md (如果存在)
   - workspace/README.md (如果存在)
   - task_config.json (如果存在，在 ${taskId}/ 目录下)

2. 查看代码结构:
   - 列出 workspace/ 下的主要 Python 模块
   - 读取 1-2 个核心模块的前 50 行代码

3. 搜索 ML/AI 关键词:
   - 在代码中搜索: sklearn, torch, tensorflow, keras, model, predict, train, feature, embedding, neural
   - 检查是否有: 特征工程、模型推理、向量化计算

4. 判断任务类型:
   - ML Pipeline (特征工程、模型推理、数据增强等)
   - Data Processing (通用 ETL、报表、聚合等)
   - Business Logic (业务规则、风控、推荐等)
   - Text Processing (NLP、文本分析等)

5. 给出 AI 相关度评级:
   - high: 直接涉及 ML 模型训练/推理、特征工程
   - medium: ML 应用场景但主要是数据处理优化
   - low: 可能用于 ML 但不是核心
   - none: 纯业务逻辑/通用数据处理

请以结构化格式返回分析结果。`

    return await agent(prompt, {
      label: `分析 ${taskId}`,
      phase: 'Scan',
      schema: TASK_ANALYSIS_SCHEMA
    })
  }
)

phase('Classify')

log('根据扫描结果进行分类...')

// Phase 2: 汇总分类
const classification = await agent(`
基于以下 ${scanResults.filter(Boolean).length} 个任务的分析结果，进行分类汇总:

${JSON.stringify(scanResults.filter(Boolean), null, 2)}

请按以下维度分类:

1. **必须保留** (AI 相关度 high):
   - 直接涉及 ML 特征工程、模型推理
   - 数据预处理 pipeline 优化（如用于训练的数据加载）
   - 向量化计算优化

2. **可以保留** (AI 相关度 medium):
   - ML 应用场景但主要优化通用算法
   - 可以合理包装为 AI pipeline 的一部分
   - 有一定区分度且不完全是业务逻辑

3. **建议淘汰** (AI 相关度 low/none):
   - 纯业务报表、ETL
   - 通用数据聚合、格式化
   - 无法包装为 AI 场景

对于每个分类，列出任务 ID、简短理由、以及是否有高区分度数据支持。

返回结构化的分类结果。
`, {
  phase: 'Classify',
  schema: {
    type: 'object',
    required: ['must_keep', 'maybe_keep', 'should_drop', 'summary'],
    properties: {
      must_keep: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            task_id: { type: 'string' },
            reason: { type: 'string' },
            discrimination: { type: 'string' }
          }
        }
      },
      maybe_keep: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            task_id: { type: 'string' },
            reason: { type: 'string' }
          }
        }
      },
      should_drop: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            task_id: { type: 'string' },
            reason: { type: 'string' }
          }
        }
      },
      summary: { type: 'string' }
    }
  }
})

phase('Recommend')

log('生成最终推荐...')

// Phase 3: 生成最终推荐报告
const finalReport = await agent(`
基于以下信息生成最终的 dev 任务保留/淘汰建议:

**分类结果**:
${JSON.stringify(classification, null, 2)}

**性能数据参考** (从之前的分析报告):
- 高区分度任务: ipb_dev_037 (opus-5 提升 5x), ipb_dev_003/004/005 (haiku 优势明显)
- 多数 dev 任务 <1ms，适合快速评测
- Haiku-4.5 vs Opus-5 在 dev 任务上有显著差异

**用户要求**:
1. 保留区分度最高的 3 个 CPU 任务（包括密码学任务，因为与 kernel 优化相关）
2. Dev 任务需要判断 AI 相关性
3. 最终目标: AI for AI Benchmark - Compute 轨道

请生成最终报告，包括:

1. **推荐保留的 dev 任务** (3-8 个):
   - 列出任务 ID、AI 相关性、区分度数据
   - 如何在 "AI for AI - Compute" 叙事中包装

2. **推荐淘汰的 dev 任务**:
   - 淘汰原因

3. **最终任务集组成**:
   - CPU 任务: 3 个（保留 AES/SHA256/VLIW 因为用户要求）
   - CUDA 任务: 6-8 个（之前已分析）
   - Dev 任务: 3-8 个（本次推荐）
   - **总计**: 12-19 个任务

4. **AI for AI 叙事整合**:
   - 如何将保留的任务整合到统一的 benchmark 叙事中
   - 分层设计（核心层/扩展层/基础层）

返回完整的 Markdown 报告。
`, {
  phase: 'Recommend',
  model: 'opus'
})

log('✅ 分析完成')

return {
  scan_results: scanResults.filter(Boolean),
  classification,
  final_report: finalReport
}
