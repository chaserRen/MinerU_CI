import argparse
import requests
import time
import json
import sys
import os


# token = os.environ.get('CI_TOKEN')
HEADERS = {
    "Benchmark-Platform-User-Token": "57822467d6ef461c93ab6a14e8c13d65"
}
BASE_URL = 'http://10.140.24.137:8000/api/evaluationTasks'

baseline_values = {
    '总表（不区分中英文）': {
        'overall': 82.0,
        'text_block_Edit_dist': 0.08,
        'display_formula_CDM': 70.0,
        'table_TEDS': 87.0,
        'table_TEDS_structure_only': 90.0,
        'reading_order_Edit_dist': 0.09,                       
    },
    '总表': {
        'text_block_Edit_dist_EN': 0.04,
        'text_block_Edit_dist_CH': 0.09,
        'display_formula_Edit_dist_EN': 0.20,
        'display_formula_Edit_dist_CH': 0.40,
        'display_formula_CDM_EN': 80.0,
        'display_formula_CDM_CH': 60.0,
        'table_TEDS_EN': 85.0,
        'table_TEDS_CH': 87.0,
        'table_TEDS_structure_only_EN': 89.0,
        'table_TEDS_structure_only_CH': 90.0,
        'table_Edit_dist_EN': 0.13,
        'table_Edit_dist_CH': 0.10,
        'reading_order_Edit_dist_EN': 0.05,
        'reading_order_Edit_dist_CH': 0.10,
        'overall_EN': 0.11,
        'overall_CH': 0.18,
    },
    '分页面': {
        'data_source: PPT2PDF': 0.10,
        'data_source: academic_literature': 0.01,
        'data_source: book': 0.04,
        'data_source: colorful_textbook': 0.10,
        'data_source: exam_paper': 0.09,
        'data_source: magazine': 0.07,
        'data_source: newspaper': 0.15,
        'data_source: note': 0.08,
        'data_source: research_report': 0.02,
    }
}


def create_new_task(md_folders):
    print("正在创建新任务...")
    json_data = {
        'name': f'CI 测试{time.strftime("%Y%m%d%H%M%S")}',
        'model_name': 'Mineru-pipeline',
        'description': '测试CI流程-0804',
        'type': 'OmniDocBench_250804',
        'ground_truth': 'OmniDocBench_250731.json',
        'data_path': md_folders #'/mnt/hwfile/doc_parse/oylk/model_mds/Omnidocbench_A/Mineru2_ckp'
    }
    try:
        response = requests.post(BASE_URL, headers=HEADERS, json=json_data)
        response.raise_for_status()
        task_id = response.json().get('id')
        print(f"评测任务创建成功，ID为: {task_id}")
        return task_id
    except Exception as e:
        print(f"::error:: 错误：评测创建任务失败: {e}")
        return None

def poll_task_status(task_id): 
    """根据任务ID轮询任务状"""
    if not task_id:
        print("::error::错误：无效的任务ID，无法轮询。")
        return

    print(f"开始轮询任务: {task_id}")
    task_detail_url = f"{BASE_URL}"
    
    while True:
        try:
            query_url = f"http://10.140.24.137:8000/api/evaluationTasks/{task_id}/details" # id 详情接口
            response = requests.get(query_url, headers=HEADERS)
            response.raise_for_status()
            task_info = response.json()
            status = task_info.get('status')  # 
            print(f"任务 {task_id} 的当前状态是: {status}")

            eval_res = {}
            if status == 'completed':
                print("任务成功完成！")
                eval_res = task_info.get('score_map')
                return eval_res
            elif status in ['failed']: 
                print("任务失败！")
                print("任务详情:", task_info)
                return eval_res
            
            time.sleep(60) 

        except requests.exceptions.RequestException as e:
            print(f"轮询过程中发生网络错误: {e}")
            break
        except Exception as e:
            print(f"轮询过程中发生未知错误: {e}")
            break

def omini_assertions(omnibench_res, baseline):
    all_passed = True
    tolerance = 0.15

    for main_key, sub_metric  in baseline.items():
        print(f"------ 验证 {main_key} 维度 ------")
        if main_key not in omnibench_res:
            print(f"::error::错误: Baseline中维度 '{main_key}' 未在接口返回的结果中找到")
            continue
            
        for metric_key, baseline_value in sub_metric.items():
            if metric_key not in omnibench_res[main_key]:
                print(f"::error::错误: Baseline中维度 '{main_key}' 中指标 '{metirc_key}' 未在接口返回的结果中找到")
                all_passed = False
                continue

            actual_value = omnibench_res[main_key][metric_key]
            if not isinstance(actual_value, (int, float)):
                 print(f"::error::错误: 指标 '{main_key} -> {metric_key}' 的实际值 '{actual_value}' 不是数值类型。")
                 all_passed = False
                 continue
            
            lower_bound = baseline_value - tolerance
            higer_bound = baseline_value + tolerance

            if not (lower_bound <= actual_value <= higer_bound):
                print(f"评测不通过: 指标 '{main_key} -> {metric_key}'")
                print(f"  - 允许范围: [{lower_bound:.4f}, {higer_bound:.4f}]")
                print(f"  - 评测分数: {actual_value:.4f}")
                all_passed = False
            else:
                print(f"评测通过: 指标 '{main_key} -> {metric_key}' (值为 {actual_value:.4f})")

    return all_passed

if __name__ == "__main__":    
    # # --- Debug Model ---
    # # # 1. 创建任务
    # # # md_folders = sys.argv[1]
    # # md_folders = "/mnt/hwfile/doc_parse/oylk/model_mds/Omnidocbench_A/Mineru2_ckp"
    # # print(f"开始处理文件夹: {md_folders}")
    # # task_id = create_new_task(md_folders)
    
    # # 2. 根据任务id轮询任务状态
    # known_task_id = '688c30b77d8df5f248a5a360'
    # # '68916ccbd017bd9da06768ac'
    # # '688c30b77d8df5f248a5a360' 
    # # '6889b85b1689550f768dd46d'
    # eval_res = poll_task_status(known_task_id)

    # omini_assertions(eval_res, baseline_values)
    
    # --- Running Model ---
    parser = argparse.ArgumentParser(description="OmniDocBench Benchmark CI Evaluation")
    parser.add_argument("md_folders", type=str, help="Mineru CLI OUTPUT FOLDER PATH")
    args = parser.parse_args()

    print(f"OmniDocBench CI START, MD FOLDER PATH: {args.md_folders}")

    task_id = create_new_task(args.md_folders)

    if not task_id:
        print("::error:: OmniDocBench CI FAILED")
        sys.exit(1)
    
    eval_res = poll_task_status(task_id)

    if not eval_res:
        print("::error:: OmniDocBench EVAL FAILED")
        sys.exit(1)
    
    if omini_assertions(eval_res, baseline_values):
        print("OmniDocBench CI EVAL PASS")
        sys.exit(1)
    else:
        print("::error:: OmniDocBench EVAL RESULT FAILED")
        sys.exit(0)