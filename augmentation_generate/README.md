# Để chạy được data_augmentation_Gemini_5_voting_models thì có các bước sau: 

## Chạy được COMET
- Vào tài khoản Hugging Face để accept license agreement: 
https://huggingface.co/Unbabel/wmt22-comet-da
https://huggingface.co/Unbabel/wmt22-cometkiwi-da

- Sau đó mở terminal và chạy lệnh:
```bash
huggingface-cli login
```

- Đăng nhập vào tài khoản Hugging Face, ở bước nhập API key thì copy API key của tài khoản mình (chỉ cần READ API key) từ trang Hugging Face và paste vào terminal.

- Cần cài đặt các package sau:
```bash
pip install --upgrade pip  # ensures that pip is current 
pip install "unbabel-comet>=2.0.0"
```

## Chạy được BERTScore
- pip install bert-score

## Sau đó hãy cầu nguyện cho máy đủ mạnh để chạy cả 5 models, chúc các bạn may mắn!
