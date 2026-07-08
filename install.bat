@echo off
chcp 65001 >nul
echo ====================================
echo  Helium - 安装依赖
echo ====================================
echo.

echo [1/2] 安装 Python 依赖...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo 安装失败，请确认 Python 和 pip 已正确安装
    pause
    exit /b 1
)
echo 完成
echo.

echo [2/2] 检查 FFmpeg...
if exist "%~dp0ffmpeg\bin\ffmpeg.exe" (
    echo FFmpeg 已就绪
) else (
    echo [警告] 未找到 ffmpeg\bin\ffmpeg.exe
    echo 请从 https://www.gyan.dev/ffmpeg/builds/ 下载 full build
    echo 解压后将 bin\ffmpeg.exe 和 bin\ffprobe.exe 放到 ffmpeg\bin\ 目录下
)
echo.

echo ====================================
echo  安装完成！运行 app.py 启动
echo ====================================
pause
