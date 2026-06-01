import { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { Send, Mic, RefreshCw, Lightbulb, X } from 'lucide-react';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  practiceMode?: string; // text | voice
  onRecordingStateChange?: (isRecording: boolean) => void;
}

export function ChatInput({ onSend, disabled, practiceMode = 'text', onRecordingStateChange }: ChatInputProps) {
  const [content, setContent] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const [recordingPhase, setRecordingPhase] = useState<'idle' | 'recording'>('idle'); // 空闲 | 录制中
  const [animationTime, setAnimationTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const timerRef = useRef<number | null>(null);
  const animationRef = useRef<number | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const handleSend = () => {
    if (content.trim() && !disabled) {
      onSend(content);
      setContent('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
  };

  // 获取最佳音频格式（优先级：AAC > MP3 > WAV > WebM）
  const getAudioFormat = (): string => {
    // 1. 优先AAC（高质量、小文件）
    if (MediaRecorder.isTypeSupported('audio/mp4;codecs=mp4a.40.2')) {
      return 'audio/mp4;codecs=mp4a.40.2'; // AAC格式（MP4容器）
    }
    if (MediaRecorder.isTypeSupported('audio/aac')) {
      return 'audio/aac';
    }
    
    // 2. 其次MP3（兼容性好）
    if (MediaRecorder.isTypeSupported('audio/mpeg')) {
      return 'audio/mpeg'; // MP3格式
    }
    if (MediaRecorder.isTypeSupported('audio/mp3')) {
      return 'audio/mp3';
    }
    
    // 3. 然后WAV（无损，文件较大）
    if (MediaRecorder.isTypeSupported('audio/wav')) {
      return 'audio/wav';
    }
    if (MediaRecorder.isTypeSupported('audio/wave')) {
      return 'audio/wave';
    }
    if (MediaRecorder.isTypeSupported('audio/x-wav')) {
      return 'audio/x-wav';
    }
    
    // 4. 最后回退到WebM
    return 'audio/webm';
  };

  // 开始录音（实际访问麦克风）
  const startRecording = async () => {
    if (disabled) return;
    
    try {
      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // 获取最佳音频格式
      const audioFormat = getAudioFormat();
      console.log('使用音频格式:', audioFormat);
      
      // 创建MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, { mimeType: audioFormat });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      // 收集音频数据
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      // 录音结束时处理
      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: audioFormat });
        setAudioBlob(blob);
        // 停止流
        stream.getTracks().forEach(track => track.stop());
      };
      
      // 开始录制
      mediaRecorder.start(100);
      
      // 更新状态
      setIsRecording(true);
      setRecordDuration(0);
      setRecordingPhase('recording');
      setAnimationTime(0);
      
      // 录音计时
      timerRef.current = window.setInterval(() => {
        setRecordDuration(prev => prev + 1);
      }, 1000);
      
      // 波纹动画计时器（60fps）
      animationRef.current = window.setInterval(() => {
        setAnimationTime(prev => prev + 1);
      }, 16);
      
    } catch (error) {
      console.error('麦克风访问失败:', error);
      alert('无法访问麦克风，请检查权限设置');
    }
  };

  // 停止MediaRecorder并清理
  const stopMediaRecorder = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (animationRef.current) {
      clearInterval(animationRef.current);
      animationRef.current = null;
    }
    setIsRecording(false);
  };

  // 重新录制
  const reRecord = () => {
    stopMediaRecorder();
    setContent('');
    setRecordDuration(0);
    setAudioBlob(null);
    setRecordingPhase('idle');
  };

  // 上传到阿里云OSS（Fun-ASR需要公网可访问的URL）
  const uploadToOSS = async (blob: Blob): Promise<string> => {
    try {
      // 将Blob转换为FormData上传到后端
      const formData = new FormData();
      formData.append('audio', blob, `recording_${Date.now()}.aac`);
      
      // 调用后端API上传到OSS
      const response = await fetch('/api/oss/upload', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      
      if (result.success) {
        console.log('上传OSS成功:', result.url);
        return result.url;  // 返回OSS文件URL
      } else {
        throw new Error(result.message || '上传OSS失败');
      }
    } catch (error) {
      console.error('上传OSS失败:', error);
      // 模拟返回（实际项目中移除）
      const mockUrl = `https://your-bucket.oss-cn-hangzhou.aliyuncs.com/voice/user_${Date.now()}.aac`;
      return mockUrl;
    }
  };

  // 调用Fun-ASR进行语音转写（需要OSS URL）
  const callASR = async (ossUrl: string): Promise<string> => {
    try {
      // Fun-ASR是异步API：提交任务 → 轮询结果
      // 1. 提交转写任务
      const submitResponse = await fetch('/api/asr/transcribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'fun-asr',           // 使用Fun-ASR模型
          audio_url: ossUrl,         // 传入OSS上的音频URL
          language: 'zh'              // 中文
        })
      });
      
      const submitResult = await submitResponse.json();
      
      if (!submitResult.success) {
        throw new Error(submitResult.message || '提交转写任务失败');
      }
      
      const taskId = submitResult.task_id;
      console.log('转写任务已提交，taskId:', taskId);
      
      // 2. 轮询查询转写结果
      let resultText = '';
      const maxRetries = 30;
      for (let i = 0; i < maxRetries; i++) {
        await new Promise(resolve => setTimeout(resolve, 1000));  // 每秒查询一次
        
        const queryResponse = await fetch(`/api/asr/query/${taskId}`);
        const queryResult = await queryResponse.json();
        
        if (queryResult.status === 'completed') {
          resultText = queryResult.text;
          console.log('ASR转写成功:', resultText);
          break;
        } else if (queryResult.status === 'failed') {
          throw new Error('ASR转写失败');
        }
      }
      
      if (!resultText) {
        throw new Error('ASR转写超时');
      }
      
      return resultText;
      
    } catch (error) {
      console.error('ASR调用失败:', error);
      // 模拟返回（实际项目中移除）
      await new Promise(resolve => setTimeout(resolve, 500));
      return `语音转写内容（时长${recordDuration}秒）：您好，我是客服小林，想咨询一下关于产品使用的问题。`;
    }
  };

  // 发送录音（Fun-ASR需要先上传OSS获取URL）
  const sendRecording = async () => {
    if (!audioBlob || disabled) return;
    
    stopMediaRecorder();
    
    try {
      // 步骤1：先上传到OSS获取URL
      console.log('上传音频到OSS...');
      const ossUrl = await uploadToOSS(audioBlob);
      console.log('OSS上传完成，URL:', ossUrl);
      
      // 步骤2：用OSS URL调用Fun-ASR转写
      console.log('开始ASR转写...');
      const asrResult = await callASR(ossUrl);
      console.log('ASR转写完成，结果:', asrResult);
      
      // 设置内容并发送
      setContent(asrResult);
      onSend(asrResult);
      
      // 重置状态
      setAudioBlob(null);
      setRecordDuration(0);
      setRecordingPhase('idle');
      
    } catch (error) {
      console.error('发送录音失败:', error);
      alert('发送失败，请重试');
    }
  };

  // 取消录音
  const cancelRecording = () => {
    stopMediaRecorder();
    setContent('');
    setRecordDuration(0);
    setAudioBlob(null);
    setRecordingPhase('idle');
  };

  // 清理定时器
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (animationRef.current) {
        clearInterval(animationRef.current);
      }
    };
  }, []);

  // 格式化时长显示
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // 判断是否正在录音
  const isRecordingActive = recordingPhase === 'recording';

  return (
    <>
      {/* 录音模式下的全屏面板 */}
      {isRecordingActive && (
        <div className="fixed bottom-0 left-0 right-0 bg-white rounded-t-3xl shadow-2xl p-4 z-50" style={{ paddingBottom: 'calc(4px + env(safe-area-inset-bottom))' }}>
          {/* 顶部：灵感按钮和关闭按钮 */}
          <div className="flex items-center justify-between mb-4">
            <button className="p-2 rounded-full bg-yellow-100 text-yellow-600 hover:bg-yellow-200 transition-colors">
              <Lightbulb className="w-5 h-5" />
            </button>
            <button 
              onClick={cancelRecording}
              className="p-2 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* 声波动画 */}
          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center justify-center gap-1 w-full">
              {Array.from({ length: 48 }).map((_, i) => (
                <div
                  key={i}
                  className="w-1 bg-green-500 rounded-full"
                  style={{
                    height: `${8 + Math.sin(animationTime * 0.05 + i * 0.3) * 16}px`,
                  }}
                />
              ))}
            </div>
            
            {/* 录制时长 */}
            <div className="px-4 py-2 bg-orange-500 text-white rounded-full">
              <span className="font-medium">{formatDuration(recordDuration)}</span>
            </div>
          </div>
          
          {/* 操作按钮：直接显示重录和发送 */}
          <div className="flex gap-3 mt-4">
            <button
              onClick={reRecord}
              className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-5 h-5" />
              <span>重录</span>
            </button>
            <button
              onClick={sendRecording}
              disabled={disabled || recordDuration === 0}
              className={`flex-1 py-3 bg-green-500 text-white rounded-xl font-medium hover:bg-green-600 transition-colors flex items-center justify-center gap-2 ${
                disabled || recordDuration === 0 ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <Send className="w-5 h-5" />
              <span>发送</span>
            </button>
          </div>
        </div>
      )}

      {/* 正常状态的输入区域 */}
      {!isRecordingActive && (
        <div className="px-4 py-3">
          {/* 文本模式 */}
          {practiceMode === 'text' && (
            <div className="flex items-end gap-3">
              <div className="flex-1 relative">
                <textarea
                  value={content}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  disabled={disabled}
                  placeholder="输入消息..."
                  className="w-full px-4 py-3 bg-gray-50 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  rows={1}
                  style={{
                    minHeight: '48px',
                    maxHeight: '120px',
                  }}
                />
              </div>
              <button
                onClick={handleSend}
                disabled={disabled || !content.trim()}
                className="p-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          )}

          {/* 语音模式 - 空闲状态 */}
          {practiceMode === 'voice' && (
            <button
              onClick={startRecording}
              disabled={disabled}
              className={`w-full flex items-center justify-center gap-3 py-4 rounded-xl transition-all font-medium ${
                disabled ? 'opacity-50 cursor-not-allowed' : 'bg-primary-500 text-white hover:bg-primary-600'
              }`}
            >
              <Mic className="w-5 h-5" />
              <span>点击说话</span>
            </button>
          )}
        </div>
      )}
    </>
  );
}
