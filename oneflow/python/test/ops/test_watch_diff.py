"""
Copyright 2020 The OneFlow Authors. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
from collections import OrderedDict

import numpy as np
import oneflow as flow
import tensorflow as tf
import test_global_storage
from test_util import GenArgList, type_name_to_flow_type, type_name_to_np_type


def WatchDiff(test_case, device_type, input_shape, dtype):
    assert device_type in ["gpu", "cpu"]
    assert dtype in ["float32", "double"]
    flow.clear_default_session()

    func_config = flow.FunctionConfig()
    func_config.default_data_type(flow.float)
    func_config.train.primary_lr(1e-4)
    func_config.train.model_update_conf(dict(naive_conf={}))

    def CheckOnes(diff):
        ones = np.ones(input_shape)
        test_case.assertTrue(np.allclose(diff.numpy(), ones, rtol=1e-5, atol=1e-5))

    @flow.global_function(func_config)
    def TrainJob():
        with flow.scope.placement(device_type, "0:0"):
            x = flow.get_variable(
                "in",
                shape=input_shape,
                dtype=type_name_to_flow_type[dtype],
                initializer=flow.random_uniform_initializer(),
                trainable=True,
            )
            flow.watch_diff(x, CheckOnes)
            flow.losses.add_loss(x)

    check_point = flow.train.CheckPoint()
    check_point.init()
    TrainJob()


def test_watch_diff(test_case):
    arg_dict = OrderedDict()
    arg_dict["device_type"] = ["gpu", "cpu"]
    arg_dict["input_shape"] = [(10,)]
    arg_dict["dtype"] = ["float32"]
    for arg in GenArgList(arg_dict):
        WatchDiff(test_case, *arg)