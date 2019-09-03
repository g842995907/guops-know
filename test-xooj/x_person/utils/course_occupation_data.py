# -*- coding: utf-8 -*-

def get_30day_CompleteData(bubbleOption_data_30, dataCourse=None, dataPratice=None, dataMatch=None):
    """
    拼接echarts图标30之前的数据列表
    :param bubbleOption_data_30: 30天原始数据
    :param dataCourse: 课程数据列表
    :param dataPratice: 练习数据列表
    :param dataMatch: 比赛数据列表
    :return:
    """
    data = {}
    if dataCourse is not None:
        data_course = merge_list(bubbleOption_data_30, dataCourse)
        data['dataCourse'] = data_course

    if dataPratice is not None:
        data_pratice = merge_list(bubbleOption_data_30, dataPratice)
        data['dataPratice'] = data_pratice

    if dataMatch is not None:
        data_match = merge_list(bubbleOption_data_30, dataMatch)
        data['dataMatch'] = data_match

    return data


def merge_list(bubbleOption_data_30, data_list):
    """
    合并list
    :param bubbleOption_data_30: 30天原始数据
    :param data_list: 需要合并的数据列表
    :return:
    """
    merge_data = data_list
    data_index_list = [data[0] for data in data_list]

    for k, v in enumerate(bubbleOption_data_30):
        if k not in data_index_list:
            merge_data.append(v)
    return merge_data
