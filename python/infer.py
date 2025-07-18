# import llm_utils
import dataclasses
import json
from decord import VideoReader, cpu
from transformers import AutoTokenizer, AutoConfig
import torch
from torchvision.transforms.functional import InterpolationMode
import numpy as np
from ml_dtypes import bfloat16
from axengine import InferenceSession
from tqdm import tqdm
import torchvision.transforms as T
from PIL import Image
import argparse


"""
pulsar2 llm_build \
    --input_path ./InternVL2_5-1B-MPO   \
    --output_path ./InternVL2_5-1B-MPO_axmodel \
    --hidden_state_type bf16 \
    --prefill_len 128 \
    --last_kv_cache_len 128 \
    --last_kv_cache_len 256 \
    --last_kv_cache_len 384 \
    --last_kv_cache_len 512 \
    --last_kv_cache_len 640 \
    --last_kv_cache_len 768 \
    --last_kv_cache_len 896 \
    --last_kv_cache_len 1024 \
    --kv_cache_len 2559 \
    --chip AX650 -c 1 --parallel 28

最多支持 4 幅图像输入; 支持文本对话;
"""

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

def build_transform(input_size):
    MEAN, STD = IMAGENET_MEAN, IMAGENET_STD
    transform = T.Compose([
        T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=MEAN, std=STD)
    ])
    return transform

def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_ratio_diff = float('inf')
    best_ratio = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio

def dynamic_preprocess(image, min_num=1, max_num=12, image_size=448, use_thumbnail=False):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # calculate the existing image aspect ratio
    target_ratios = set(
        (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
        i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    # find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, target_ratios, orig_width, orig_height, image_size)

    # calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        )
        # split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images

def load_image(image_file, input_size=448, max_num=12):
    image = Image.open(image_file).convert('RGB')
    transform = build_transform(input_size=input_size)
    images = dynamic_preprocess(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
    pixel_values = [transform(image) for image in images]
    pixel_values = torch.stack(pixel_values)
    return pixel_values

def post_process(data, topk=1, topp=0.9, temperature=0.6):
    def top_p(l: np.ndarray, p: float) -> np.ndarray:
        index = np.argsort(l)
        res = l.copy()
        sum_p = 0
        for i in index[::-1]:
            if sum_p >= p:
                res[i] = 0
            sum_p += res[i]
        return res / sum_p

    def softmax(l: np.ndarray) -> np.ndarray:
        l_max = l - l.max()
        l_exp = np.exp(l_max)
        res = l_exp / np.sum(l_exp)
        return res.astype(np.float64)

    r = data.astype(np.float32)
    r = r.flatten()
    # topk
    candidate_index = np.argpartition(r, -topk)[-topk:]
    candidate_value = r[candidate_index]
    # temperature
    candidate_value /= temperature
    # softmax
    candidate_soft = softmax(candidate_value)
    # topp
    candidate_soft = top_p(candidate_soft, topp)
    candidate_soft = candidate_soft.astype(np.float64) / candidate_soft.sum()
    pos = np.random.multinomial(1, candidate_soft).argmax()
    next_token = candidate_index[pos]
    return next_token, candidate_index, candidate_soft


def get_index(bound, fps, max_frame, first_idx=0, num_segments=32):
    if bound:
        start, end = bound[0], bound[1]
    else:
        start, end = -100000, 100000
    start_idx = max(first_idx, round(start * fps))
    end_idx = min(round(end * fps), max_frame)
    seg_size = float(end_idx - start_idx) / num_segments
    frame_indices = np.array([
        int(start_idx + (seg_size / 2) + np.round(seg_size * idx))
        for idx in range(num_segments)
    ])
    return frame_indices


def load_video(video_path, bound=None, input_size=448, max_num=1, num_segments=32):
    vr = VideoReader(video_path, ctx=cpu(0), num_threads=1)
    max_frame = len(vr) - 1
    fps = float(vr.get_avg_fps())

    pixel_values_list, num_patches_list = [], []
    transform = build_transform(input_size=input_size)
    frame_indices = get_index(bound, fps, max_frame, first_idx=0, num_segments=num_segments)
    for frame_index in frame_indices:
        img = Image.fromarray(vr[frame_index].asnumpy()).convert('RGB')
        img = dynamic_preprocess(img, image_size=input_size, use_thumbnail=True, max_num=max_num)
        pixel_values = [transform(tile) for tile in img]
        pixel_values = torch.stack(pixel_values)
        num_patches_list.append(pixel_values.shape[0])
        pixel_values_list.append(pixel_values)
    pixel_values = torch.cat(pixel_values_list)
    return pixel_values, num_patches_list


if __name__ == "__main__":

    prompt = None
    parser = argparse.ArgumentParser(description="Model configuration parameters")
    parser.add_argument("--hf_model", type=str, default="./InternVL2_5-1B-MPO",
                        help="Path to HuggingFace model")
    parser.add_argument("--axmodel_path", type=str, default="./InternVL2_5-1B-MPO_axmodel",
                        help="Path to save compiled axmodel of llama model")
    parser.add_argument("--vit_model", type=str, default=None,
                        help="Path to save compiled axmodel of llama model")
    parser.add_argument("-i", "--images", nargs='+', type=str, default=None,
                        help="Path to the test image.")
    parser.add_argument("-v", "--video", type=str, default=None,
                        help="Path to the test video.")
    parser.add_argument("--segments", type=int, default=4,
                        help="Number of segments to split the video into.") # TODO
    parser.add_argument("-q", "--question", type=str, default="Please calculate the derivative of the function y=2x^2+3.",
                        help="Your question that you want to ask the model.")
    args = parser.parse_args()


    hf_model_path = args.hf_model
    axmodel_path = args.axmodel_path
    vit_axmodel_path = args.vit_model
    test_imgs_path = args.images
    test_video_path = args.video
    segments = args.segments
    is_video = True if test_video_path is not None else False

    config = AutoConfig.from_pretrained(hf_model_path, trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained(hf_model_path, trust_remote_code=True, use_fast=False)
    # set the max number of tiles in `max_num`

    if not is_video:
        pixel_values_list = []
        if test_imgs_path is not None:
            for img_path in test_imgs_path:
                pixel_values = load_image(img_path, input_size=448, max_num=1)
                pixel_values_list.append(pixel_values)
            print(f"输入图像数: {len(pixel_values_list)}")
            print("preprocess image done!")

            # extract img feature by vit
            vit_session = InferenceSession(vit_axmodel_path)
            vit_output_list = []
            for idx, pixel_values in enumerate(pixel_values_list):
                vit_output = vit_session.run(None, {"image": pixel_values.numpy()})[0]
                vit_output_list.append(vit_output.copy()) # 避免 vit 输出结果使用同一块内存

            print(f"vit_output.shape is {vit_output_list[0].shape}, vit feature extract done!")

        prompt = "<|im_start|>system\n你是由上海人工智能实验室联合商汤科技开发的书生多模态大模型, 英文名叫 InternVL2_5-1B-MPO, 是一个有用无害的人工智能助手, 擅长思考和回答用户的问题. 请你在回答问题时使用简体中文.<|im_end|>\n"
        question = args.question
        prompt += "<|im_start|>user\n" + question

        if len(pixel_values_list) > 0:
            for idx in range(len(pixel_values_list)):
                prompt += "\n<img>" + "<IMG_CONTEXT>" * 256 + "</img>\n"

        prompt += "<|im_end|>\n<|im_start|>assistant"
    else:
        # raise NotImplementedError("Video inference is not implemented yet.")
        pixel_values, num_patches_list = load_video(test_video_path, num_segments=args.segments, max_num=1)
        # Frame1: <image>\nFrame2: <image>\n...\nFrame8: <image>\n{question}

        pixel_values_list = [e[None, ...] for e in pixel_values]
        if pixel_values_list is not None:
            print(f"输入帧数: {len(pixel_values_list)}")
            print("preprocess image done!")

            # extract img feature by vit
            vit_session = InferenceSession(vit_axmodel_path)
            vit_output_list = []
            for idx, pixel_values in enumerate(pixel_values_list):
                vit_output = vit_session.run(None, {"image": pixel_values.numpy()})[0]
                vit_output_list.append(vit_output.copy()) # 避免 vit 输出结果使用同一块内存

            print(f"vit_output.shape is {vit_output_list[0].shape}, vit feature extract done!")

        question = args.question
        prompt = "<|im_start|>system\n你是书生·万象, 英文名是InternVL, 是由上海人工智能实验室、清华大学及多家合作单位联合开发的多模态大语言模型.<|im_end|>\n"
        prompt += "<|im_start|>user"

        if len(pixel_values_list) > 0:
            for idx in range(len(pixel_values_list)):
                prompt += f"\nFrame{idx+1}: <img>" + "<IMG_CONTEXT>" * 256 + "</img>\n"

        prompt += f"\n{question}<|im_end|>\n<|im_start|>assistant\n"

    # print(f"prompt is {prompt}")
    token_ids = tokenizer.encode(prompt)

    # 图像理解
    image_start_indices = np.where(np.array(token_ids) == 151665)[0].tolist() # <img> tag
    embeds = np.load(f"{axmodel_path}/model.embed_tokens.weight.npy")
    prefill_data = np.take(embeds, token_ids, axis=0)
    prefill_data = prefill_data.astype(bfloat16)
    token_len = len(token_ids)

    assert token_len < 1024 + 128, f"输入 prompt({token_len}) 超过最大限度!"
    for idx, image_start_index in enumerate(image_start_indices):
        image_insert_index = image_start_index + 1
        prefill_data[image_insert_index : image_insert_index + 256] = vit_output_list[idx][0, :, :]
    ##################################

    lastN = 2559
    cfg = config.llm_config
    # cfg = config
    # cfg.num_hidden_layers = 24

    kv_dim = cfg.hidden_size // cfg.num_attention_heads * cfg.num_key_value_heads
    k_caches = [
        np.zeros((1, lastN, kv_dim), dtype=bfloat16)
        for _ in range(cfg.num_hidden_layers)
    ]
    v_caches = [
        np.zeros((1, lastN, kv_dim), dtype=bfloat16)
        for _ in range(cfg.num_hidden_layers)
    ]

    prefill_decoder_sessins = []
    for i in tqdm(range(cfg.num_hidden_layers), desc="Init InferenceSession"):
        session = InferenceSession(
            f"{axmodel_path}/qwen2_p128_l{i}_together.axmodel"
        )
        prefill_decoder_sessins.append(session)

    post_process_session = InferenceSession(
        f"{axmodel_path}/qwen2_post.axmodel"
    )
    print("model load done!")
    print("prefill token_len: ", token_len)

    """
        prefill
    """
    prefill_slice_len = 128
    # slice_indexs = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    slice_indexs = [
        e for e in range(token_len // prefill_slice_len + 1)
    ]
    print(f"slice_indexs is {slice_indexs}")
    prefill_len = prefill_slice_len * slice_indexs[-1] if slice_indexs[-1] != 0 else prefill_slice_len # 这里的 128 就是 prefill_slice_len

    if prefill_len > 0:
        for slice_index in slice_indexs:
            indices = np.array(
                list(
                    range(
                        slice_index * prefill_slice_len,
                        (slice_index + 1) * prefill_slice_len,
                    )
                ),
                np.uint32,
            ).reshape((1, prefill_slice_len))

            mask = (
                np.zeros((1, prefill_slice_len, prefill_slice_len * (slice_index + 1)))
                - 65536
            )
            data = np.zeros((1, prefill_slice_len, cfg.hidden_size)).astype(bfloat16)
            for i, t in enumerate(
                range(
                    slice_index * prefill_slice_len,
                    (slice_index + 1) * prefill_slice_len,
                )
            ):
                if t < len(token_ids):
                    mask[:, i, : slice_index * prefill_slice_len + i + 1] = 0
                    data[:, i : i + 1, :] = (
                        prefill_data[t]
                        .reshape((1, 1, cfg.hidden_size))
                        .astype(bfloat16)
                    )

            if slice_index == slice_indexs[-1]:
                remain_len = token_len - slice_index * prefill_slice_len
            else:
                remain_len = prefill_slice_len
            mask = mask.astype(bfloat16)
            for i in range(cfg.num_hidden_layers):
                input_feed = {
                    "K_cache": (
                        k_caches[i][:, 0 : prefill_slice_len * slice_index, :]
                        if slice_index
                        else np.zeros((1, 1, cfg.hidden_size), dtype=bfloat16)
                    ),
                    "V_cache": (
                        v_caches[i][:, 0 : prefill_slice_len * slice_index, :]
                        if slice_index
                        else np.zeros((1, 1, cfg.hidden_size), dtype=bfloat16)
                    ),
                    "indices": indices,
                    "input": data,
                    "mask": mask,
                }
                outputs = prefill_decoder_sessins[i].run(None, input_feed, shape_group=slice_index + 1)
                k_caches[i][
                    :,
                    slice_index
                    * prefill_slice_len : slice_index
                    * prefill_slice_len + remain_len,
                    :,
                ] = outputs[0][:, :remain_len, :]
                v_caches[i][
                    :,
                    slice_index
                    * prefill_slice_len : slice_index
                    * prefill_slice_len + remain_len,
                    :,
                ] = outputs[1][:, :remain_len, :]
                data = outputs[2]

            print("slice prefill done", slice_index)
        post_out = post_process_session.run(
            None,
            {
                "input": data[
                    :, token_len - (len(slice_indexs) - 1) * prefill_slice_len - 1, None, :
                ]
            }
        )[0]
        next_token, posssible_tokens, possible_soft = post_process(post_out)
        posibles = [tokenizer.decode([t]) for t in posssible_tokens]
        posible_soft = [str((t, s)) for t, s in zip(posibles, possible_soft)]
        token_ids.append(next_token)

    print("answer >>", tokenizer.decode(next_token, skip_special_tokens=True), end='', flush=True)
    # set to decoder
    kv_cache_len = 2559
    mask = np.zeros((1, 1, kv_cache_len + 1), dtype=np.float32).astype(bfloat16)
    mask[:, :, :kv_cache_len] -= 65536
    if prefill_len > 0:
        mask[:, :, :token_len] = 0
    for start_indice in range(kv_cache_len):
        if prefill_len > 0 and start_indice < token_len:
            continue

        next_token = token_ids[start_indice]
        indices = np.array([start_indice], np.uint32).reshape((1, 1))
        data = embeds[next_token, :].reshape((1, 1, cfg.hidden_size)).astype(bfloat16)
        for i in range(cfg.num_hidden_layers):
            input_feed = {
                "K_cache": k_caches[i],
                "V_cache": v_caches[i],
                "indices": indices,
                "input": data,
                "mask": mask,
            }
            outputs = prefill_decoder_sessins[i].run(None, input_feed, shape_group=0)
            k_caches[i][:, start_indice, :] = outputs[0][:, :, :]
            v_caches[i][:, start_indice, :] = outputs[1][:, :, :]
            data = outputs[2]
        mask[..., start_indice] = 0
        if start_indice < token_len - 1:
            pass
        else:
            post_out = post_process_session.run(None, {"input": data})[0]
            next_token, posssible_tokens, possible_soft = post_process(post_out)
            token_ids.append(next_token)
            if next_token == tokenizer.eos_token_id and next_token > token_len:
                break
        print(tokenizer.decode(next_token, skip_special_tokens=True), end='', flush=True)
    print("\nInference done!")

