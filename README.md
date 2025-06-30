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
$ python3 infer.py --hf_model InternVL2_5-1B-MPO/ --axmodel_path InternVL2_5-1B-MPO_axmodel/ -q "我输入了几幅图? 内容是什么?" -i examples/image_0.jpg examples/image_1.jpg examples/image_2.png examples/image_3.png --vit_model vit_axmodel/internvl2_5_1b_mpo_vit.axmodel
```

此模型最多支持 `4` 幅图像作为输入:

![image_0.jpg](python/examples/image_0.jpg)

![image_1.jpg](python/examples/image_1.jpg)

![image_2.png](python/examples/image_2.png)

![image_3.png](python/examples/image_3.png)

模型推理结果如下:

```bash
python3 infer.py --hf_model InternVL2_5-1B-MPO/ --axmodel_path InternVL2_5-1B-MPO_axmodel/ -q "我输入了几幅图? 内容是什么?" -i examples/image_0.jpg examples/image_1.jpg examples/image_2.png examples/image_3.png --vit_model vit_axmodel/internvl2_5_1b_mpo_vit.axmodel

prefill token_len:  1119
slice_indexs is [0, 1, 2, 3, 4, 5, 6, 7, 8]
slice prefill done 0
slice prefill done 1
slice prefill done 2
slice prefill done 3
slice prefill done 4
slice prefill done 5
slice prefill done 6
slice prefill done 7
slice prefill done 8
answer >>

1. **红熊猫**: 图片中是一只红熊猫，它有着鲜艳的红棕色毛发，黑色的面部和白色的胡须，正趴在木头上，背景是绿色的树木和植物。

2. **大熊猫**: 图片中是一只大熊猫，它有着黑白相间的毛发，黑色的耳朵和四肢，以及白色的面部和鼻子，正在竹子间休息，背景是绿色的植被。

3. **宇航员**: 图片中有三名宇航员，他们穿着白色的宇航服，戴着头盔，站在一片森林中，背景是高大的树木和植物，环境显得神秘而宁静。

4. **少女**: 图片中是一位少女，她有着银色的长发，戴着粉色的花朵发饰，穿着蓝色的连衣裙，背景是海滩和海洋，天空晴朗，海浪轻拍沙滩。

^@这些图片展示了不同的动物和场景，从自然到科幻，从宁静到神秘。
Inference done!
```

输入以下命令执行**视频理解**任务:

```sh
$ cd InternVL2_5-1B-MPO.axera/python
$ python3 infer.py --hf_model InternVL2_5-1B-MPO/ --axmodel_path InternVL2_5-1B-MPO_axmodel/ -q "请描述这个视频" --vit_model vit_axmodel/internvl2_5_1b_mpo_vit.axmodel -v red-panda.mp4
```

模型输入:



https://github.com/user-attachments/assets/2beffc73-d078-4c54-8282-7b7d845f39c9



模型推理结果如下:

```bash
ai@ai-bj ~/yongqiang/InternVL2_5-1B-MPO.axera/python $ python3 infer.py --hf_model InternVL2_5-1B-MPO/ --axmodel_path InternVL2_5-1B-MPO_axmodel/ -q "请描述这个视频" --vit_model vit_axmodel/internvl2_5_1b_mpo_vit.axmodel -v red-panda.mp4

prefill token_len:  1104
slice_indexs is [0, 1, 2, 3, 4, 5, 6, 7, 8]
slice prefill done 0
slice prefill done 1
slice prefill done 2
slice prefill done 3
slice prefill done 4
slice prefill done 5
slice prefill done 6
slice prefill done 7
slice prefill done 8
answer >> 视频显示一只红熊猫在一个被木屑覆盖的户外环境中活动。红熊猫在木屑铺成的地面上行走，周围有绿色植物和一些木制结构。在视频的开始，红熊猫在左侧的树丛附近活动，然后向右侧移动。随着红熊猫继续行走，可以看到它经过了一些大石头和木制的围栏。背景中有一些木制的小屋和树木，环境看起来像是一个动物园或野生动物保护区。阳光透过树叶洒在地面上，给场景增添了一种温暖的氛围。红熊猫看起来很自在，没有受到限制^@地在环境中移动。
Inference done!
```

#### 图像/视频理解任务·推理耗时统计

Chips | Image num | ImageEncoder (448x448) | Prefill TTFT | Decoder | w8a16
---| ---| ---| ---| ---| ---|
AX650N | 0 | 0 ms | 94.615 ms (128 tokens) | 29.721 | 33.64 tokens/sec
AX650N | 1 | 364.870 ms | 381.775 ms (384 tokens) | 29.721 | 33.64 tokens/sec
AX650N | 4 | 1460 ms | 2175.631 ms (1152 tokens) | 29.721 | 33.64 tokens/sec

备注: 128 chunk prefill 推理, decode layer 耗时 22.49 ms, post 耗时 7.231 ms.

decode 阶段只有一个子图, 耗时如下:

```sh
g0: 0.937 ms
```

prefill 各子图耗时:

```sh
g1: 3.641 ms
g2: 5.113 ms
g3: 6.852 ms
g4: 8.273 ms
g5: 10.062 ms
g6: 11.714 ms
g7: 13.487 ms
g8: 14.727 ms
g9: 16.481 ms
```

post 耗时:

```sh
g0: 7.231 ms
```

在**单幅图像**推理时, prefil TTFT 为: (g1 + g2 + g3) * 28 + 11.455 = 30.387 * 28 + 11.455 = 862.291 ms.

在**四幅图像**推理时 (视频理解是四帧输入), prefil TTFT 为: (g1 + ··· + g9) * 28 + 11.455 = 163.476 * 28 + 11.455 = 4588.79 ms.

模型解码速度为: 1000 / 29.721 ms = 33.64 tokens/s.


## 技术讨论

- Github issues
- QQ 群: 139953715
