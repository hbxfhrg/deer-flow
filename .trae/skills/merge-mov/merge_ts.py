#!/usr/bin/env python3
import os
import subprocess
import tempfile


def merge_ts_files():
    """
    合并当前目录中的TS视频文件为单个MP4文件，以目录名命名
    """
    # 获取当前目录名作为输出文件名
    current_dir = os.getcwd()
    dir_name = os.path.basename(current_dir)
    output_file = f"{dir_name}.mp4"
    
    # 查找所有TS文件并按名称排序
    ts_files = sorted([f for f in os.listdir('.') if f.endswith('.ts')])
    
    if not ts_files:
        print("错误: 当前目录中没有找到TS文件")
        return False
    
    print(f"找到 {len(ts_files)} 个TS文件:")
    for f in ts_files:
        print(f"  - {f}")
    
    # 创建临时播放列表文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for ts_file in ts_files:
            f.write(f"file '{os.path.abspath(ts_file)}'\n")
        playlist_file = f.name
    
    try:
        # 使用FFmpeg合并文件
        print(f"正在合并为 {output_file}...")
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', playlist_file,
            '-c', 'copy',
            output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"成功: 视频已合并为 {output_file}")
            return True
        else:
            print(f"错误: FFmpeg执行失败")
            print(f"错误输出: {result.stderr}")
            return False
    finally:
        # 清理临时文件
        if os.path.exists(playlist_file):
            os.unlink(playlist_file)


if __name__ == "__main__":
    merge_ts_files()
