import streamlit as st
import boto3
import json
from PIL import Image
import io
import base64
import time
import os
from moviepy.editor import ImageSequenceClip

# 设置页面配置
st.set_page_config(
    page_title="AI 创作助手",
    page_icon="🎨",
    layout="wide"
)

# 初始化 AWS 客户端
bedrock = boto3.client('bedrock-runtime')
translate = boto3.client('translate')

def translate_to_english(text):
    """使用 AWS Translate 将文本翻译为英文"""
    try:
        response = translate.translate_text(
            Text=text,
            SourceLanguageCode='auto',
            TargetLanguageCode='en'
        )
        return response['TranslatedText']
    except Exception as e:
        st.error(f"翻译时出错: {str(e)}")
        return None

def optimize_prompt(prompt):
    """使用 DeepSeek R1 模型优化提示词"""
    try:
        # 构建请求体
        body = json.dumps({
            "prompt": f"请优化以下图片生成提示词，使其更加详细和专业：{prompt}",
            "max_tokens": 500,
            "temperature": 0.7
        })
        
        # 调用 Bedrock API
        response = bedrock.invoke_model(
            modelId="deepseek.deepseek-r1",
            body=body
        )
        
        # 解析响应
        response_body = json.loads(response.get('body').read())
        optimized_prompt = response_body.get('completion')
        return optimized_prompt
    except Exception as e:
        st.error(f"优化提示词时出错: {str(e)}")
        return None

def generate_image(prompt):
    """使用 Amazon Nova Canvas 模型生成图片"""
    try:
        # 翻译提示词为英文
        english_prompt = translate_to_english(prompt)
        if not english_prompt:
            return None
            
        # 构建请求体
        body = json.dumps({
            "text_prompts": [{"text": english_prompt}],
            "cfg_scale": 7,
            "steps": 50,
            "width": 1024,
            "height": 1024
        })
        
        # 调用 Bedrock API
        response = bedrock.invoke_model(
            modelId="amazon.nova-canvas-v1:0",
            body=body
        )
        
        # 解析响应
        response_body = json.loads(response.get('body').read())
        image_data = response_body.get('artifacts')[0].get('base64')
        
        # 将 base64 转换为图片
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        return image
    except Exception as e:
        st.error(f"生成图片时出错: {str(e)}")
        return None

def generate_video(prompt, duration=5, fps=24):
    """使用 Amazon Nova Reel 模型生成视频"""
    try:
        # 翻译提示词为英文
        english_prompt = translate_to_english(prompt)
        if not english_prompt:
            return None
            
        # 构建请求体
        body = json.dumps({
            "text_prompts": [{"text": english_prompt}],
            "duration": duration,
            "fps": fps,
            "width": 1024,
            "height": 1024
        })
        
        # 调用 Bedrock API
        response = bedrock.invoke_model(
            modelId="amazon.nova-reel-v1:1",
            body=body
        )
        
        # 解析响应
        response_body = json.loads(response.get('body').read())
        video_data = response_body.get('artifacts')[0].get('base64')
        
        # 将 base64 转换为视频文件
        video_bytes = base64.b64decode(video_data)
        video_path = "output_video.mp4"
        with open(video_path, "wb") as f:
            f.write(video_bytes)
            
        return video_path
    except Exception as e:
        st.error(f"生成视频时出错: {str(e)}")
        return None

def main():
    st.title("🎨 AI 创作助手")
    
    # 语言选择
    language = st.selectbox(
        "选择界面语言",
        ["中文", "English", "日本語", "한국어"]
    )
    
    # 根据选择的语言设置界面文本
    if language == "中文":
        prompt_label = "请输入创作描述"
        optimize_button = "优化提示词"
        generate_image_button = "生成图片"
        generate_video_button = "生成视频"
        loading_text = "正在生成，请稍候..."
        video_duration = "视频时长（秒）"
        video_fps = "视频帧率"
        translated_prompt = "英文提示词"
    elif language == "English":
        prompt_label = "Enter description"
        optimize_button = "Optimize prompt"
        generate_image_button = "Generate image"
        generate_video_button = "Generate video"
        loading_text = "Generating, please wait..."
        video_duration = "Video duration (seconds)"
        video_fps = "Video FPS"
        translated_prompt = "English prompt"
    elif language == "日本語":
        prompt_label = "説明を入力してください"
        optimize_button = "プロンプトを最適化"
        generate_image_button = "画像を生成"
        generate_video_button = "動画を生成"
        loading_text = "生成中です。お待ちください..."
        video_duration = "動画の長さ（秒）"
        video_fps = "動画のフレームレート"
        translated_prompt = "英語のプロンプト"
    else:
        prompt_label = "설명을 입력하세요"
        optimize_button = "프롬프트 최적화"
        generate_image_button = "이미지 생성"
        generate_video_button = "비디오 생성"
        loading_text = "생성 중입니다. 잠시만 기다려주세요..."
        video_duration = "비디오 길이(초)"
        video_fps = "비디오 프레임 레이트"
        translated_prompt = "영어 프롬프트"
    
    # 初始化会话状态
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'optimized_prompt' not in st.session_state:
        st.session_state.optimized_prompt = ""
    if 'english_prompt' not in st.session_state:
        st.session_state.english_prompt = ""
    
    # 创建两列布局
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("创作助手")
        user_input = st.text_area(prompt_label, height=100)
        
        if st.button(optimize_button):
            if user_input:
                with st.spinner(loading_text):
                    optimized_prompt = optimize_prompt(user_input)
                    if optimized_prompt:
                        st.session_state.optimized_prompt = optimized_prompt
                        # 翻译优化后的提示词
                        english_prompt = translate_to_english(optimized_prompt)
                        if english_prompt:
                            st.session_state.english_prompt = english_prompt
                            st.success("提示词已优化并翻译！")
            else:
                st.warning("请输入创作描述")
        
        if st.session_state.optimized_prompt:
            st.text_area("优化后的提示词", st.session_state.optimized_prompt, height=100)
            st.text_area(translated_prompt, st.session_state.english_prompt, height=100)
            
            # 图片生成
            if st.button(generate_image_button):
                with st.spinner(loading_text):
                    image = generate_image(st.session_state.optimized_prompt)
                    if image:
                        st.image(image, caption="生成的图片", use_column_width=True)
            
            # 视频生成选项
            st.subheader("视频生成选项")
            duration = st.slider(video_duration, 1, 10, 5)
            fps = st.slider(video_fps, 12, 60, 24)
            
            if st.button(generate_video_button):
                with st.spinner(loading_text):
                    video_path = generate_video(st.session_state.optimized_prompt, duration, fps)
                    if video_path:
                        st.video(video_path)
    
    with col2:
        st.subheader("对话历史")
        for message in st.session_state.chat_history:
            st.text(message)

if __name__ == "__main__":
    main() 
