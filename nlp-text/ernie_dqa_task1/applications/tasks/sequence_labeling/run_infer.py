# -*- coding: utf-8 -*
"""import"""
import os
import sys
sys.path.append("../../../")
import numpy as np
from erniekit.common.register import RegisterSet
from erniekit.common import register
from erniekit.data.data_set import DataSet
import logging
from erniekit.utils import args
from erniekit.utils import params
from erniekit.utils import log



def dataset_reader_from_params(params_dict):
    """
    :param params_dict:
    :return:
    """
    dataset_reader = DataSet(params_dict)
    dataset_reader.build()

    return dataset_reader


def build_inference(params_dict, dataset_reader, parser_handler):
    """build trainer"""
    inference_name = params_dict.get("type", "CustomInference")
    inference_class = RegisterSet.inference.__getitem__(inference_name)
    inference = inference_class(params=params_dict, data_set_reader=dataset_reader, parser_handler=parser_handler)

    return inference


def parse_predict_result(predict_result, input_list, params_dict, seq_lens):
    """按需解析模型预测出来的结果
    :param predict_result: 模型预测出来的结果
    :param input_list: 样本明文数据，dict类型
    :param params_dict: 一些参数配置
    :return:list 希望保存到文件中的结果，output/predict_result.txt
    """
    return_list = []
    return_score_list = []
    start_probs = predict_result[0].copy_to_cpu()
    start_probs = start_probs.tolist()
    end_probs = predict_result[1].copy_to_cpu()
    end_probs = end_probs.tolist()
    src_tokens = input_list[0]
    for i in range(len(src_tokens)):
        src_token_list = src_tokens[i]
        doc_start_index = src_token_list.index('[SEP]')
        doc_end_index = len(src_token_list) - 1
        best_7_start_index = sorted(enumerate(start_probs[i]), key=lambda x: x[1], reverse=True)[:7]
        best_7_end_index = sorted(enumerate(end_probs[i]), key=lambda x: x[1], reverse=True)[:7]
        start_end_pairs = []
        for s in best_7_start_index:
            for e in best_7_end_index:
                if (s[0] <= e[0] and s[0] > doc_start_index and e[0] < doc_end_index) or (s[0] == 0 and e[0] == 0):
                    start_end_pairs.append((s[0], e[0], s[1]*e[1]))
        if len(start_end_pairs) == 0:
            return_list.append("NoAnswer")
            return_score_list.append(0.0)
            continue
        sorted_start_end_pairs = sorted(start_end_pairs, key=lambda x:x[2], reverse=True)
        for sorted_pair in sorted_start_end_pairs:
            start_index = sorted_pair[0]
            end_index = sorted_pair[1]
            if start_index == 0 and end_index == 0:
                return_list.append('NoAnswer')
                return_score_list.append(round(sorted_pair[2], 5))
                break
            elif start_index == 0 or end_index == 0:
                continue
            else:
                predict_answer = ''.join(src_token_list[start_index : end_index+1])
                return_list.append(predict_answer)
                return_score_list.append(round(sorted_pair[2], 5))
                break
        else:
            return_list.append('NoAnswer')
            return_score_list.append(0.0)

    return return_list, return_score_list


if __name__ == "__main__":
    args = args.build_common_arguments()
    log.init_log("./log/test", level=logging.DEBUG)
    param_dict = params.from_file(args.param_path)
    _params = params.replace_none(param_dict)

    # 记得import一下注册的模块
    register.import_modules()
    register.import_new_module("inference", "custom_inference")
    
    dataset_reader_params_dict = _params.get("dataset_reader")
    dataset_reader = dataset_reader_from_params(dataset_reader_params_dict)

    inference_params_dict = _params.get("inference")

    inference = build_inference(inference_params_dict, dataset_reader, parse_predict_result)

    inference.inference_batch()

    logging.info("os exit.")
    os._exit(0)
