"""Pre-built Cypher query templates for common medical knowledge graph operations.

The Graph Query Agent uses these templates as a safer alternative to
fully LLM-generated Cypher — the model selects a template and fills
in the parameters, which greatly reduces hallucination risk.
"""

CYPHER_TEMPLATES: dict[str, dict] = {
    "disease_full_info": {
        "description": "获取疾病的完整信息：症状、治疗方案、药物、检查项目",
        "query": """
            MATCH (d:Disease)
            WHERE d.name CONTAINS $disease_name
            OPTIONAL MATCH (d)-[hs:HAS_SYMPTOM]->(s:Symptom)
            OPTIONAL MATCH (d)-[tb:TREATED_BY]->(t:Treatment)
            OPTIONAL MATCH (t)-[ud:USES_DRUG]->(drug:Drug)
            OPTIONAL MATCH (d)-[:REQUIRES_EXAM]->(e:Examination)
            RETURN d {.*, labels: labels(d)} AS disease,
                   collect(DISTINCT s {.*, frequency: hs.frequency}) AS symptoms,
                   collect(DISTINCT t {.*, evidence_level: tb.evidence_level}) AS treatments,
                   collect(DISTINCT drug {.*}) AS drugs,
                   collect(DISTINCT e {.*}) AS examinations
            LIMIT 10
        """,
        "parameters": ["disease_name"],
    },
    "disease_by_symptoms": {
        "description": "根据症状列表查找可能的疾病",
        "query": """
            UNWIND $symptom_names AS symptom_name
            MATCH (s:Symptom)<-[:HAS_SYMPTOM]-(d:Disease)
            WHERE s.name CONTAINS symptom_name
            WITH d, count(DISTINCT s) AS matched_symptoms
            ORDER BY matched_symptoms DESC
            RETURN d {.*} AS disease, matched_symptoms
            LIMIT 10
        """,
        "parameters": ["symptom_names"],
    },
    "drug_safety_info": {
        "description": "获取药物的安全信息：禁忌、副作用、相互作用",
        "query": """
            MATCH (drug:Drug)
            WHERE drug.name CONTAINS $drug_name
            OPTIONAL MATCH (drug)-[ci:CONTRAINDICATED_IN]->(c:Contraindication)
            OPTIONAL MATCH (drug)-[:HAS_SIDE_EFFECT]->(se:SideEffect)
            OPTIONAL MATCH (drug)-[iw:INTERACTS_WITH]->(other:Drug)
            RETURN drug {.*} AS drug,
                   collect(DISTINCT c {.*, reason: ci.reason, ci_severity: ci.severity}) AS contraindications,
                   collect(DISTINCT se {.*}) AS side_effects,
                   collect(DISTINCT other {.name, interaction_severity: iw.severity, mechanism: iw.mechanism}) AS interactions
            LIMIT 10
        """,
        "parameters": ["drug_name"],
    },
    "drug_contraindications_batch": {
        "description": "批量查询多个药物的禁忌信息",
        "query": """
            UNWIND $drug_names AS drug_name
            MATCH (drug:Drug)-[ci:CONTRAINDICATED_IN]->(c:Contraindication)
            WHERE drug.name CONTAINS drug_name
            RETURN drug.name AS drug_name,
                   drug.fda_category AS fda_category,
                   collect({
                       contraindication: c.name,
                       severity: ci.severity,
                       reason: ci.reason
                   }) AS contraindications
        """,
        "parameters": ["drug_names"],
    },
    "drug_interactions_check": {
        "description": "检查药物间的相互作用",
        "query": """
            UNWIND $drug_names AS dn1
            UNWIND $drug_names AS dn2
            WITH dn1, dn2 WHERE dn1 < dn2
            MATCH (d1:Drug)-[iw:INTERACTS_WITH]->(d2:Drug)
            WHERE d1.name CONTAINS dn1 AND d2.name CONTAINS dn2
            RETURN d1.name AS drug1, d2.name AS drug2,
                   iw.mechanism AS mechanism, iw.severity AS severity
        """,
        "parameters": ["drug_names"],
    },
    "department_knowledge": {
        "description": "获取特定科室关联的所有疾病和治疗知识",
        "query": """
            MATCH (d:Disease)-[:BELONGS_TO]->(dept:Department)
            WHERE dept.name CONTAINS $department_name
            OPTIONAL MATCH (d)-[:TREATED_BY]->(t:Treatment)
            OPTIONAL MATCH (t)-[:USES_DRUG]->(drug:Drug)
            RETURN d {.*} AS disease,
                   collect(DISTINCT t {.*}) AS treatments,
                   collect(DISTINCT drug {.name, .fda_category}) AS drugs
            LIMIT 20
        """,
        "parameters": ["department_name"],
    },
    "risk_factors": {
        "description": "获取疾病的风险因素和可能并发症",
        "query": """
            MATCH (d:Disease)
            WHERE d.name CONTAINS $disease_name
            OPTIONAL MATCH (d)-[:HAS_RISK_FACTOR]->(rf:RiskFactor)
            OPTIONAL MATCH (d)-[:MAY_CAUSE]->(comp:Complication)
            RETURN d {.*} AS disease,
                   collect(DISTINCT rf {.*}) AS risk_factors,
                   collect(DISTINCT comp {.*}) AS complications
            LIMIT 10
        """,
        "parameters": ["disease_name"],
    },
}
