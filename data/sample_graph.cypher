// ============================================================
// 妇产科知识图谱 — 示例数据
// 在 Neo4j Browser 或 cypher-shell 中执行此脚本导入
// ============================================================

// --- 清理旧数据（谨慎使用） ---
// MATCH (n) DETACH DELETE n;

// --- 创建约束和索引 ---
CREATE CONSTRAINT IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (drug:Drug) REQUIRE drug.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (dept:Department) REQUIRE dept.name IS UNIQUE;
CREATE INDEX IF NOT EXISTS FOR (t:Treatment) ON (t.name);
CREATE INDEX IF NOT EXISTS FOR (e:Examination) ON (e.name);

// === 科室节点 ===
MERGE (dept_ob:Department {name: '产科'})
MERGE (dept_endo:Department {name: '内分泌科'})
MERGE (dept_cardio:Department {name: '心内科'})
MERGE (dept_nephro:Department {name: '肾内科'});

// === 疾病节点 ===
MERGE (gdm:Disease {
    name: '妊娠期糖尿病',
    icd_code: 'O24.4',
    description: '妊娠期间首次发生或发现的糖耐量异常',
    severity_level: '中'
})
MERGE (pe:Disease {
    name: '子痫前期',
    icd_code: 'O14',
    description: '妊娠20周后出现高血压伴蛋白尿或其他系统受累',
    severity_level: '高'
})
MERGE (ghy:Disease {
    name: '妊娠期高血压',
    icd_code: 'O13',
    description: '妊娠20周后首次出现高血压，无蛋白尿',
    severity_level: '中'
})
MERGE (anemia:Disease {
    name: '妊娠期贫血',
    icd_code: 'O99.0',
    description: '妊娠期间血红蛋白低于110g/L',
    severity_level: '低'
})
MERGE (thyroid:Disease {
    name: '妊娠期甲状腺功能减退',
    icd_code: 'O99.2',
    description: '妊娠期间甲状腺功能低下',
    severity_level: '中'
});

// === 症状节点 ===
MERGE (s_glucose:Symptom {name: '糖耐量异常', description: 'OGTT结果异常', body_part: '全身'})
MERGE (s_edema:Symptom {name: '水肿', description: '组织间液过多导致的肿胀', body_part: '下肢'})
MERGE (s_hypertension:Symptom {name: '高血压', description: '血压≥140/90mmHg', body_part: '心血管'})
MERGE (s_proteinuria:Symptom {name: '蛋白尿', description: '尿蛋白定量≥0.3g/24h', body_part: '泌尿系统'})
MERGE (s_headache:Symptom {name: '头痛', description: '持续性头痛', body_part: '头部'})
MERGE (s_blurred_vision:Symptom {name: '视物模糊', description: '视觉障碍', body_part: '眼部'})
MERGE (s_polyuria:Symptom {name: '多尿', description: '尿量增多', body_part: '泌尿系统'})
MERGE (s_polydipsia:Symptom {name: '多饮', description: '饮水量增多', body_part: '全身'})
MERGE (s_fatigue:Symptom {name: '疲乏', description: '持续性疲劳感', body_part: '全身'})
MERGE (s_pallor:Symptom {name: '面色苍白', description: '皮肤黏膜苍白', body_part: '面部'})
MERGE (s_cold_intolerance:Symptom {name: '畏寒', description: '对寒冷敏感', body_part: '全身'});

// === 治疗方案节点 ===
MERGE (t_mnt:Treatment {name: '医学营养治疗(MNT)', type: '生活方式', guideline_source: '中华医学会妇产科学分会2022指南'})
MERGE (t_insulin:Treatment {name: '胰岛素治疗', type: '药物治疗', guideline_source: 'ADA 2024指南'})
MERGE (t_antihypertensive:Treatment {name: '降压治疗', type: '药物治疗', guideline_source: 'ACOG 2023指南'})
MERGE (t_magnesium:Treatment {name: '硫酸镁治疗', type: '药物治疗', guideline_source: 'WHO推荐'})
MERGE (t_iron:Treatment {name: '补铁治疗', type: '药物治疗', guideline_source: '中华医学会2021指南'})
MERGE (t_levothyroxine:Treatment {name: '左甲状腺素替代治疗', type: '药物治疗', guideline_source: 'ATA 2017指南'})
MERGE (t_exercise:Treatment {name: '运动处方', type: '生活方式', guideline_source: 'ACOG 2020运动指南'})
MERGE (t_termination:Treatment {name: '适时终止妊娠', type: '手术', guideline_source: 'ACOG实践指南'});

// === 药物节点 ===
MERGE (d_insulin_r:Drug {name: '门冬胰岛素', generic_name: 'Insulin Aspart', fda_category: 'B'})
MERGE (d_insulin_n:Drug {name: '低精蛋白锌胰岛素', generic_name: 'NPH Insulin', fda_category: 'B'})
MERGE (d_metformin:Drug {name: '二甲双胍', generic_name: 'Metformin', fda_category: 'B'})
MERGE (d_labetalol:Drug {name: '拉贝洛尔', generic_name: 'Labetalol', fda_category: 'C'})
MERGE (d_nifedipine:Drug {name: '硝苯地平', generic_name: 'Nifedipine', fda_category: 'C'})
MERGE (d_mgso4:Drug {name: '硫酸镁', generic_name: 'Magnesium Sulfate', fda_category: 'B'})
MERGE (d_ferrous:Drug {name: '琥珀酸亚铁', generic_name: 'Ferrous Succinate', fda_category: 'A'})
MERGE (d_levothyroxine:Drug {name: '左甲状腺素钠', generic_name: 'Levothyroxine', fda_category: 'A'})
MERGE (d_glyburide:Drug {name: '格列本脲', generic_name: 'Glyburide', fda_category: 'C'})
MERGE (d_enalapril:Drug {name: '依那普利', generic_name: 'Enalapril', fda_category: 'D'})
MERGE (d_atenolol:Drug {name: '阿替洛尔', generic_name: 'Atenolol', fda_category: 'D'})
MERGE (d_warfarin:Drug {name: '华法林', generic_name: 'Warfarin', fda_category: 'X'});

// === 检查项目节点 ===
MERGE (e_ogtt:Examination {name: 'OGTT(口服葡萄糖耐量试验)', type: '实验室检查', normal_range: '空腹<5.1,1h<10.0,2h<8.5', unit: 'mmol/L'})
MERGE (e_hba1c:Examination {name: '糖化血红蛋白(HbA1c)', type: '实验室检查', normal_range: '<5.7%', unit: '%'})
MERGE (e_bp:Examination {name: '血压监测', type: '体格检查', normal_range: '<140/90', unit: 'mmHg'})
MERGE (e_urine_protein:Examination {name: '尿蛋白定量', type: '实验室检查', normal_range: '<0.3', unit: 'g/24h'})
MERGE (e_liver_function:Examination {name: '肝功能检查', type: '实验室检查', normal_range: 'ALT<40,AST<40', unit: 'U/L'})
MERGE (e_platelet:Examination {name: '血小板计数', type: '实验室检查', normal_range: '100-300', unit: '×10^9/L'})
MERGE (e_ultrasound:Examination {name: '产科超声', type: '影像检查', normal_range: '', unit: ''})
MERGE (e_nst:Examination {name: 'NST(无应激试验)', type: '胎儿监护', normal_range: '反应型', unit: ''})
MERGE (e_tsh:Examination {name: 'TSH检测', type: '实验室检查', normal_range: '孕早期0.1-2.5,孕中期0.2-3.0,孕晚期0.3-3.0', unit: 'mIU/L'})
MERGE (e_hemoglobin:Examination {name: '血红蛋白检测', type: '实验室检查', normal_range: '≥110', unit: 'g/L'});

// === 禁忌节点 ===
MERGE (ci_pregnancy:Contraindication {name: '妊娠期', severity: '绝对禁忌', context: '妊娠期间禁用'})
MERGE (ci_renal_failure:Contraindication {name: '肾功能衰竭', severity: '绝对禁忌', context: '肾功能严重受损时禁用'})
MERGE (ci_liver_disease:Contraindication {name: '严重肝病', severity: '绝对禁忌', context: '肝功能严重受损时禁用'})
MERGE (ci_asthma:Contraindication {name: '支气管哮喘', severity: '相对禁忌', context: '哮喘患者慎用β受体阻滞剂'})
MERGE (ci_heart_block:Contraindication {name: '心脏传导阻滞', severity: '绝对禁忌', context: 'II/III度房室传导阻滞禁用'});

// === 副作用节点 ===
MERGE (se_hypoglycemia:SideEffect {name: '低血糖', severity: '中', frequency: '常见'})
MERGE (se_gi:SideEffect {name: '胃肠道不适', severity: '低', frequency: '常见'})
MERGE (se_hypotension:SideEffect {name: '低血压', severity: '中', frequency: '偶见'})
MERGE (se_bradycardia:SideEffect {name: '心动过缓', severity: '中', frequency: '偶见'})
MERGE (se_constipation:SideEffect {name: '便秘', severity: '低', frequency: '常见'})
MERGE (se_flushing:SideEffect {name: '面部潮红', severity: '低', frequency: '常见'});

// === 风险因素节点 ===
MERGE (rf_obesity:RiskFactor {name: '肥胖(BMI≥28)', description: '体重指数过高'})
MERGE (rf_age:RiskFactor {name: '高龄(≥35岁)', description: '孕妇年龄≥35岁'})
MERGE (rf_family_dm:RiskFactor {name: '糖尿病家族史', description: '一级亲属有糖尿病'})
MERGE (rf_prev_gdm:RiskFactor {name: '既往GDM病史', description: '既往妊娠有妊娠期糖尿病'})
MERGE (rf_prev_pe:RiskFactor {name: '既往子痫前期病史', description: '既往妊娠有子痫前期'})
MERGE (rf_multiple:RiskFactor {name: '多胎妊娠', description: '双胎或多胎妊娠'})
MERGE (rf_first_pregnancy:RiskFactor {name: '初次妊娠', description: '首次怀孕'});

// === 并发症节点 ===
MERGE (comp_macrosomia:Complication {name: '巨大儿', description: '胎儿出生体重≥4000g', severity: '中'})
MERGE (comp_neonatal_hypo:Complication {name: '新生儿低血糖', description: '出生后新生儿血糖过低', severity: '中'})
MERGE (comp_eclampsia:Complication {name: '子痫', description: '子痫前期基础上出现抽搐', severity: '高'})
MERGE (comp_hellp:Complication {name: 'HELLP综合征', description: '溶血、肝酶升高、血小板减少', severity: '高'})
MERGE (comp_placental_abruption:Complication {name: '胎盘早剥', description: '胎盘在胎儿娩出前从子宫壁剥离', severity: '高'})
MERGE (comp_preterm:Complication {name: '早产', description: '妊娠满28周至不满37周间分娩', severity: '中'});

// ============================================================
// 建立关系
// ============================================================

// --- 妊娠期糖尿病 (GDM) 关系 ---
MATCH (gdm:Disease {name: '妊娠期糖尿病'})

MATCH (s:Symptom {name: '糖耐量异常'}) MERGE (gdm)-[:HAS_SYMPTOM {frequency: '必要条件', specificity: '高'}]->(s)
WITH gdm
MATCH (s:Symptom {name: '多尿'}) MERGE (gdm)-[:HAS_SYMPTOM {frequency: '常见', specificity: '低'}]->(s)
WITH gdm
MATCH (s:Symptom {name: '多饮'}) MERGE (gdm)-[:HAS_SYMPTOM {frequency: '常见', specificity: '低'}]->(s)
WITH gdm
MATCH (s:Symptom {name: '疲乏'}) MERGE (gdm)-[:HAS_SYMPTOM {frequency: '常见', specificity: '低'}]->(s)

WITH gdm
MATCH (t:Treatment {name: '医学营养治疗(MNT)'}) MERGE (gdm)-[:TREATED_BY {evidence_level: 'A', guideline: '一线治疗'}]->(t)
WITH gdm
MATCH (t:Treatment {name: '胰岛素治疗'}) MERGE (gdm)-[:TREATED_BY {evidence_level: 'A', guideline: 'MNT无效后首选'}]->(t)
WITH gdm
MATCH (t:Treatment {name: '运动处方'}) MERGE (gdm)-[:TREATED_BY {evidence_level: 'B', guideline: '辅助治疗'}]->(t)

WITH gdm
MATCH (e:Examination {name: 'OGTT(口服葡萄糖耐量试验)'}) MERGE (gdm)-[:REQUIRES_EXAM]->(e)
WITH gdm
MATCH (e:Examination {name: '糖化血红蛋白(HbA1c)'}) MERGE (gdm)-[:REQUIRES_EXAM]->(e)
WITH gdm
MATCH (e:Examination {name: '产科超声'}) MERGE (gdm)-[:REQUIRES_EXAM]->(e)
WITH gdm
MATCH (e:Examination {name: 'NST(无应激试验)'}) MERGE (gdm)-[:REQUIRES_EXAM]->(e)

WITH gdm
MATCH (dept:Department {name: '产科'}) MERGE (gdm)-[:BELONGS_TO]->(dept)
WITH gdm
MATCH (dept:Department {name: '内分泌科'}) MERGE (gdm)-[:BELONGS_TO]->(dept)

WITH gdm
MATCH (rf:RiskFactor {name: '肥胖(BMI≥28)'}) MERGE (gdm)-[:HAS_RISK_FACTOR]->(rf)
WITH gdm
MATCH (rf:RiskFactor {name: '高龄(≥35岁)'}) MERGE (gdm)-[:HAS_RISK_FACTOR]->(rf)
WITH gdm
MATCH (rf:RiskFactor {name: '糖尿病家族史'}) MERGE (gdm)-[:HAS_RISK_FACTOR]->(rf)
WITH gdm
MATCH (rf:RiskFactor {name: '既往GDM病史'}) MERGE (gdm)-[:HAS_RISK_FACTOR]->(rf)

WITH gdm
MATCH (comp:Complication {name: '巨大儿'}) MERGE (gdm)-[:MAY_CAUSE]->(comp)
WITH gdm
MATCH (comp:Complication {name: '新生儿低血糖'}) MERGE (gdm)-[:MAY_CAUSE]->(comp)
WITH gdm
MATCH (comp:Complication {name: '早产'}) MERGE (gdm)-[:MAY_CAUSE]->(comp);

// --- 子痫前期 (PE) 关系 ---
MATCH (pe:Disease {name: '子痫前期'})

MATCH (s:Symptom {name: '高血压'}) MERGE (pe)-[:HAS_SYMPTOM {frequency: '必要条件', specificity: '中'}]->(s)
WITH pe
MATCH (s:Symptom {name: '蛋白尿'}) MERGE (pe)-[:HAS_SYMPTOM {frequency: '常见', specificity: '中'}]->(s)
WITH pe
MATCH (s:Symptom {name: '水肿'}) MERGE (pe)-[:HAS_SYMPTOM {frequency: '常见', specificity: '低'}]->(s)
WITH pe
MATCH (s:Symptom {name: '头痛'}) MERGE (pe)-[:HAS_SYMPTOM {frequency: '重度标志', specificity: '中'}]->(s)
WITH pe
MATCH (s:Symptom {name: '视物模糊'}) MERGE (pe)-[:HAS_SYMPTOM {frequency: '重度标志', specificity: '高'}]->(s)

WITH pe
MATCH (t:Treatment {name: '降压治疗'}) MERGE (pe)-[:TREATED_BY {evidence_level: 'A', guideline: '血压≥160/110需紧急降压'}]->(t)
WITH pe
MATCH (t:Treatment {name: '硫酸镁治疗'}) MERGE (pe)-[:TREATED_BY {evidence_level: 'A', guideline: '预防子痫抽搐'}]->(t)
WITH pe
MATCH (t:Treatment {name: '适时终止妊娠'}) MERGE (pe)-[:TREATED_BY {evidence_level: 'A', guideline: '根治性治疗'}]->(t)

WITH pe
MATCH (e:Examination {name: '血压监测'}) MERGE (pe)-[:REQUIRES_EXAM]->(e)
WITH pe
MATCH (e:Examination {name: '尿蛋白定量'}) MERGE (pe)-[:REQUIRES_EXAM]->(e)
WITH pe
MATCH (e:Examination {name: '肝功能检查'}) MERGE (pe)-[:REQUIRES_EXAM]->(e)
WITH pe
MATCH (e:Examination {name: '血小板计数'}) MERGE (pe)-[:REQUIRES_EXAM]->(e)
WITH pe
MATCH (e:Examination {name: '产科超声'}) MERGE (pe)-[:REQUIRES_EXAM]->(e)

WITH pe
MATCH (dept:Department {name: '产科'}) MERGE (pe)-[:BELONGS_TO]->(dept)
WITH pe
MATCH (dept:Department {name: '心内科'}) MERGE (pe)-[:BELONGS_TO]->(dept)
WITH pe
MATCH (dept:Department {name: '肾内科'}) MERGE (pe)-[:BELONGS_TO]->(dept)

WITH pe
MATCH (rf:RiskFactor {name: '初次妊娠'}) MERGE (pe)-[:HAS_RISK_FACTOR]->(rf)
WITH pe
MATCH (rf:RiskFactor {name: '高龄(≥35岁)'}) MERGE (pe)-[:HAS_RISK_FACTOR]->(rf)
WITH pe
MATCH (rf:RiskFactor {name: '既往子痫前期病史'}) MERGE (pe)-[:HAS_RISK_FACTOR]->(rf)
WITH pe
MATCH (rf:RiskFactor {name: '多胎妊娠'}) MERGE (pe)-[:HAS_RISK_FACTOR]->(rf)

WITH pe
MATCH (comp:Complication {name: '子痫'}) MERGE (pe)-[:MAY_CAUSE]->(comp)
WITH pe
MATCH (comp:Complication {name: 'HELLP综合征'}) MERGE (pe)-[:MAY_CAUSE]->(comp)
WITH pe
MATCH (comp:Complication {name: '胎盘早剥'}) MERGE (pe)-[:MAY_CAUSE]->(comp)
WITH pe
MATCH (comp:Complication {name: '早产'}) MERGE (pe)-[:MAY_CAUSE]->(comp);

// --- 妊娠期甲减 关系 ---
MATCH (thyroid:Disease {name: '妊娠期甲状腺功能减退'})
MATCH (s:Symptom {name: '疲乏'}) MERGE (thyroid)-[:HAS_SYMPTOM {frequency: '常见', specificity: '低'}]->(s)
WITH thyroid
MATCH (s:Symptom {name: '畏寒'}) MERGE (thyroid)-[:HAS_SYMPTOM {frequency: '常见', specificity: '中'}]->(s)
WITH thyroid
MATCH (s:Symptom {name: '水肿'}) MERGE (thyroid)-[:HAS_SYMPTOM {frequency: '常见', specificity: '低'}]->(s)
WITH thyroid
MATCH (t:Treatment {name: '左甲状腺素替代治疗'}) MERGE (thyroid)-[:TREATED_BY {evidence_level: 'A', guideline: '首选治疗'}]->(t)
WITH thyroid
MATCH (e:Examination {name: 'TSH检测'}) MERGE (thyroid)-[:REQUIRES_EXAM]->(e)
WITH thyroid
MATCH (dept:Department {name: '内分泌科'}) MERGE (thyroid)-[:BELONGS_TO]->(dept)
WITH thyroid
MATCH (dept:Department {name: '产科'}) MERGE (thyroid)-[:BELONGS_TO]->(dept);

// --- 治疗方案-药物关系 ---
MATCH (t:Treatment {name: '胰岛素治疗'})
MATCH (d:Drug {name: '门冬胰岛素'}) MERGE (t)-[:USES_DRUG {dosage: '个体化', route: '皮下注射', duration: '至分娩'}]->(d)
WITH t
MATCH (d:Drug {name: '低精蛋白锌胰岛素'}) MERGE (t)-[:USES_DRUG {dosage: '个体化', route: '皮下注射', duration: '至分娩'}]->(d);

MATCH (t:Treatment {name: '降压治疗'})
MATCH (d:Drug {name: '拉贝洛尔'}) MERGE (t)-[:USES_DRUG {dosage: '50-200mg tid', route: '口服', duration: '至分娩后血压稳定'}]->(d)
WITH t
MATCH (d:Drug {name: '硝苯地平'}) MERGE (t)-[:USES_DRUG {dosage: '10-20mg tid', route: '口服', duration: '至分娩后血压稳定'}]->(d);

MATCH (t:Treatment {name: '硫酸镁治疗'})
MATCH (d:Drug {name: '硫酸镁'}) MERGE (t)-[:USES_DRUG {dosage: '负荷量4g+维持1-2g/h', route: '静脉注射', duration: '产后24-48h'}]->(d);

MATCH (t:Treatment {name: '补铁治疗'})
MATCH (d:Drug {name: '琥珀酸亚铁'}) MERGE (t)-[:USES_DRUG {dosage: '0.1g tid', route: '口服', duration: '血红蛋白恢复正常后继续3个月'}]->(d);

MATCH (t:Treatment {name: '左甲状腺素替代治疗'})
MATCH (d:Drug {name: '左甲状腺素钠'}) MERGE (t)-[:USES_DRUG {dosage: '个体化,孕期需增量30-50%', route: '口服', duration: '长期'}]->(d);

// --- 药物禁忌关系 ---
MATCH (d:Drug {name: '依那普利'}), (ci:Contraindication {name: '妊娠期'})
MERGE (d)-[:CONTRAINDICATED_IN {reason: 'ACEI类药物可致胎儿肾发育异常、羊水过少、颅骨发育不良', severity: '绝对禁忌'}]->(ci);

MATCH (d:Drug {name: '华法林'}), (ci:Contraindication {name: '妊娠期'})
MERGE (d)-[:CONTRAINDICATED_IN {reason: '可致华法林胚胎病：鼻发育不良、骨骺点状钙化', severity: '绝对禁忌'}]->(ci);

MATCH (d:Drug {name: '阿替洛尔'}), (ci:Contraindication {name: '妊娠期'})
MERGE (d)-[:CONTRAINDICATED_IN {reason: '可致胎儿宫内生长受限', severity: '绝对禁忌'}]->(ci);

MATCH (d:Drug {name: '拉贝洛尔'}), (ci:Contraindication {name: '支气管哮喘'})
MERGE (d)-[:CONTRAINDICATED_IN {reason: 'β受体阻滞作用可诱发支气管痉挛', severity: '相对禁忌'}]->(ci);

MATCH (d:Drug {name: '拉贝洛尔'}), (ci:Contraindication {name: '心脏传导阻滞'})
MERGE (d)-[:CONTRAINDICATED_IN {reason: '可加重传导阻滞', severity: '绝对禁忌'}]->(ci);

MATCH (d:Drug {name: '二甲双胍'}), (ci:Contraindication {name: '肾功能衰竭'})
MERGE (d)-[:CONTRAINDICATED_IN {reason: '肾功能不全时乳酸酸中毒风险增加', severity: '绝对禁忌'}]->(ci);

MATCH (d:Drug {name: '二甲双胍'}), (ci:Contraindication {name: '严重肝病'})
MERGE (d)-[:CONTRAINDICATED_IN {reason: '肝功能不全影响乳酸代谢', severity: '绝对禁忌'}]->(ci);

// --- 药物副作用关系 ---
MATCH (d:Drug {name: '门冬胰岛素'}), (se:SideEffect {name: '低血糖'}) MERGE (d)-[:HAS_SIDE_EFFECT]->(se);
MATCH (d:Drug {name: '二甲双胍'}), (se:SideEffect {name: '胃肠道不适'}) MERGE (d)-[:HAS_SIDE_EFFECT]->(se);
MATCH (d:Drug {name: '拉贝洛尔'}), (se:SideEffect {name: '低血压'}) MERGE (d)-[:HAS_SIDE_EFFECT]->(se);
MATCH (d:Drug {name: '拉贝洛尔'}), (se:SideEffect {name: '心动过缓'}) MERGE (d)-[:HAS_SIDE_EFFECT]->(se);
MATCH (d:Drug {name: '硝苯地平'}), (se:SideEffect {name: '面部潮红'}) MERGE (d)-[:HAS_SIDE_EFFECT]->(se);
MATCH (d:Drug {name: '硝苯地平'}), (se:SideEffect {name: '低血压'}) MERGE (d)-[:HAS_SIDE_EFFECT]->(se);
MATCH (d:Drug {name: '琥珀酸亚铁'}), (se:SideEffect {name: '便秘'}) MERGE (d)-[:HAS_SIDE_EFFECT]->(se);
MATCH (d:Drug {name: '琥珀酸亚铁'}), (se:SideEffect {name: '胃肠道不适'}) MERGE (d)-[:HAS_SIDE_EFFECT]->(se);

// --- 药物相互作用关系 ---
MATCH (d1:Drug {name: '硫酸镁'}), (d2:Drug {name: '硝苯地平'})
MERGE (d1)-[:INTERACTS_WITH {mechanism: '协同降压效应，可致严重低血压和神经肌肉阻滞', severity: '高'}]->(d2);

MATCH (d1:Drug {name: '门冬胰岛素'}), (d2:Drug {name: '拉贝洛尔'})
MERGE (d1)-[:INTERACTS_WITH {mechanism: 'β阻滞剂可掩盖低血糖症状', severity: '中'}]->(d2);
