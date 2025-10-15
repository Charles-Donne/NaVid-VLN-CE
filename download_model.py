from huggingface_hub import hf_hub_download

# 下载模型文件
model_path = hf_hub_download(
    repo_id="Jzzhang/NaVid",
    filename="navid-7b-full-224-video-fps-1-grid-2-r2r-rxr-training-split",
    local_dir="model_zoo",
    local_dir_use_symlinks=False
)

print(f"模型已下载到: {model_path}")
