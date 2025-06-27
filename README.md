# InternVL2_5-1B-MPO.axera

> Deepseek InternVL2_5-1B-MPO DEMO on Axera.

- 目前支持 `Python` 语言, `C++` 代码在开发中.
- 预编译模型可以从 [百度网盘](https://pan.baidu.com/s/1s2ihzQXfbtDdW7rDsKzooA?pwd=fjjr) 下载.
- 如需自行导出编译 `VIT` 模型请参考 [模型转换](/model_convert/README.md).

## 支持平台

- [x] AX650N
- [ ] AX630C

## Git Clone

首先使用如下命令 `clone` 本项目, 然后进入 `python` 文件夹:

```bash
$ git clone git@github.com:AXERA-TECH/InternVL2_5-1B-MPO.axera.git
$ cd InternVL2_5-1B-MPO.axera/python
```

之后在开发板上下载或安装以下支持库:

- 从 `huggingface` 下载 `InternVL2_5-1B-MPO` 模型.

    ```bash
    $ git clone https://huggingface.co/OpenGVLab/InternVL2_5-1B-MPO
    ```

- 在开发板上安装配置 `pyaxengine`, [点击跳转下载链接](https://github.com/AXERA-TECH/pyaxengine/releases). 注意板端 `SDK` 最低版本要求:

    - AX650 SDK >= 2.18
    - AX620E SDK >= 3.12
    - 执行 `pip3 install axengine-x.x.x-py3-none-any.whl` 安装

- 手动编译安装 `decord` 视频库 (如果不需要视频推理, 可不安装), 安装请参考 [decord-install-linux](https://github.com/dmlc/decord?tab=readme-ov-file#linux).

将下载后的预编译模型解压到当前文件夹[🔔可选], 默认文件夹排布如下:

```bash
$ tree -L 2 .
.
├── examples
│   ├── image_0.jpg
│   ├── image_1.jpg
│   ├── image_2.png
│   ├── image_3.png
│   ├── laorenshuaidao.mp4
│   ├── red-panda.mp4
│   └── tuboshu.mp4
├── infer.py
├── infer_video.py
├── InternVL2_5-1B-MPO
│   ├── added_tokens.json
│   ├── config.json
│   ├── configuration_intern_vit.py
│   ├── configuration_internvl_chat.py
│   ├── conversation.py
│   ├── examples
│   ├── generation_config.json
│   ├── merges.txt
│   ├── modeling_intern_vit.py
│   ├── modeling_internvl_chat.py
│   ├── model.safetensors
│   ├── preprocessor_config.json
│   ├── README.md
│   ├── runs
│   ├── special_tokens_map.json
│   ├── tokenizer_config.json
│   └── vocab.json
├── InternVL2_5-1B-MPO_axmodel
│   ├── model.embed_tokens.weight.bfloat16.bin
│   ├── model.embed_tokens.weight.float32.bin
│   ├── model.embed_tokens.weight.npy
│   ├── qwen2_p128_l0_together.axmodel
│   ├── qwen2_p128_l10_together.axmodel
│   ├── qwen2_p128_l11_together.axmodel
│   ├── qwen2_p128_l12_together.axmodel
│   ├── qwen2_p128_l13_together.axmodel
│   ├── qwen2_p128_l14_together.axmodel
│   ├── qwen2_p128_l15_together.axmodel
│   ├── qwen2_p128_l16_together.axmodel
│   ├── qwen2_p128_l17_together.axmodel
│   ├── qwen2_p128_l18_together.axmodel
│   ├── qwen2_p128_l19_together.axmodel
│   ├── qwen2_p128_l1_together.axmodel
│   ├── qwen2_p128_l20_together.axmodel
│   ├── qwen2_p128_l21_together.axmodel
│   ├── qwen2_p128_l22_together.axmodel
│   ├── qwen2_p128_l23_together.axmodel
│   ├── qwen2_p128_l2_together.axmodel
│   ├── qwen2_p128_l3_together.axmodel
│   ├── qwen2_p128_l4_together.axmodel
│   ├── qwen2_p128_l5_together.axmodel
│   ├── qwen2_p128_l6_together.axmodel
│   ├── qwen2_p128_l7_together.axmodel
│   ├── qwen2_p128_l8_together.axmodel
│   ├── qwen2_p128_l9_together.axmodel
│   └── qwen2_post.axmodel
├── red-panda.mp4
├── requirements.txt
├── torch_infer.py
└── vit_axmodel
    └── internvl3_2b_vit_slim.axmodel

6 directories, 56 files
```

## 模型转换

关于 `onnx` 和 `axmodel` 的导出、编译参见 [模型转换](./model_convert/README.md) 部分内容.

## 上板部署

- `AX650N` 的设备已预装 `Ubuntu 22.04`
- 以 `root` 权限登陆 `AX650N` 的板卡设备
- 接入互联网, 确保 `AX650N` 的设备能正常执行 `apt install`, `pip install` 等指令
- 已验证设备: `AX650N DEMO Board`、`爱芯派Pro(AX650N)`

### Python API 运行

#### Requirements

```bash
$ mkdir /opt/site-packages
$ cd python
$ pip3 install -r requirements.txt --prefix=/opt/site-packages
``` 

#### 添加环境变量

将以下两行添加到 `/root/.bashrc`(实际添加的路径需要自行检查)后, 重新连接终端或者执行 `source ~/.bashrc`

```bash
$ export PYTHONPATH=$PYTHONPATH:/opt/site-packages/local/lib/python3.10/dist-packages  
$ export PATH=$PATH:/opt/site-packages/local/bin
``` 

#### 运行

在 `Axera 开发板` 上运行以下命令开始聊天对话:

```sh
$ cd InternVL2_5-1B-MPO.axera/python
$ python3 infer.py --hf_model InternVL2_5-1B-MPO/ --axmodel_path InternVL2_5-1B-MPO_axmodel/ --question "请计算函数[y=2x^2+2]的导数, 并提供 markdown 格式的推理过程"
```

输出结果如下:

```bash
$ python3 infer.py -q "请你计算函数 y=3x^2+2 的导数, 给出简要的计算过程."
[INFO] Available providers:  ['AXCLRTExecutionProvider']

...

answer >> : 计算函数 y=3x^2+2 的导数需要用到基本的微积分知识，特别是求导法则。对于多项式函数，我们使用的是链式法则或者直接应用乘积法则。对于二次函数，如 y=3x^2+2，其导数可以通过求导法则直接计算。

对于 y=3x^2+2，我们首先注意到这是一个二次函数，其一般形式为 f(x)=ax^2+bx+c，其中 a=3, b=0, c=2。

对于二次函数，其导数 f'(x) = 2ax + b，因为二次函数的导数是二次项的系数。

所以，对于 y=3x^2+2，其导数 f'(x) = 6x。

简要计算过程如下：

1. 首先，我们识别出函数^@ y=3x^2+2 是一个二次函数，其一般形式为 f(x)=ax^2+bx+c。

2. 其次，我们应用二次函数的导数公式 f'(x) = 2ax + b，其中 a=3, b=0, c=2。

3. 最后，将 a 和 b 的值代入公式中，得到 f'(x) = 6x。

因此，函数 y=3x^2+2 的导数是 6x。
Inference done!
```

输入以下命令执行图像理解任务:

```sh
$ cd InternVL2_5-1B-MPO.axera/python
$ python3 infer.py --hf_model InternVL2_5-1B-MPO/ --axmodel_path InternVL2_5-1B-MPO_axmodel/ -q "请分别描述这几幅图像的内容, 并找出它们的异同点" -i examples/image_0.jpg examples/image_1.jpg examples/image_2.png examples/image_3.png
```

此模型最多支持 `4` 幅图像作为输入:

![image_0.jpg](python/examples/image_0.jpg)

![image_1.jpg](python/examples/image_1.jpg)

![image_2.png](python/examples/image_2.png)

![image_3.png](python/examples/image_3.png)

模型推理结果如下:

```bash
None
```

输入以下命令执行**视频理解**任务:

```sh
$ cd InternVL2_5-1B-MPO.axera/python
$ python3 infer_video.py --hf_model InternVL2_5-1B-MPO/ --axmodel_path InternVL2_5-1B-MPO_axmodel_2048/ --vit_model vit_axmodel/internvl3_2b_vit_slim.axmodel -q "请描述这个视频" -i examples/red-panda.mp4
```

模型输入:



https://github.com/user-attachments/assets/2beffc73-d078-4c54-8282-7b7d845f39c9



模型推理结果如下:

```bash
None
```

#### 图像/视频理解任务·推理耗时统计

Chips | Image num | ImageEncoder (448x448) | Prefill TTFT | Decoder | w8a16
---| ---| ---| ---| ---| ---|
AX650N | 0 | 0 ms | 220.979 ms (128 tokens) | 86.969 ms | 11.50 tokens/sec
AX650N | 1 | 364.870 ms | 862.291 ms (384 tokens) | 86.969 ms | 11.50 tokens/sec
AX650N | 4 | 1460 ms | 4588.79 ms (1152 tokens) | 86.969 ms | 11.50 tokens/sec
AX650N | 8 | 2920 ms | 13904.383 ms (2176 tokens) | 86.969 ms | 11.50 tokens/sec

备注: 128 chunk prefill 推理, decode layer 耗时 2.686 ms * 28, post 耗时 11.455 ms.

该模型 prefill 阶段存在 17 个可用子图, 每个子图耗时如下:

```
g1: 7.483 ms
g2: 10.089 ms
g3: 12.815 ms
g4: 15.235 ms
g5: 18.527 ms
g6: 20.751 ms
g7: 23.520 ms
g8: 25.932 ms
g9: 29.124 ms
g10: 31.727 ms
g11: 34.708 ms
g12: 36.982 ms
g13: 39.950 ms
g14: 42.418 ms
g15: 45.933 ms
g16: 48.577 ms
g17: 52.405 ms
```

decode 阶段只有一个子图, 耗时如下:

```
g0: 2.664 ms
```

在**单幅图像**推理时, prefil TTFT 为: (g1 + g2 + g3) * 28 + 11.455 = 30.387 * 28 + 11.455 = 862.291 ms.

在**四幅图像**推理时, prefil TTFT 为: (g1 + ··· + g9) * 28 + 11.455 = 163.476 * 28 + 11.455 = 4588.79 ms.

在**视频推理**时, prefil TTFT 为: (g1 + ··· + g17) * 28 + 11.455 = 496.176 * 28 + 11.455 = 13904.383 ms.

模型解码速度为: 1000 / 86.969 ms = 11.50 tokens/s.

---

固定 320 prefill 推理, prefill 每一层耗时 28.258 ms, 一共 28 层, decode 耗时 2.510 ms, post 耗时 11.761 ms.

## 技术讨论

- Github issues
- QQ 群: 139953715
