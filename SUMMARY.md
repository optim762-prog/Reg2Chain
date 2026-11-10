# Main results

## Inter-annotator agreement
```
Double-annotated units: 14
Entities strict (span+type): A1=53 A2=61 agreed=48 F1=0.842
Entities untyped (span only): agreed=48 F1=0.842
Cohen's kappa (token level, 714 tokens): 0.826
Relations strict: A1=29 A2=36 agreed=27 F1=0.831
```
## Table 3 of the paper - extraction (test units)
```
system,task,setting,TP,FP,FN,P,R,F1,F1 95% CI
baseline,NER,strict,3,138,213,0.021,0.014,0.017,"[0.00, 0.04]"
baseline,NER,relaxed,32,109,184,0.227,0.148,0.179,"[0.11, 0.24]"
baseline,NER,untyped,93,48,123,0.66,0.431,0.521,"[0.45, 0.58]"
baseline,RE,strict,1,19,107,0.05,0.009,0.016,"[0.00, 0.06]"
baseline,RE,relaxed,1,19,107,0.05,0.009,0.016,"[0.00, 0.06]"
rules,NER,strict,152,32,64,0.826,0.704,0.76,"[0.67, 0.84]"
rules,NER,relaxed,163,21,53,0.886,0.755,0.815,"[0.74, 0.88]"
rules,NER,untyped,174,10,42,0.946,0.806,0.87,"[0.81, 0.92]"
rules,RE,strict,45,10,63,0.818,0.417,0.552,"[0.38, 0.69]"
rules,RE,relaxed,50,5,58,0.909,0.463,0.613,"[0.45, 0.75]"
llm,NER,strict,145,66,71,0.687,0.671,0.679,"[0.56, 0.79]"
```
```
system,setting,TP,FP,FN,P,R,F1,CI / test
rules,strict,59,7,49,0.894,0.546,0.678,"[0.53, 0.79]"
rules,relaxed,60,6,48,0.909,0.556,0.69,"[0.55, 0.80]"
llm,strict,72,32,36,0.692,0.667,0.679,"[0.55, 0.79]"
llm,relaxed,72,32,36,0.692,0.667,0.679,"[0.55, 0.79]"
hybrid,strict,79,38,29,0.675,0.731,0.702,"[0.59, 0.80]"
hybrid,relaxed,79,38,29,0.675,0.731,0.702,"[0.59, 0.80]"
hybrid vs rules,strict,,,,,,0.024,"[-0.048, 0.114] p=0.5516"
hybrid vs rules,relaxed,,,,,,0.013,"[-0.061, 0.104] p=0.7662"
hybrid vs llm,strict,,,,,,0.023,"[-0.015, 0.065] p=0.2438"
hybrid vs llm,relaxed,,,,,,0.023,"[-0.015, 0.065] p=0.2438"
llm vs rules,strict,,,,,,0.001,"[-0.092, 0.104] p=0.9702"
llm vs rules,relaxed,,,,,,-0.01,"[-0.104, 0.096] p=0.8470"
```
## Table 4 of the paper - knowledge graph
```
graph,nodes,edges,avg_degree,isolated_nodes,components,largest_component_share,concepts,rules,traceable_rules_share,rules_test,gold_rules_test,rule_TP,rule_precision,rule_recall,rule_F1,concept_precision
baseline,40,27,1.35,12,13,0.7,30,1,1.0,1,70,0,0.0,0.0,0.0,0.303
learned,237,273,2.3,17,19,0.844,99,57,1.0,47,70,39,0.83,0.557,0.667,0.878
refined,250,327,2.62,20,24,0.828,78,71,1.0,58,70,46,0.793,0.657,0.719,0.895
```
## Coverage of the requirements
```
ALL                              n=55  covered=36  partial=16  not_covered=3   undecided=0   coverage=65.5 % (with partial as 1/2: 80.0 %)
on_chain=OFF                     n=33  covered=30  partial=1   not_covered=2   undecided=0   coverage=90.9 % (with partial as 1/2: 92.4 %)
type=LIMIT                       n=23  covered=23  partial=0   not_covered=0   undecided=0   coverage=100.0 % (with partial as 1/2: 100.0 %)
```
## Regulatory query agent
```
ExtraVirginOliveOil                                     gold= 8 returned= 9 correct= 8
VirginOliveOil                                          gold= 7 returned= 8 correct= 7
LampanteOliveOil                                        gold= 2 returned= 0 correct= 0
RefinedOliveOil                                         gold= 4 returned= 4 correct= 4
OliveOilComposedOfRefinedOliveOilsAndVirginOliveOils    gold= 4 returned= 5 correct= 4
CrudeOlivePomaceOil                                     gold= 0 returned= 0 correct= 0
RefinedOlivePomaceOil                                   gold= 4 returned= 4 correct= 4
OlivePomaceOil                                          gold= 5 returned= 5 correct= 4
ALL quality limits: gold=34 returned=35 correct=31 precision=0.886 recall=0.912 F1=0.899
```
## Table 5 of the paper - contracts
```
model,condition,contracts,compile_raw,compile_normalised,limit_tests,no_invented_limit,labelling_tests,isCompliant_tests,all_tests_pass,traceability_correct,gas_deploy,gas_isCompliant,slither_high_medium
deepseek6.7b,C_json_onto,18,1.000,1.000,0.962 ± 0.052,0.933 ± 0.258,0.759 ± 0.322,0.778 ± 0.256,0.222,0.894 ± 0.243,671645,55485,0.000 ± 0.000
qwen14b,A_text,18,0.556,0.833,0.903 ± 0.151,0.771 ± 0.291,0.393 ± 0.338,0.667 ± 0.244,0.000,0.500 ± 0.514,881243,53196,0.000 ± 0.000
qwen14b,B_json,18,1.000,1.000,1.000 ± 0.000,1.000 ± 0.000,1.000 ± 0.000,1.000 ± 0.000,1.000,1.000 ± 0.000,733784,58736,0.000 ± 0.000
qwen14b,C_json_onto,18,1.000,1.000,1.000 ± 0.000,1.000 ± 0.000,1.000 ± 0.000,1.000 ± 0.000,1.000,1.000 ± 0.000,728135,58736,0.000 ± 0.000
qwen14b,D_json_solidity,18,1.000,1.000,1.000 ± 0.000,1.000 ± 0.000,1.000 ± 0.000,1.000 ± 0.000,1.000,1.000 ± 0.000,728908,58736,0.000 ± 0.000
qwen7b,A_text,18,0.944,1.000,0.830 ± 0.115,0.200 ± 0.104,0.519 ± 0.381,0.472 ± 0.118,0.000,0.667 ± 0.485,808335,57298,0.000 ± 0.000
qwen7b,B_json,18,1.000,1.000,0.882 ± 0.199,1.000 ± 0.000,0.580 ± 0.430,0.750 ± 0.257,0.056,0.667 ± 0.485,763727,56298,0.000 ± 0.000
qwen7b,C_json_onto,18,1.000,1.000,0.759 ± 0.229,1.000 ± 0.000,0.599 ± 0.441,0.750 ± 0.257,0.000,0.556 ± 0.511,775799,56298,0.000 ± 0.000
qwen7b,D_json_solidity,18,1.000,1.000,0.951 ± 0.143,1.000 ± 0.000,0.623 ± 0.456,0.806 ± 0.251,0.278,0.500 ± 0.514,774764,58672,0.000 ± 0.000
```
```
qwen7b/C_json_onto vs qwen7b/A_text: n=18 mean test pass 0.792 vs 0.681 (diff +0.111), Wilcoxon p=0.0094
qwen7b/B_json vs qwen7b/A_text: n=18 mean test pass 0.851 vs 0.681 (diff +0.170), Wilcoxon p=0.0013
qwen7b/C_json_onto vs qwen7b/B_json: n=18 mean test pass 0.792 vs 0.851 (diff -0.058), Wilcoxon p=0.1054
qwen14b/C_json_onto vs qwen14b/A_text: n=18 mean test pass 1.000 vs 0.652 (diff +0.348), Wilcoxon p=0.0002
qwen14b/B_json vs qwen14b/A_text: n=18 mean test pass 1.000 vs 0.652 (diff +0.348), Wilcoxon p=0.0002
qwen14b/C_json_onto vs qwen14b/B_json: n=18 mean test pass 1.000 vs 1.000 (diff +0.000), Wilcoxon p=1.0000
qwen7b/D_json_solidity vs qwen7b/B_json: n=18 mean test pass 0.911 vs 0.851 (diff +0.061), Wilcoxon p=0.0208
qwen7b/D_json_solidity vs qwen7b/A_text: n=18 mean test pass 0.911 vs 0.681 (diff +0.230), Wilcoxon p=0.0003
qwen14b/D_json_solidity vs qwen14b/B_json: n=18 mean test pass 1.000 vs 1.000 (diff +0.000), Wilcoxon p=1.0000
qwen14b/D_json_solidity vs qwen14b/A_text: n=18 mean test pass 1.000 vs 0.652 (diff +0.348), Wilcoxon p=0.0002
qwen14b/C_json_onto vs qwen7b/C_json_onto: n=18 mean test pass 1.000 vs 0.792 (diff +0.208), Wilcoxon p=0.0002
qwen14b/C_json_onto vs deepseek6.7b/C_json_onto: n=18 mean test pass 1.000 vs 0.877 (diff +0.123), Wilcoxon p=0.0010
```
## Table 6 of the paper - blind expert review
```
model=deepseek6.7b | condition=C_json_onto | contracts=2 | Q1_limits_correct=4.50 | Q2_labelling_correct=1.00 | Q5_traceability=2.00 | Q6_code_quality=2.00 | security_medium_high=2 | deployable_yes_or_minor=0 | minutes=17.0
model=qwen14b | condition=A_text | contracts=2 | Q1_limits_correct=3.50 | Q2_labelling_correct=1.50 | Q5_traceability=1.50 | Q6_code_quality=2.00 | security_medium_high=2 | deployable_yes_or_minor=0 | minutes=18.0
model=qwen14b | condition=B_json | contracts=2 | Q1_limits_correct=5.00 | Q2_labelling_correct=3.00 | Q5_traceability=5.00 | Q6_code_quality=3.00 | security_medium_high=2 | deployable_yes_or_minor=0 | minutes=17.0
model=qwen14b | condition=C_json_onto | contracts=2 | Q1_limits_correct=5.00 | Q2_labelling_correct=3.00 | Q5_traceability=5.00 | Q6_code_quality=3.00 | security_medium_high=2 | deployable_yes_or_minor=0 | minutes=10.0
model=qwen14b | condition=D_json_solidity | contracts=2 | Q1_limits_correct=5.00 | Q2_labelling_correct=3.00 | Q5_traceability=5.00 | Q6_code_quality=2.50 | security_medium_high=2 | deployable_yes_or_minor=0 | minutes=10.0
model=qwen7b | condition=A_text | contracts=2 | Q1_limits_correct=3.00 | Q2_labelling_correct=1.50 | Q5_traceability=1.50 | Q6_code_quality=3.00 | security_medium_high=2 | deployable_yes_or_minor=0 | minutes=21.0
model=qwen7b | condition=B_json | contracts=2 | Q1_limits_correct=3.00 | Q2_labelling_correct=2.50 | Q5_traceability=2.00 | Q6_code_quality=2.50 | security_medium_high=2 | deployable_yes_or_minor=0 | minutes=15.0
model=qwen7b | condition=C_json_onto | contracts=2 | Q1_limits_correct=3.00 | Q2_labelling_correct=2.50 | Q5_traceability=2.00 | Q6_code_quality=2.50 | security_medium_high=2 | deployable_yes_or_minor=0 | minutes=17.0
model=qwen7b | condition=D_json_solidity | contracts=2 | Q1_limits_correct=5.00 | Q2_labelling_correct=2.50 | Q5_traceability=2.00 | Q6_code_quality=3.00 | security_medium_high=2 | deployable_yes_or_minor=0 | minutes=10.0
Agreement expert correctness (mean Q1,Q2) vs automatic test pass rate: Spearman rho = 0.985 (n=18)
Total expert time: 135 min
```
