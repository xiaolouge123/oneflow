import os
from collections import OrderedDict

import numpy as np
import oneflow as flow
import tensorflow as tf
import test_global_storage
from test_util import GenArgList

gpus = tf.config.experimental.list_physical_devices("GPU")
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)


def compare_with_tensorflow(device_type, data_type, x_shape, case):
    assert device_type in ["gpu", "cpu"]
    flow.clear_default_session()
    func_config = flow.FunctionConfig()
    func_config.default_data_type(flow.float)
    func_config.train.primary_lr(1e-4)
    func_config.train.model_update_conf(dict(naive_conf={}))

    @flow.function(func_config)
    def ScalarAddByTensorJob():
        with flow.device_prior_placement(device_type, "0:0"):
            x = flow.get_variable(
                "x",
                shape=x_shape,
                dtype=flow.float,
                initializer=flow.random_uniform_initializer(minval=0, maxval=100),
                trainable=True,
            )
            y = flow.get_variable(
                "y",
                shape=(1,),
                dtype=flow.float,
                initializer=flow.random_uniform_initializer(minval=0, maxval=100),
                trainable=True,
            )
            if case == "add":
                loss = flow.math.add(x, y)
            elif case == "sub":
                loss = flow.math.subtract(x, y)
            elif case == "mul":
                loss = flow.math.multiply(x, y)
            elif case == "div":
                loss = flow.math.divide(x, y)
            flow.losses.add_loss(loss)

            flow.watch(x, test_global_storage.Setter("x"))
            flow.watch(y, test_global_storage.Setter("y"))
            flow.watch_diff(x, test_global_storage.Setter("x_diff"))
            flow.watch_diff(y, test_global_storage.Setter("y_diff"))
            flow.watch(loss, test_global_storage.Setter("loss"))
            flow.watch_diff(loss, test_global_storage.Setter("loss_diff"))

            return loss

    # OneFlow
    check_point = flow.train.CheckPoint()
    check_point.init()
    of_out = ScalarAddByTensorJob().get()
    # TensorFlow
    with tf.GradientTape(persistent=True) as tape:
        x = tf.Variable(test_global_storage.Get("x"))
        y = tf.Variable(test_global_storage.Get("y"))
        if case == "add":
            tf_out = x + y
        elif case == "sub":
            tf_out = x - y
        elif case == "mul":
            tf_out = x * y
        elif case == "div":
            tf_out = x / y
    loss_diff = test_global_storage.Get("loss_diff")
    tf_x_diff = tape.gradient(tf_out, x, loss_diff)
    tf_y_diff = tape.gradient(tf_out, y, loss_diff)

    assert np.allclose(of_out.ndarray(), tf_out.numpy(), rtol=1e-5, atol=1e-5)
    assert np.allclose(
        test_global_storage.Get("x_diff"), tf_x_diff.numpy(), rtol=1e-5, atol=1e-5
    )
    assert np.allclose(
        test_global_storage.Get("y_diff"), tf_y_diff.numpy(), rtol=1e-5, atol=1e-5
    )


def test_add(test_case):
    arg_dict = OrderedDict()
    arg_dict["device_type"] = ["gpu"]
    arg_dict["data_type"] = [flow.float]
    arg_dict["x_shape"] = [(10, 20, 30)]
    arg_dict["case"] = ["add"]
    for arg in GenArgList(arg_dict):
        compare_with_tensorflow(*arg)


def test_sub(test_case):
    arg_dict = OrderedDict()
    arg_dict["device_type"] = ["gpu"]
    arg_dict["data_type"] = [flow.float]
    arg_dict["x_shape"] = [(10, 20, 30)]
    arg_dict["case"] = ["sub"]
    for arg in GenArgList(arg_dict):
        compare_with_tensorflow(*arg)


def test_mul(test_case):
    arg_dict = OrderedDict()
    arg_dict["device_type"] = ["gpu"]
    arg_dict["data_type"] = [flow.float]
    arg_dict["x_shape"] = [(10, 20, 30)]
    arg_dict["case"] = ["mul"]
    for arg in GenArgList(arg_dict):
        compare_with_tensorflow(*arg)


def test_div(test_case):
    arg_dict = OrderedDict()
    arg_dict["device_type"] = ["gpu"]
    arg_dict["data_type"] = [flow.float]
    arg_dict["x_shape"] = [(10, 20, 30)]
    arg_dict["case"] = ["div"]
    for arg in GenArgList(arg_dict):
        compare_with_tensorflow(*arg)
