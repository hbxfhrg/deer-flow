# 自由式对练流程 - Java 方法调用示例文档

## 一、核心流程概述

自由式对练系统包含三个核心 API 调用，构成完整的对话流程：

| 步骤 | API 方法 | 功能说明 |
|:---:|----------|----------|
| 1 | `practiceStart()` | 开始对练，生成开场白 |
| 2 | `practiceTurn()` | 对话轮次，处理学员消息并生成回复 |
| 3 | `practiceEnd()` | 结束对练，生成最终报告 |

---

## 二、数据结构定义

### 2.1 请求对象

```java
/**
 * 开始对练请求
 */
public class PracticeStartRequest {
    private Integer courseId;      // 课程ID，必填
    private String userName;      // 学员姓名，必填
    
    // Getters & Setters
    public Integer getCourseId() { return courseId; }
    public void setCourseId(Integer courseId) { this.courseId = courseId; }
    public String getUserName() { return userName; }
    public void setUserName(String userName) { this.userName = userName; }
}

/**
 * 对话轮次请求
 */
public class PracticeTurnRequest {
    private Integer recordId;     // 对练记录ID，必填
    private String message;       // 学员消息内容，必填
    
    // Getters & Setters
    public Integer getRecordId() { return recordId; }
    public void setRecordId(Integer recordId) { this.recordId = recordId; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
}

/**
 * 结束对练请求
 */
public class PracticeEndRequest {
    private Integer recordId;     // 对练记录ID，必填
    
    // Getters & Setters
    public Integer getRecordId() { return recordId; }
    public void setRecordId(Integer recordId) { this.recordId = recordId; }
}
```

### 2.2 响应对象

```java
/**
 * 开始对练响应
 */
public class PracticeStartResponse {
    private Integer recordId;         // 对练记录ID
    private String customerMessage;   // AI客户开场白
    private Integer totalRounds;      // 总轮次
    
    // Getters & Setters
}

/**
 * 对话轮次响应
 */
public class PracticeTurnResponse {
    private String customerMessage;   // AI客户回复
    private Evaluation evaluation;    // 当前轮次评估结果
    private Boolean isComplete;       // 是否已完成
    private Integer round;            // 当前轮次
    
    // Getters & Setters
}

/**
 * 评估结果
 */
public class Evaluation {
    private Integer roundScore;               // 本轮得分
    private String feedback;                  // 反馈意见
    private Map<String, Integer> dimensionScores;  // 各维度得分
    
    // Getters & Setters
}

/**
 * 结束对练响应
 */
public class PracticeEndResponse {
    private Integer totalScore;       // 总得分
    private Report report;            // 最终报告
    
    // Getters & Setters
}

/**
 * 最终报告
 */
public class Report {
    private String summary;           // 综合评价
    private List<String> strengths;   // 优势列表
    private List<String> improvements;// 改进建议
    private Map<String, Integer> finalScores; // 各维度最终得分
    
    // Getters & Setters
}
```

---

## 三、完整调用示例

### 3.1 场景说明

假设场景：**智能汽车销售对练**
- 课程ID：`2`
- 考核维度：`["三电系统", "智能驾驶", "舒适性", "外观设计", "售后服务"]`（共5轮）
- 学员：`张三`

### 3.2 调用过程示例

```java
import java.util.HashMap;
import java.util.Map;

public class PracticeDemo {
    
    // 模拟 API 客户端
    private PracticeApiClient apiClient = new PracticeApiClient();
    
    public void runFullPractice() {
        System.out.println("========== 阶段1：开始对练 ==========");
        
        // 1. 构造请求
        PracticeStartRequest startReq = new PracticeStartRequest();
        startReq.setCourseId(2);           // 课程ID：智能汽车销售课程
        startReq.setUserName("张三");       // 学员姓名
        
        // 2. 调用 API
        PracticeStartResponse startResp = apiClient.practiceStart(startReq);
        
        // 3. 获取返回值
        Integer recordId = startResp.getRecordId();      // 示例返回：1001
        String aiMessage = startResp.getCustomerMessage(); // 示例返回："您好！我想了解一下你们的电动车..."
        Integer totalRounds = startResp.getTotalRounds(); // 示例返回：5（考核维度数量）
        
        System.out.println("RecordId: " + recordId);
        System.out.println("AI开场白: " + aiMessage);
        System.out.println("总轮次: " + totalRounds);
        
        // ==================== 对话轮次循环 ====================
        
        // 第1轮 - 考核维度：智能驾驶（随机排序后第一个）
        System.out.println("\n========== 阶段2：第1轮对话 ==========");
        processTurn(recordId, "我们的智能驾驶系统支持L3级别自动驾驶...", 1);
        
        // 第2轮 - 考核维度：三电系统
        System.out.println("\n========== 阶段2：第2轮对话 ==========");
        processTurn(recordId, "我们采用宁德时代的麒麟电池，续航可达800公里...", 2);
        
        // 第3轮 - 考核维度：舒适性
        System.out.println("\n========== 阶段2：第3轮对话 ==========");
        processTurn(recordId, "座椅采用Nappa真皮材质，支持零重力模式...", 3);
        
        // 第4轮 - 考核维度：外观设计
        System.out.println("\n========== 阶段2：第4轮对话 ==========");
        processTurn(recordId, "车身采用溜背设计，风阻系数仅0.22...", 4);
        
        // 第5轮 - 考核维度：售后服务
        System.out.println("\n========== 阶段2：第5轮对话 ==========");
        PracticeTurnResponse finalTurnResp = processTurn(
            recordId, 
            "我们提供终身免费保养服务，全国有500+服务网点...", 
            5
        );
        
        // 检查是否自动结束（第5轮结束后自动触发）
        if (finalTurnResp.getIsComplete()) {
            System.out.println("\n========== 阶段3：对练结束 ==========");
            PracticeEndRequest endReq = new PracticeEndRequest();
            endReq.setRecordId(recordId);
            
            PracticeEndResponse endResp = apiClient.practiceEnd(endReq);
            
            System.out.println("总得分: " + endResp.getTotalScore());
            System.out.println("综合评价: " + endResp.getReport().getSummary());
            System.out.println("优势: " + endResp.getReport().getStrengths());
            System.out.println("改进建议: " + endResp.getReport().getImprovements());
        }
    }
    
    /**
     * 处理单轮对话
     */
    private PracticeTurnResponse processTurn(Integer recordId, String userMessage, int expectedRound) {
        // 1. 构造请求
        PracticeTurnRequest turnReq = new PracticeTurnRequest();
        turnReq.setRecordId(recordId);
        turnReq.setMessage(userMessage);
        
        // 2. 调用 API
        PracticeTurnResponse turnResp = apiClient.practiceTurn(turnReq);
        
        // 3. 解析响应
        System.out.println("学员消息: " + userMessage);
        System.out.println("AI回复: " + turnResp.getCustomerMessage());
        System.out.println("当前轮次: " + turnResp.getRound() + "/" + turnResp.getTotalRounds());
        System.out.println("本轮得分: " + turnResp.getEvaluation().getRoundScore());
        System.out.println("反馈意见: " + turnResp.getEvaluation().getFeedback());
        System.out.println("维度得分: " + turnResp.getEvaluation().getDimensionScores());
        System.out.println("是否完成: " + turnResp.getIsComplete());
        
        return turnResp;
    }
}
```

---

## 四、数据流转示例

### 4.1 完整数据变化表

| 步骤 | 方法调用 | 输入参数 | 返回结果 | 数据库变化 |
|:---:|----------|----------|----------|------------|
| 1 | `practiceStart(2, "张三")` | `courseId=2, userName="张三"` | `recordId=1001, customerMessage="您好！...", totalRounds=5` | 创建 `pract_course_record` 记录 |
| 2 | `practiceTurn(1001, "L3级别自动驾驶...")` | `recordId=1001, message="L3级别..."` | `customerMessage="这么厉害？...", round=1, roundScore=85, isComplete=false` | 创建学员消息、AI回复、评估记录 |
| 3 | `practiceTurn(1001, "宁德时代电池...")` | `recordId=1001, message="宁德时代..."` | `customerMessage="续航真不错...", round=2, roundScore=90, isComplete=false` | 创建学员消息、AI回复、评估记录 |
| 4 | `practiceTurn(1001, "Nappa真皮座椅...")` | `recordId=1001, message="Nappa真皮..."` | `customerMessage="坐着肯定舒服...", round=3, roundScore=88, isComplete=false` | 创建学员消息、AI回复、评估记录 |
| 5 | `practiceTurn(1001, "溜背设计风阻...")` | `recordId=1001, message="溜背设计..."` | `customerMessage="颜值很高啊...", round=4, roundScore=92, isComplete=false` | 创建学员消息、AI回复、评估记录 |
| 6 | `practiceTurn(1001, "终身免费保养...")` | `recordId=1001, message="终身免费..."` | `customerMessage="服务真周到...", round=5, roundScore=89, isComplete=true` | 创建学员消息、AI回复、评估记录，触发结束流程 |
| 7 | `practiceEnd(1001)` | `recordId=1001` | `totalScore=444, report={"summary":"表现优秀...", ...}` | 创建 `pract_record` 记录，更新 `pract_course_record` |

### 4.2 维度顺序随机化说明

系统使用 `recordId` 作为随机种子，确保同一次对练的维度顺序一致：

```java
// 原始考核维度配置
String[] examCategories = {"三电系统", "智能驾驶", "舒适性", "外观设计", "售后服务"};

// 使用 recordId=1001 作为种子进行随机排序
// 排序后顺序示例：["智能驾驶", "三电系统", "舒适性", "外观设计", "售后服务"]

// 第1轮 → 智能驾驶
// 第2轮 → 三电系统  
// 第3轮 → 舒适性
// 第4轮 → 外观设计
// 第5轮 → 售后服务
```

### 4.3 详细变量变化演示（实例值）

#### 阶段1：开始对练

**输入参数：**
```java
courseId = 2                    // 智能汽车销售课程
userName = "张三"               // 学员姓名
```

**内部处理过程：**
```java
// 1. 查询课程信息
Course course = courseService.getById(2);
// 返回: course = {id:2, name:"智能汽车销售", sceneId:5}

// 2. 查询场景信息  
Scene scene = sceneService.getById(5);
// 返回: scene = {id:5, examCategories:"三电系统，智能驾驶，舒适性，外观设计，售后服务", dialogRoundLimit:5}

// 3. 计算总轮次
String[] categories = scene.getExamCategories().replace("，", ",").split(",");
// categories = ["三电系统", "智能驾驶", "舒适性", "外观设计", "售后服务"]
int totalRounds = categories.length;
// totalRounds = 5

// 4. 生成对练记录
CourseRecord record = new CourseRecord();
record.setCourseId(2);
record.setSceneId(5);
record.setUserName("张三");
record.setStartTime(new Date());
courseRecordService.save(record);
// recordId = 1001

// 5. LLM生成开场白
String customerMessage = llmService.generateOpening(course, scene);
// customerMessage = "您好！我想了解一下你们的电动车，最近正在考虑换车呢~"
```

**返回结果：**
```java
recordId = 1001
customerMessage = "您好！我想了解一下你们的电动车，最近正在考虑换车呢~"
totalRounds = 5
```

---

#### 阶段2：第1轮对话（考核维度：智能驾驶）

**输入参数：**
```java
recordId = 1001
message = "我们的智能驾驶系统支持L3级别自动驾驶，高速上可以自动变道超车"
```

**内部处理过程：**
```java
// 1. 查询对话历史
List<Dialog> allDialogs = dialogService.getByRecordId(1001);
// allDialogs = [{dialogId:1, speaker:2, content:"您好！我想了解..."}]

// 2. 计算当前轮次（统计学员回复数量）
int currentRound = 0;
for (Dialog d : allDialogs) {
    if (d.getSpeaker() == 1) currentRound++;
}
// currentRound = 0（之前没有学员消息）

// 3. 保存学员消息
Dialog userDialog = new Dialog();
userDialog.setRecordId(1001);
userDialog.setSpeaker(1);  // 学员
userDialog.setContent("我们的智能驾驶系统支持L3级别自动驾驶...");
dialogService.save(userDialog);
// dialogId = 2

// 4. 当前轮次+1
currentRound++;  // currentRound = 1

// 5. 获取当前考核维度（使用recordId作为随机种子）
String currentCategory = getCurrentCategory(scene, currentRound, 1001);
// currentCategory = "智能驾驶"（随机排序后的第一个维度）

// 6. LLM评估学员回答
Evaluation evaluation = llmService.evaluate(
    scene.getExamCategories(),
    scene.getScoringRules(),
    allDialogs,
    message,
    currentCategory
);
// evaluation = {
//     roundScore: 85,
//     feedback: "回答清晰，准确介绍了智能驾驶功能，但可以补充更多技术细节",
//     dimensionScores: {"智能驾驶": 85, "沟通能力": 88, "专业素养": 82}
// }

// 7. 更新学员消息的评分
dialogService.updateScore(2, 85, "回答清晰，准确介绍了智能驾驶功能...");

// 8. LLM生成客户回复
String customerReply = llmService.generateReply(
    scene, 
    allDialogs, 
    currentRound, 
    totalRounds, 
    currentCategory
);
// customerReply = "这么厉害？那在高速上行驶时，遇到突发情况系统能及时反应吗？"

// 9. 保存客户回复
Dialog aiDialog = new Dialog();
aiDialog.setRecordId(1001);
aiDialog.setSpeaker(2);  // AI客户
aiDialog.setContent("这么厉害？那在高速上行驶时...");
dialogService.save(aiDialog);
// dialogId = 3

// 10. 判断是否完成
boolean isComplete = currentRound >= totalRounds;
// isComplete = false（1 < 5）
```

**返回结果：**
```java
customerMessage = "这么厉害？那在高速上行驶时，遇到突发情况系统能及时反应吗？"
evaluation = {
    roundScore: 85,
    feedback: "回答清晰，准确介绍了智能驾驶功能，但可以补充更多技术细节",
    dimensionScores: {"智能驾驶": 85, "沟通能力": 88, "专业素养": 82}
}
round = 1
isComplete = false
```

---

#### 阶段2：第2轮对话（考核维度：三电系统）

**输入参数：**
```java
recordId = 1001
message = "我们采用宁德时代的麒麟电池，续航可达800公里，支持800V超快充"
```

**内部处理过程：**
```java
// 1. 查询对话历史
List<Dialog> allDialogs = dialogService.getByRecordId(1001);
// allDialogs = [
//     {dialogId:1, speaker:2, content:"您好！..."},
//     {dialogId:2, speaker:1, content:"我们的智能驾驶..."},
//     {dialogId:3, speaker:2, content:"这么厉害？..."}
// ]

// 2. 计算当前轮次
int currentRound = 0;
for (Dialog d : allDialogs) {
    if (d.getSpeaker() == 1) currentRound++;
}
// currentRound = 1（已有1条学员消息）

// 3. 保存学员消息（dialogId = 4）
// ...

// 4. 当前轮次+1
currentRound++;  // currentRound = 2

// 5. 获取当前考核维度
String currentCategory = getCurrentCategory(scene, currentRound, 1001);
// currentCategory = "三电系统"（随机排序后的第二个维度）

// 6. LLM评估
// evaluation = {roundScore: 90, feedback: "非常专业，参数准确...", ...}

// 7. LLM生成客户回复
// customerMessage = "续航真不错！那低温环境下续航会打折扣吗？"

// 8. 判断是否完成
// isComplete = false（2 < 5）
```

**返回结果：**
```java
customerMessage = "续航真不错！那低温环境下续航会打折扣吗？"
evaluation = {
    roundScore: 90,
    feedback: "非常专业，参数准确，回答完整",
    dimensionScores: {"三电系统": 92, "沟通能力": 88, "专业素养": 90}
}
round = 2
isComplete = false
```

---

#### 阶段2：第5轮对话（考核维度：售后服务）

**输入参数：**
```java
recordId = 1001
message = "我们提供终身免费保养服务，全国有500+服务网点，支持上门取送车"
```

**内部处理过程：**
```java
// 计算当前轮次（已有4条学员消息）
int currentRound = 4;
currentRound++;  // currentRound = 5

// 获取当前考核维度 = "售后服务"

// LLM评估
// evaluation = {roundScore: 89, ...}

// LLM生成客户回复
// customerMessage = "服务真周到！那保养都包含哪些项目呢？"

// 判断是否完成
boolean isComplete = currentRound >= totalRounds;
// isComplete = true（5 >= 5）

// 触发结束流程
Report report = llmService.generateFinalReport(allDialogs, evaluations);
int totalScore = (85 + 90 + 88 + 92 + 89) / 5;  // totalScore = 89
```

**返回结果：**
```java
customerMessage = "服务真周到！那保养都包含哪些项目呢？"
evaluation = {
    roundScore: 89,
    feedback: "售后服务介绍全面，客户关怀意识强",
    dimensionScores: {"售后服务": 90, "沟通能力": 88, "专业素养": 87}
}
round = 5
isComplete = true  // 触发自动结束
```

---

#### 阶段3：结束对练

**输入参数：**
```java
recordId = 1001
```

**内部处理过程：**
```java
// 1. 查询所有对话记录
List<Dialog> allDialogs = dialogService.getByRecordId(1001);
// 共11条记录：1条开场白 + 5组学员/AI对话

// 2. LLM生成最终报告
Report report = llmService.generateFinalReport(allDialogs, scene);
// report = {
//     summary: "整体表现优秀，专业知识扎实，沟通能力良好，建议加强技术细节的讲解",
//     strengths: ["专业知识扎实", "回答逻辑清晰", "客户需求理解到位"],
//     improvements: ["可增加更多技术参数", "可提供更多实际案例"],
//     finalScores: {"三电系统": 91, "智能驾驶": 86, "舒适性": 88, "外观设计": 92, "售后服务": 90}
// }

// 3. 计算总得分
int totalScore = calculateTotalScore(report.getFinalScores());
// totalScore = 89.4 → 四舍五入为 89

// 4. 创建练习记录
PracticeRecord practiceRecord = new PracticeRecord();
practiceRecord.setCourseId(2);
practiceRecord.setUserName("张三");
practiceRecord.setDialogRounds(5);
practiceRecord.setTotalScore(89);
practiceRecord.setReportData(report);
practiceRecord.setEndTime(new Date());
practiceRecordService.save(practiceRecord);

// 5. 更新课程记录
courseRecordService.updateEndTime(1001, new Date(), 89);
```

**返回结果：**
```java
totalScore = 89
report = {
    summary: "整体表现优秀，专业知识扎实，沟通能力良好，建议加强技术细节的讲解",
    strengths: ["专业知识扎实", "回答逻辑清晰", "客户需求理解到位"],
    improvements: ["可增加更多技术参数", "可提供更多实际案例"],
    finalScores: {"三电系统": 91, "智能驾驶": 86, "舒适性": 88, "外观设计": 92, "售后服务": 90}
}
```

---

#### 完整变量变化轨迹表

| 步骤 | 变量 | 初始值 | 变化后值 | 说明 |
|:---:|------|--------|----------|------|
| 1 | `recordId` | - | 1001 | 新生成的对练记录ID |
| 1 | `totalRounds` | - | 5 | 根据考核维度数量计算 |
| 2 | `currentRound` | 0 | 1 | 第1轮学员回复后 |
| 2 | `currentCategory` | - | "智能驾驶" | 随机排序后的第1个维度 |
| 2 | `isComplete` | - | false | 1 < 5 |
| 3 | `currentRound` | 1 | 2 | 第2轮学员回复后 |
| 3 | `currentCategory` | "智能驾驶" | "三电系统" | 随机排序后的第2个维度 |
| 3 | `isComplete` | false | false | 2 < 5 |
| 4 | `currentRound` | 2 | 3 | 第3轮学员回复后 |
| 4 | `currentCategory` | "三电系统" | "舒适性" | 随机排序后的第3个维度 |
| 5 | `currentRound` | 3 | 4 | 第4轮学员回复后 |
| 5 | `currentCategory` | "舒适性" | "外观设计" | 随机排序后的第4个维度 |
| 6 | `currentRound` | 4 | 5 | 第5轮学员回复后 |
| 6 | `currentCategory` | "外观设计" | "售后服务" | 随机排序后的第5个维度 |
| 6 | `isComplete` | false | true | 5 >= 5，触发结束 |
| 7 | `totalScore` | - | 89 | 最终总得分 |

---

## 五、核心业务逻辑说明

### 5.1 轮次计算规则

```java
// 总轮次计算
int totalRounds = scene.getExamCategories().split(",").length; // 考核维度数量

// 当前轮次计算（动态统计学员回复数量）
int currentRound = 0;
for (Dialog dialog : allDialogs) {
    if (dialog.getSpeaker() == 1 && dialog.getContent() != null) { // 学员消息
        currentRound++;
    }
}
currentRound++; // 学员回复后轮次+1
```

### 5.2 结束判断条件

```java
// 当当前轮次 >= 总轮次时，自动结束对练
boolean isComplete = currentRound >= totalRounds;

if (isComplete) {
    // 生成最终报告
    Report report = generateFinalReport(allDialogs, evaluations);
    int totalScore = calculateTotalScore(report);
    
    // 保存结果到数据库
    savePracticeRecord(recordId, totalScore, report);
}
```

---

## 六、错误处理示例

```java
try {
    PracticeTurnResponse response = apiClient.practiceTurn(turnRequest);
} catch (PracticeException e) {
    switch (e.getErrorCode()) {
        case "INVALID_MESSAGE":
            System.out.println("错误：消息内容无效（空消息或全是特殊字符）");
            break;
        case "RECORD_NOT_FOUND":
            System.out.println("错误：对练记录不存在");
            break;
        case "PRACTICE_ALREADY_COMPLETED":
            System.out.println("错误：对练已结束，无法继续");
            break;
        case "SYSTEM_ERROR":
            System.out.println("错误：系统内部错误");
            break;
    }
}
```

---

## 七、总结

| 关键点 | 说明 |
|--------|------|
| **流程入口** | 通过 `practiceStart(courseId, userName)` 开始 |
| **轮次控制** | 自动根据 `examCategories` 字段计算总轮次 |
| **维度顺序** | 使用 `recordId` 作为随机种子，确保同次对练维度顺序一致 |
| **结束机制** | 当前轮次达到总轮次时自动结束，也可手动调用 `practiceEnd()` |
| **数据存储** | `pract_course_record` 在开始时创建，`pract_record` 在结束时创建 |

---

**文档版本**: v1.0  
**创建日期**: 2026-05-22  
**适用场景**: 自由式对练系统 API 接口说明与调用示例